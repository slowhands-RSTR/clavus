"""
Clavus TUI — Textual-based terminal UI for cue management, sync, and snapshots.

Layout uses grid rows (no dock: top/bottom to avoid Textual v8 rendering bug).
┌─────────────────────────────────────────────┐
│  header: project + status + time             │  row 0
├─────────────────────────────────────────────┤
│  ruler: timeline with cue position markers   │  row 1
├──────────────────────┬──────────────────────┤
│  cues list           │  snapshot history     │  row 2 (split)
├─────────────────────────────────────────────┤
│  footer: keys + stats                       │  row 3
└─────────────────────────────────────────────┘
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

from textual import work, on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Static, Input, ListView, ListItem, Label
from textual.message import Message
from textual.css.query import NoMatches

# ─── Color Palette (CRUX dark) ──────────────────────────────────────────────

C = {
    "bg": "#0b1418",
    "surface": "#0f1a20",
    "surface2": "#162a34",
    "border": "#1a3040",
    "accent": "#1a9e9e",
    "fg": "#b8c8c8",
    "dim": "#6a8a8a",
    "muted": "#3a5a65",
    "yellow": "#d4a030",
    "green": "#44cc44",
    "red": "#ff4444",
}

# ─── Themes ──────────────────────────────────────────────────────────────────

THEMES = {
    "clavus": {
        "bg": "#0b1418", "surface": "#0f1a20", "surface2": "#162a34",
        "border": "#1a3040", "accent": "#1a9e9e", "fg": "#b8c8c8",
        "dim": "#6a8a8a", "muted": "#3a5a65", "hover": "#0f1a20",
    }
}

# ─── Data Models ────────────────────────────────────────────────────────────

@dataclass
class Cue:
    id: str = ""
    position: str = "1.1.1"
    text: str = ""
    author: str = ""
    status: str = "pending"   # pending, resolved, skipped
    timestamp: float = 0.0
    track_name: str = ""
    snapshot_hash: str = ""
    replies: list[dict] = field(default_factory=list)

@dataclass
class SnapshotInfo:
    hash: str = ""
    message: str = ""
    timestamp: float = 0.0
    track_count: int = 0
    bpm: float = 0.0

    @classmethod
    def from_dict(cls, d: dict) -> "SnapshotInfo":
        """Create from API response, ignoring extra keys."""
        return cls(
            hash=d.get("hash", d.get("full_hash", "")),
            message=d.get("message", ""),
            timestamp=d.get("timestamp", 0.0),
            track_count=d.get("track_count", 0),
            bpm=d.get("bpm", 0.0),
        )

@dataclass
class Bundle:
    project: object = None
    cues: list[Cue] = field(default_factory=list)
    snapshots: list[SnapshotInfo] = field(default_factory=list)


# ─── ClavusClient ───────────────────────────────────────────────────────────

class ClavusClient:
    """HTTP client for the Clavus sync server."""

    def __init__(self, base_url: str = "http://localhost:7890"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=10.0)

    async def ping(self) -> bool:
        try:
            r = await self.client.get(f"{self.base_url}/api/ping")
            return r.status_code == 200
        except Exception:
            return False

    async def get_project_info(self, name: str = "") -> Optional[dict]:
        try:
            params = {"name": name} if name else {}
            r = await self.client.get(f"{self.base_url}/api/project", params=params)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    async def pull(self, project: str) -> Bundle:
        bundle = Bundle(cues=[], snapshots=[])
        try:
            resp = await self.client.get(
                f"{self.base_url}/api/sync/pull",
                params={"name": project},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                bundle.project = data.get("project")
                bundle.cues = [Cue(**c) for c in data.get("cues", [])]
                bundle.snapshots = [SnapshotInfo.from_dict(s) for s in data.get("snapshots", [])]
        except Exception:
            pass
        return bundle

    async def push(self, project: str, cues: list[Cue]) -> bool:
        try:
            payload = [{"id": c.id, "position": c.position, "text": c.text,
                        "author": c.author, "status": c.status,
                        "timestamp": c.timestamp, "track_name": c.track_name,
                        "snapshot_hash": c.snapshot_hash, "replies": c.replies}
                       for c in cues]
            resp = await self.client.post(
                f"{self.base_url}/api/sync/push",
                params={"name": project},
                json=payload,
                timeout=15,
            )
            return resp.status_code == 200
        except Exception:
            return False

    async def close(self):
        await self.client.aclose()


# ─── App CSS ────────────────────────────────────────────────────────────────

CSS = f"""
ClavusApp {{
    background: {C['bg']};
}}

Screen {{
    background: {C['bg']};
}}

/* ── Main Layout ── */
#app-grid {{
    layout: grid;
    grid-size: 1 5;
    grid-rows: auto auto 1fr auto auto;
    height: 100%;
}}

/* ── Header Row ── */
#header-row {{
    height: 2;
    background: {C['surface']};
    color: {C['fg']};
    padding: 0 1;
    dock: none;
}}
#header-title {{
    color: {C['accent']};
    text-style: bold;
    padding: 0 1;
}}
#header-status {{
    color: {C['dim']};
    padding: 0 1;
}}

/* ── Ruler Row ── */
#ruler-row {{
    height: 1;
    background: {C['bg']};
    padding: 0 1;
}}
#ruler {{
    color: {C['muted']};
    overflow-x: auto;
}}

/* ── Content Row ── */
#content-row {{
    height: 1fr;
    layout: grid;
    grid-size: 2 1;
    grid-columns: 3fr 2fr;
}}

#cues-panel {{
    background: {C['bg']};
    border-right: solid {C['border']};
    height: 100%;
}}
#cues-panel > Static.label {{
    color: {C['dim']};
    text-style: bold;
    padding: 0 1;
    height: 1;
}}
#cues-list {{
    height: 1fr;
}}
#cues-list ListView {{
    height: 100%;
    border: none;
    background: transparent;
}}
#cues-list ListItem {{
    background: transparent;
    padding: 0 1;
    height: 3;
}}
#cues-list ListItem:hover {{
    background: {C['surface']};
}}
ListView:focus .list-item--focused {{
    background: {C['surface2']};
}}

#history-panel {{
    background: {C['bg']};
    height: 100%;
}}
#history-panel > Static.label {{
    color: {C['dim']};
    text-style: bold;
    padding: 0 1;
    height: 1;
}}
#history-list {{
    height: 1fr;
}}

/* ── Footer Row ── */
#footer-row {{
    height: 1;
    background: {C['surface']};
    color: {C['dim']};
    padding: 0 1;
    dock: none;
}}
#footer-keys {{
    color: {C['accent']};
}}
#footer-stats {{
    color: {C['muted']};
    text-align: right;
}}

/* ── Scrollbars (CRUX dark) ── */
Scrollbar {{
    scrollbar-color: rgba(26,158,158,0.5) {C['border']};
    scrollbar-color-hover: rgba(26,158,158,0.8) {C['surface2']};
    scrollbar-color-active: rgba(26,158,158,0.9) {C['surface2']};
    scrollbar-size-vertical: 2;
    scrollbar-size-horizontal: 2;
}}
Scrollbar > .scrollbar--bar {{
    background: {C['border']};
}}
Scrollbar > .scrollbar--grabber {{
    background: rgba(26,158,158,0.4);
}}
Scrollbar > .scrollbar--grabber:hover {{
    background: rgba(26,158,158,0.8);
}}
Scrollbar.vertical > .scrollbar--grabber {{
    min-height: 3;
}}

/* ── Inline Reply Bar ── */
#reply-bar {{
    height: 3;
    background: {C['surface2']};
    border-top: solid {C['accent']};
    padding: 0 1;
    visibility: hidden;
}}
#reply-bar.visible {{
    visibility: visible;
}}
#reply-bar Input {{
    width: 100%;
    background: {C['bg']};
    border: solid {C['accent']};
    color: {C['fg']};
    padding: 0 1;
}}
"""


# ─── Messages ───────────────────────────────────────────────────────────────

class StatusMessage(Message):
    def __init__(self, text: str):
        self.text = text
        super().__init__()


# ─── App ────────────────────────────────────────────────────────────────────

class ClavusApp(App):
    CSS = CSS
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "reply_cue", "Reply"),
        Binding("e", "edit_cue", "Edit"),
        Binding("c", "new_cue", "New cue"),
        Binding("s", "skip_cue", "Skip"),
        Binding("R", "resolve_cue", "Resolve"),
        Binding("p", "pull", "Pull"),
        Binding("P", "push", "Push"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("tab", "focus_next", "Next pane", show=False),
        Binding("shift+tab", "focus_previous", "Prev pane", show=False),
        Binding("escape", "hide_reply_bar", "Close", show=False),
    ]

    def __init__(self, connect_url: str = ""):
        super().__init__()
        self._connect_url = connect_url or os.environ.get("CLAVUS_SERVER", "http://localhost:7890")
        self.client = ClavusClient(self._connect_url)
        self.project_name: str = ""
        self.connection_status: str = "connecting..."
        self.cues: list[Cue] = []
        self.snapshots: list[SnapshotInfo] = []
        self.selected_cue_idx: int = 0
        self.pushed_ids: set[str] = set()
        self._error_count: int = 0
        self._input_mode: str = ""  # "reply", "new_cue", "edit", "command"
        self._reply_cue_id: str = ""

    def get_css_variables(self) -> dict[str, str]:
        base = super().get_css_variables()
        base.update(THEMES["clavus"])
        return base

    def compose(self) -> ComposeResult:
        with Container(id="app-grid"):
            # Header
            yield Container(
                Static("~▲~ clavus", id="header-title"),
                Static("connecting...", id="header-status"),
                id="header-row",
            )
            # Ruler
            yield Container(
                Static("", id="ruler"),
                id="ruler-row",
            )
            # Content
            yield Container(
                Container(
                    Static(" Cues", classes="label"),
                    Container(id="cues-list",),
                    id="cues-panel",
                ),
                Container(
                    Static(" History", classes="label"),
                    Container(id="history-list",),
                    id="history-panel",
                ),
                id="content-row",
            )
            # Footer
            yield Container(
                Static("", id="footer-keys"),
                Static("", id="footer-stats"),
                id="footer-row",
            )
            # Reply bar (inline, hidden by default)
            yield Container(
                Input(id="reply-input", placeholder="type your reply..."),
                id="reply-bar",
            )

    def on_mount(self) -> None:
        self._update_header()
        self._update_footer()
        self._connect()

    # ─── Connection ─────────────────────────────────────────────────────

    @work(exclusive=True)
    async def _connect(self) -> None:
        """Connect to server and load initial data."""
        ok = await self.client.ping()
        if not ok:
            self.connection_status = "offline"
            self._update_header()
            self._update_footer()
            self.post_message(StatusMessage("server offline — start clavus serve"))
            return

        info = await self.client.get_project_info()
        if info:
            self.project_name = info.get("name", "unknown")
            self.connection_status = "connected"
        else:
            self.project_name = ""
            self.connection_status = "no project"

        self._update_header()
        self._update_footer()
        await self._do_pull()

    # ─── Pull / Push ────────────────────────────────────────────────────

    async def _do_pull(self) -> None:
        if not self.project_name:
            return
        bundle = await self.client.pull(self.project_name)
        if bundle.cues:
            self.cues = bundle.cues
        self.snapshots = bundle.snapshots
        self._update_header()
        self._update_footer()
        self.render_cues()
        self.render_history()

    async def _do_push(self) -> None:
        if not self.project_name:
            return
        new = [c for c in self.cues if c.id not in self.pushed_ids]
        if new:
            ok = await self.client.push(self.project_name, new)
            if ok:
                self.pushed_ids.update(c.id for c in new)
                self.post_message(StatusMessage(f"⬆ pushed {len(new)} cue(s)"))
            else:
                self.post_message(StatusMessage("❌ push failed"))

    @work(exclusive=True)
    async def action_pull(self) -> None:
        self.post_message(StatusMessage("pulling..."))
        await self._do_pull()
        self.post_message(StatusMessage("pulled"))

    @work(exclusive=True)
    async def action_push(self) -> None:
        self.post_message(StatusMessage("pushing..."))
        await self._do_push()
        self.post_message(StatusMessage("done"))

    # ─── Cue Operations ─────────────────────────────────────────────────

    def action_new_cue(self) -> None:
        self._show_input_bar("new_cue", "")

    def action_edit_cue(self) -> None:
        cue = self._get_selected_cue()
        if not cue:
            self.post_message(StatusMessage("select a cue with j/k first"))
            return
        self._reply_cue_id = cue.id
        self._show_input_bar("edit", cue.text)

    def _show_input_bar(self, mode: str, prefill: str = "") -> None:
        """Show the inline input bar in a given mode."""
        self._input_mode = mode
        bar = self.query_one("#reply-bar", Container)
        inp = bar.query_one("#reply-input", Input)
        inp.value = prefill
        bar.add_class("visible")
        inp.focus()

    def action_reply_cue(self) -> None:
        cue = self._get_selected_cue()
        if not cue:
            self.post_message(StatusMessage("select a cue with j/k first"))
            return
        self._reply_cue_id = cue.id
        self._show_input_bar("reply")
        self.post_message(StatusMessage(f"💬 reply to @{cue.position}: type and press Enter"))

    def action_resolve_cue(self) -> None:
        cue = self._get_selected_cue()
        if cue:
            cue.status = "resolved"
            self.render_cues()
            self.post_message(StatusMessage(f"resolved: {cue.text[:40]}"))

    def action_skip_cue(self) -> None:
        cue = self._get_selected_cue()
        if cue:
            cue.status = "skipped"
            self.render_cues()
            self.post_message(StatusMessage(f"skipped: {cue.text[:40]}"))

    def _get_selected_cue(self) -> Optional[Cue]:
        idx = self.selected_cue_idx
        if 0 <= idx < len(self.cues):
            return self.cues[idx]
        return None

    # ─── Callbacks ──────────────────────────────────────────────────────

    def _handle_new_cue(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        pos = "1.1.1"
        if "@" in text:
            parts = text.split("@", 1)
            text = parts[0].strip()
            pos = parts[1].strip()
        cue = Cue(
            id=str(int(time.time() * 1000)),
            position=pos,
            text=text,
            author="you",
            status="pending",
            timestamp=time.time(),
        )
        self.cues.append(cue)
        self.selected_cue_idx = len(self.cues) - 1
        self.render_cues()
        self.post_message(StatusMessage(f"💬 cue added @ {pos}"))

    def _handle_edit_cue(self, cue_id: str, text: str) -> None:
        text = text.strip()
        if not text:
            return
        for c in self.cues:
            if c.id == cue_id or c.id.startswith(cue_id):
                c.text = text
                self.render_cues()
                self.post_message(StatusMessage(f"✏️ cue updated"))
                return
        self.post_message(StatusMessage(f"❌ cue not found"))

    def _handle_reply(self, cue_id: str, text: str) -> None:
        text = text.strip()
        if not text:
            return
        for c in self.cues:
            if c.id == cue_id or c.id.startswith(cue_id):
                c.replies.append({
                    "author": "you",
                    "text": text,
                    "timestamp": time.time(),
                })
                self.render_cues()
                self.post_message(StatusMessage(f"💬 reply added"))
                return
        self.post_message(StatusMessage(f"❌ cue not found"))

    # ─── Command : (general command bar) ────────────────────────────────

    def action_open_command(self) -> None:
        self._show_input_bar("command", "")

    def _handle_command(self, cmd: str) -> None:
        cmd = cmd.strip()
        if not cmd:
            return

        if cmd.startswith("cue "):
            self._handle_new_cue(cmd[4:])
        elif cmd.startswith("edit "):
            parts = cmd.split(" ", 2)
            if len(parts) >= 3:
                self._handle_edit_cue(parts[1], parts[2])
        elif cmd.startswith("reply "):
            text = cmd[6:].strip()
            cue = self._get_selected_cue()
            if cue:
                self._handle_reply(cue.id, text)
            else:
                self.post_message(StatusMessage("select a cue with j/k first"))
        elif cmd in ("resolve", "R"):
            self.action_resolve_cue()
        elif cmd == "skip":
            self.action_skip_cue()
        elif cmd == "pull":
            self.action_pull()
        elif cmd == "push":
            self.action_push()
        elif cmd in ("help", "h"):
            self._show_help()

    def action_hide_reply_bar(self) -> None:
        """Hide the inline reply bar if visible."""
        try:
            bar = self.query_one("#reply-bar", Container)
            if "visible" in bar.classes:
                bar.remove_class("visible")
                self._input_mode = ""
                self._focus_cues()
        except NoMatches:
            pass

    @on(Input.Submitted, "#reply-input")
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter in the inline input bar."""
        text = event.value.strip()
        if not text:
            self.action_hide_reply_bar()
            return
        if self._input_mode == "reply":
            self._handle_reply(self._reply_cue_id, text)
        elif self._input_mode == "new_cue":
            self._handle_new_cue(text)
        elif self._input_mode == "edit":
            self._handle_edit_cue(self._reply_cue_id, text)
        elif self._input_mode == "command":
            self._handle_command(text)
        self.action_hide_reply_bar()

    def action_close_command(self) -> None:
        pass  # no-op

    # ─── Rendering ──────────────────────────────────────────────────────

    def _update_header(self) -> None:
        try:
            title = self.query_one("#header-title", Static)
            status = self.query_one("#header-status", Static)

            conn = self.connection_status
            conn_dot = "⬤" if conn == "connected" else "◌"
            title_str = f"[bold {C['accent']}]~▲~ clavus[/]"
            if self.project_name:
                title_str += f"  [white]{self.project_name}[/]"

            status_str = f"[{C['dim']}]{conn_dot} {conn}[/]  [dim]{len(self.cues)} cues[/]"
            snap_count = len(self.snapshots)
            if snap_count:
                status_str += f"  [dim]{snap_count} snapshot{'s' if snap_count != 1 else ''}[/]"

            title.update(title_str)
            status.update(status_str)
        except NoMatches:
            pass

    def _update_footer(self) -> None:
        try:
            keys = self.query_one("#footer-keys", Static)
            stats = self.query_one("#footer-stats", Static)

            key_str = (
                f"[{C['accent']}]r[/] reply  "
                f"[{C['accent']}]R[/] resolve  "
                f"[{C['accent']}]e[/] edit  "
                f"[{C['accent']}]c[/] cue  "
                f"[{C['accent']}]s[/] skip  "
                f"[{C['accent']}]p[/] pull  "
                f"[{C['accent']}]P[/] push  "
                f"[{C['accent']}]q[/] quit"
            )
            stats_str = f"[{C['muted']}]j/k navigate | {len(self.cues)} cues[/]"

            keys.update(key_str)
            stats.update(stats_str)
        except NoMatches:
            pass

    def render_cues(self) -> None:
        try:
            container = self.query_one("#cues-list", Container)
            lv = container.query(ListView).first() if container.query(ListView) else None
            if not lv:
                lv = ListView(id="cues-listview")
                container.mount(lv)

            lv.clear()
            for i, cue in enumerate(self.cues):
                color = C["yellow"] if cue.status == "pending" else (
                    C["green"] if cue.status == "resolved" else C["muted"])
                status_char = "●" if cue.status == "pending" else (
                    "✓" if cue.status == "resolved" else "–")
                reply_count = f" [{C['dim']}]{len(cue.replies)}r[/]" if cue.replies else ""
                text = f"[{color}]{status_char}[/] [dim]@{cue.position}[/] "
                text += f"[{C['fg']}]{cue.text[:55]}[/]"
                text += f" [{C['muted']}]{cue.id[:8]}[/]{reply_count}"
                if cue.author and cue.author != "you":
                    text += f" [{C['dim']}]- {cue.author}[/]"
                lv.append(ListItem(Label(text)))
        except NoMatches:
            pass

    def render_history(self) -> None:
        try:
            container = self.query_one("#history-list", Container)
            lv = container.query(ListView).first() if container.query(ListView) else None
            if not lv:
                lv = ListView(id="history-listview")
                container.mount(lv)

            lv.clear()
            if not self.snapshots:
                lv.append(ListItem(Label(f"[{C['dim']}]  no snapshots yet[/]")))
                lv.append(ListItem(Label(f"  [{C['muted']}]clavus snapshot 'your message'[/]")))
            else:
                for snap in self.snapshots[:20]:
                    time_str = time.strftime("%m/%d %H:%M", time.localtime(snap.timestamp)) if snap.timestamp else ""
                    text = f"[{C['accent']}]{snap.hash[:8]}[/] [{C['dim']}]{time_str}[/]"
                    if snap.message:
                        text += f"  [{C['fg']}]{snap.message[:50]}[/]"
                    if snap.track_count:
                        text += f"  [{C['muted']}]{snap.track_count}trk[/]"
                    lv.append(ListItem(Label(text)))
        except NoMatches:
            pass

    def _focus_cues(self) -> None:
        try:
            container = self.query_one("#cues-list", Container)
            lv = container.query(ListView).first()
            if lv:
                lv.focus()
        except NoMatches:
            pass

    # ─── Navigation ─────────────────────────────────────────────────────

    def action_focus_next(self) -> None:
        try:
            containers = [
                self.query_one("#cues-list", Container),
            ]
            for c in containers:
                lv = c.query(ListView).first()
                if lv and lv.has_focus:
                    # Move to history
                    h = self.query_one("#history-list", Container)
                    hl = h.query(ListView).first()
                    if hl:
                        hl.focus()
                    return
            # Focus cues
            self._focus_cues()
        except NoMatches:
            pass

    def action_cursor_down(self) -> None:
        lv = self.focused
        if lv and hasattr(lv, "action_cursor_down"):
            lv.action_cursor_down()
            # Track selection
            if hasattr(lv, "index") and lv.index is not None:
                if lv.id and "history" not in lv.id:
                    self.selected_cue_idx = lv.index

    def action_cursor_up(self) -> None:
        lv = self.focused
        if lv and hasattr(lv, "action_cursor_up"):
            lv.action_cursor_up()
            if hasattr(lv, "index") and lv.index is not None:
                if lv.id and "history" not in lv.id:
                    self.selected_cue_idx = lv.index

    def action_focus_search(self) -> None:
        self.action_open_command()  # opens : command screen

    # ─── Messages ───────────────────────────────────────────────────────

    def on_status_msg(self, msg: StatusMessage) -> None:
        # Flash status in footer briefly
        try:
            self.query_one("#footer-stats", Static).update(
                f"[{C['dim']}]{msg.text}[/]"
            )
        except NoMatches:
            pass

    def _show_help(self) -> None:
        self.post_message(StatusMessage(
            "c=cue  r=reply  R=resolve  e=edit  s=skip  p=pull  P=push  j/k=navigate  q=quit"
        ))


# ─── Entry Point ────────────────────────────────────────────────────────────

def run_tui(connect_url: str = "") -> None:
    app = ClavusApp(connect_url=connect_url)
    app.run()


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--connect", "-c", default="")
    a = p.parse_args()
    run_tui(a.connect)
