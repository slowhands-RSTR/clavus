"""
Clavus TUI — Textual terminal UI for cue management + sync.

Usage:
    python3 -m clavus.tui                  # Local mode, auto-detect
    python3 -m clavus.tui --connect <url>  # Connect to remote clavus serve

Theme: CRUX dark — #0b1418 bg, #1a9e9e accent, #b8c8c8 fg
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import httpx

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen, ModalScreen
from textual.widgets import Header, Footer, Static, Button, Input, Label, Select, ListItem, ListView
from textual.reactive import reactive
from textual.message import Message
from textual.widget import Widget
from textual.css.query import NoMatches

from rich.text import Text
from rich.table import Table
from rich.panel import Panel
from rich.markup import escape as rich_escape

# ─── Data Models ──────────────────────────────────────────────────────


@dataclass
class SyncCue:
    """A cue from the sync API."""
    id: str
    position: str
    text: str
    author: str
    status: str = "pending"
    timestamp: float = 0.0
    track_name: str = ""
    snapshot_hash: str = ""
    replies: list[dict] = field(default_factory=list)

    @property
    def time_str(self) -> str:
        return time.strftime("%m/%d %H:%M", time.localtime(self.timestamp))


@dataclass
class SyncProjectInfo:
    name: str
    head: Optional[str] = None
    branch: str = "main"


@dataclass
class SyncSnapshot:
    hash: str
    full_hash: str
    timestamp: float
    message: str
    track_count: int = 0
    bpm: float = 120.0
    is_head: bool = False


@dataclass
class SyncBundle:
    project: Optional[SyncProjectInfo] = None
    cues: list[SyncCue] = field(default_factory=list)
    snapshots: list[SyncSnapshot] = field(default_factory=list)
    timestamp: float = 0.0


# ─── API Client ───────────────────────────────────────────────────────


class ClavusClient:
    """Async HTTP client for clavus serve."""

    def __init__(self, base_url: str = "http://localhost:7890"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=15.0)

    async def pull(self, project_name: str) -> SyncBundle:
        """Fetch full project state from server."""
        resp = await self.client.get(
            f"{self.base_url}/api/sync/pull",
            params={"name": project_name},
        )
        resp.raise_for_status()
        data = resp.json()

        proj_data = data.get("project") or {}
        project = SyncProjectInfo(
            name=proj_data.get("name", ""),
            head=proj_data.get("head"),
            branch=proj_data.get("branch", "main"),
        )

        cues = [
            SyncCue(**c) for c in data.get("cues", [])
        ]

        snapshots = [
            SyncSnapshot(**s) for s in data.get("snapshots", [])
        ]

        return SyncBundle(
            project=project,
            cues=cues,
            snapshots=snapshots,
            timestamp=data.get("timestamp", time.time()),
        )

    async def push(self, project_name: str, cues: list[SyncCue]) -> dict:
        """Send local cues to server."""
        payload = {
            "cues": [
                {
                    "id": c.id,
                    "position": c.position,
                    "text": c.text,
                    "author": c.author,
                    "status": c.status,
                    "timestamp": c.timestamp,
                    "track_name": c.track_name,
                    "snapshot_hash": c.snapshot_hash,
                    "replies": c.replies,
                }
                for c in cues
            ]
        }
        resp = await self.client.post(
            f"{self.base_url}/api/sync/push",
            params={"name": project_name},
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()

    async def list_projects(self) -> list[dict]:
        """List available projects on the server."""
        resp = await self.client.get(f"{self.base_url}/api/projects")
        resp.raise_for_status()
        data = resp.json()
        return data.get("projects", [])

    async def close(self):
        await self.client.aclose()


# ─── Widgets ──────────────────────────────────────────────────────────


class CueCard(Static):
    """A single cue card showing position, text, replies, and status."""

    def __init__(self, cue: SyncCue, **kwargs):
        super().__init__(**kwargs)
        self.cue = cue
        self.can_focus = True

    def on_mount(self):
        self._render()

    def _render(self):
        c = self.cue
        status_icon = {
            "pending": "●",
            "resolved": "✓",
            "skipped": "—",
            "deferred": "○",
        }.get(c.status, "●")

        status_color = {
            "pending": "yellow",
            "resolved": "green",
            "skipped": "dim",
            "deferred": "blue",
        }.get(c.status, "white")

        lines = []
        track_part = f" [{c.track_name}]" if c.track_name else ""
        lines.append(
            f"[{status_color}]{status_icon} @{rich_escape(c.position)}[/]"
            f" {rich_escape(c.text)}"
            f"{track_part}"
        )
        lines.append(
            f"  [{status_color}]by {rich_escape(c.author)} · {c.time_str}[/]"
        )

        for r in c.replies:
            r_author = r.get("author", "?")
            r_text = r.get("text", "")
            lines.append(
                f"  └─ [dim]{rich_escape(r_author)}:[/] {rich_escape(r_text)}"
            )

        lines.append(f"   [{status_color}]─── {c.status} ───[/]")
        self.update("\n".join(lines))

    def refresh_cue(self, cue: SyncCue) -> None:
        """Update the cue data and re-render."""
        self.cue = cue
        self._render()


class ProjectBar(Static):
    """Top bar showing project info and connection status."""

    project_name = reactive("")
    connection_status = reactive("⬤ connecting...")

    def on_mount(self):
        self._render()

    def watch_project_name(self, value: str):
        self._render()

    def watch_connection_status(self, value: str):
        self._render()

    def _render(self):
        name = self.project_name or "—"
        status = self.connection_status
        self.update(f" ⧩ clavus  [{self.accent}]{rich_escape(name)}[/]  {status}")

    @property
    def accent(self) -> str:
        return "cyan"  # #1a9e9e mapped to cyan in rich


class SyncFooter(Static):
    """Footer showing keyboard shortcuts."""

    def on_mount(self):
        self.update(
            " [bold cyan]P[/] Pull  [bold cyan]S[/] Sync  "
            "[bold cyan]C[/] Cue  [bold cyan]R[/] Resolve  "
            "[bold cyan]Q[/] Quit"
        )


class CueInputScreen(ModalScreen[Optional[SyncCue]]):
    """Modal screen for composing a new cue."""

    def compose(self) -> ComposeResult:
        yield Container(
            Label("New Cue", classes="modal-title"),
            Input(placeholder="@2:30 or 1:23 or 0.0.0", id="cue-pos-input"),
            Input(placeholder="Type your cue...", id="cue-text-input"),
            Input(placeholder="Track name (optional)", id="cue-track-input"),
            Horizontal(
                Button("Add", variant="primary", id="cue-add-btn"),
                Button("Cancel", id="cue-cancel-btn"),
            ),
            id="cue-input-container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cue-add-btn":
            text = self.query_one("#cue-text-input", Input).value.strip()
            position = self.query_one("#cue-pos-input", Input).value.strip() or "0.0.0"
            track = self.query_one("#cue-track-input", Input).value.strip()
            if text:
                cue = SyncCue(
                    id=f"local_{int(time.time() * 1000)}",
                    position=position,
                    text=text,
                    author=os.environ.get("USER", "anonymous"),
                    status="pending",
                    timestamp=time.time(),
                    track_name=track,
                )
                self.dismiss(cue)
            else:
                self.query_one("#cue-text-input", Input).focus()
        elif event.button.id == "cue-cancel-btn":
            self.dismiss(None)


# ─── Main TUI App ─────────────────────────────────────────────────────


CRUX_CSS = """
Screen {
    background: #0b1418;
}

ProjectBar {
    background: #0f1a20;
    color: #b8c8c8;
    border-bottom: solid #1a3040;
    padding: 1 2;
    height: 3;
    dock: top;
}

ScrollableContainer {
    background: #0b1418;
}

CueCard {
    background: #0f1a20;
    border: solid #1a3040;
    margin: 0 1 0 1;
    padding: 1;
}

CueCard:focus {
    border: solid #1a9e9e;
}

SyncFooter {
    background: #0f1a20;
    color: #6a8a8a;
    border-top: solid #1a3040;
    padding: 1;
    height: 3;
    dock: bottom;
    text-align: center;
}

Button {
    background: #15242b;
    color: #1a9e9e;
    border: solid #1a3040;
}

Button:hover {
    background: #1a2d36;
    border: solid #1a9e9e;
}

Button:focus {
    border: solid #1a9e9e;
}

Button.primary {
    background: #1a9e9e;
    color: #0b1418;
}

Label {
    color: #b8c8c8;
}

Input {
    background: #15242b;
    color: #b8c8c8;
    border: solid #1a3040;
}

Input:focus {
    border: solid #1a9e9e;
}

Select {
    background: #15242b;
    color: #b8c8c8;
    border: solid #1a3040;
}

Select:focus {
    border: solid #1a9e9e;
}

#cue-input-container {
    background: #0f1a20;
    border: solid #1a3040;
    padding: 2;
    width: 60%;
    height: auto;
    margin: 4 8;
}

#cue-input-container > Label.modal-title {
    text-style: bold;
    color: #1a9e9e;
    margin-bottom: 1;
}

#cue-input-container > Input {
    margin-bottom: 1;
}

#cue-input-container > Horizontal {
    align: center middle;
    margin-top: 1;
}

.project-info-box {
    background: #0f1a20;
    border: solid #1a3040;
    margin: 1 1 0 1;
    padding: 1;
    height: auto;
}

.project-info-box > Label {
    margin: 0 1;
}

#no-project-msg {
    color: #6a8a8a;
    text-align: center;
    margin: 4;
}

#status-bar {
    background: #0f1a20;
    color: #6a8a8a;
    border-bottom: solid #1a3040;
    height: 1;
    padding: 0 2;
    dock: top;
}
"""


class ClavusTUI(App):
    """Main Clavus TUI application."""

    CSS = CRUX_CSS

    BINDINGS = [
        Binding("p", "pull", "Pull"),
        Binding("s", "sync", "Sync"),
        Binding("c", "cue", "Cue"),
        Binding("r", "resolve", "Resolve"),
        Binding("q", "quit", "Quit"),
        Binding("j", "cursor_down", "Down"),
        Binding("k", "cursor_up", "Up"),
        Binding("enter", "select", "Select"),
    ]

    def __init__(self, connect_url: str = ""):
        super().__init__()
        self.connect_url = connect_url or os.environ.get(
            "CLAVUS_SERVER", "http://localhost:7890"
        )
        self.client = ClavusClient(self.connect_url)
        self.project_name: str = ""
        self._cues: list[SyncCue] = []
        self._pushed_ids: set[str] = set()
        self._poll_interval = 10
        self._sync_status = ""

    def compose(self) -> ComposeResult:
        yield ProjectBar(id="project-bar")
        yield ScrollableContainer(id="main-content")
        yield SyncFooter(id="footer")

    async def on_mount(self) -> None:
        """Initialize: try to detect project and connect."""
        bar = self.query_one(ProjectBar)
        bar.connection_status = "⬤ connecting..."

        try:
            projects = await self.client.list_projects()
            if projects:
                # Auto-select first project
                self.project_name = projects[0]["name"]
                await self.do_pull()
            else:
                content = self.query_one("#main-content", ScrollableContainer)
                content.mount(
                    Static(
                        "⚠ No projects found on server.\n"
                        "Run 'clavus init' on the server machine.\n\n"
                        f"Server: {self.connect_url}",
                        id="no-project-msg",
                    )
                )
                bar.connection_status = "⬤ no projects"
        except Exception as e:
            content = self.query_one("#main-content", ScrollableContainer)
            content.mount(
                Static(
                    f"⚠ Could not connect to {self.connect_url}\n"
                    f"Error: {e}\n\n"
                    "Make sure 'clavus serve' is running.\n"
                    "Set CLAVUS_SERVER env var or pass --connect.",
                    id="no-project-msg",
                )
            )
            bar.connection_status = f"⬤ disconnected"

        # Auto-poll
        self.set_interval(self._poll_interval, self._auto_poll)

    async def _auto_poll(self) -> None:
        """Periodically pull latest state (no push)."""
        if not self.project_name:
            return
        try:
            bundle = await self.client.pull(self.project_name)
            self._update_from_bundle(bundle, from_poll=True)
        except Exception:
            bar = self.query_one(ProjectBar)
            bar.connection_status = "⬤ disconnected"

    async def _update_from_bundle(
        self, bundle: SyncBundle, from_poll: bool = False
    ) -> None:
        """Update all widgets from a sync bundle."""
        bar = self.query_one(ProjectBar)
        content = self.query_one("#main-content", ScrollableContainer)

        # Update project info
        if bundle.project:
            self.project_name = bundle.project.name
            bar.project_name = bundle.project.name
            bar.connection_status = f"⬤ connected"

        # Update cues
        self._cues = bundle.cues
        self._rebuild_cue_list(content)

        # Update status
        footer = self.query_one(SyncFooter)
        cue_count = len(bundle.cues)
        pending = sum(1 for c in bundle.cues if c.status == "pending")
        snap_count = len(bundle.snapshots)
        poll_indicator = " [dim](auto-poll)[/]" if from_poll else ""
        footer.update(
            f" [bold cyan]P[/] Pull  [bold cyan]S[/] Sync  "
            f"[bold cyan]C[/] Cue  [bold cyan]R[/] Resolve  "
            f"[bold cyan]Q[/] Quit  "
            f"|  {cue_count} cues ({pending} pending)  |  "
            f"{snap_count} snapshots"
            f"{poll_indicator}"
        )

    def _rebuild_cue_list(self, content: ScrollableContainer) -> None:
        """Rebuild the cue card list in the content area."""
        # Store focused cue id before refresh
        focused_id = None
        focused = self.focused
        if focused and hasattr(focused, "cue"):
            focused_id = focused.cue.id

        content.remove_children()

        if not self._cues:
            content.mount(
                Static("No cues yet. Press C to add one.", id="no-project-msg")
            )
            return

        # Sort by timestamp (newest at top)
        sorted_cues = sorted(self._cues, key=lambda c: c.timestamp, reverse=True)

        for cue in sorted_cues:
            card = CueCard(cue)
            content.mount(card)

        # Re-focus the previously focused card if it still exists
        if focused_id:
            try:
                for child in content.children:
                    if hasattr(child, "cue") and child.cue.id == focused_id:
                        child.focus()
                        child.scroll_visible()
                        break
            except Exception:
                pass

    # ── Actions ───────────────────────────────────────────────────────

    async def action_pull(self) -> None:
        """Pull latest state from server."""
        if not self.project_name:
            return
        bar = self.query_one(ProjectBar)
        bar.connection_status = "⬤ pulling..."
        try:
            bundle = await self.client.pull(self.project_name)
            self._pushed_ids.update(c.id for c in bundle.cues)
            self._update_from_bundle(bundle)
        except Exception as e:
            bar.connection_status = f"⬤ error: {e}"

    async def action_sync(self) -> None:
        """Push local changes, then pull remote changes (full two-way)."""
        if not self.project_name:
            return
        bar = self.query_one(ProjectBar)
        bar.connection_status = "⬤ syncing..."

        try:
            # Push new local cues (ones we haven't seen from the server)
            new_cues = [
                c for c in self._cues if c.id not in self._pushed_ids
            ]
            if new_cues:
                result = await self.client.push(self.project_name, new_cues)
                self._pushed_ids.update(c.id for c in new_cues)

            # Pull latest
            bundle = await self.client.pull(self.project_name)
            self._pushed_ids.update(c.id for c in bundle.cues)
            self._update_from_bundle(bundle)
        except Exception as e:
            bar.connection_status = f"⬤ sync error: {e}"

    async def action_cue(self) -> None:
        """Open cue composer modal."""
        result = await self.push_screen(CueInputScreen())
        if result is None:
            return

        # Create local cue (not pushed yet)
        self._cues.append(result)
        content = self.query_one("#main-content", ScrollableContainer)
        self._rebuild_cue_list(content)

        # Update footer
        footer = self.query_one(SyncFooter)
        pending = sum(1 for c in self._cues if c.status == "pending")
        footer.update(
            f" [bold cyan]P[/] Pull  [bold cyan]S[/] Sync  "
            f"[bold cyan]C[/] Cue  [bold cyan]R[/] Resolve  "
            f"[bold cyan]Q[/] Quit  "
            f"|  {len(self._cues)} cues ({pending} pending)"
        )

    async def action_resolve(self) -> None:
        """Mark the currently focused cue as resolved."""
        focused = self.focused
        if not focused or not hasattr(focused, "cue"):
            return

        cue = focused.cue
        if cue.status != "pending":
            return

        cue.status = "resolved"
        focused.refresh_cue(cue)

        # This cue will be pushed on next sync

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()

    def action_cursor_down(self) -> None:
        """Move focus to the next cue card."""
        content = self.query_one("#main-content", ScrollableContainer)
        cards = [c for c in content.children if isinstance(c, CueCard)]
        if not cards:
            return

        focused = self.focused
        if focused in cards:
            idx = cards.index(focused)
            if idx < len(cards) - 1:
                cards[idx + 1].focus()
                cards[idx + 1].scroll_visible()
        else:
            cards[0].focus()
            cards[0].scroll_visible()

    def action_cursor_up(self) -> None:
        """Move focus to the previous cue card."""
        content = self.query_one("#main-content", ScrollableContainer)
        cards = [c for c in content.children if isinstance(c, CueCard)]
        if not cards:
            return

        focused = self.focused
        if focused in cards:
            idx = cards.index(focused)
            if idx > 0:
                cards[idx - 1].focus()
                cards[idx - 1].scroll_visible()
        else:
            cards[-1].focus()
            cards[-1].scroll_visible()

    def action_select(self) -> None:
        """Select/resolve the focused cue."""
        # Same as resolve for now
        self.run_action("resolve")

    async def on_shutdown(self) -> None:
        """Clean up on exit."""
        await self.client.close()


# ─── Entry Point ──────────────────────────────────────────────────────


def run_tui(connect_url: str = "") -> None:
    """Launch the Clavus TUI."""
    app = ClavusTUI(connect_url=connect_url)
    app.run()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Clavus TUI")
    parser.add_argument("--connect", "-c", default="",
                        help="Clavus server URL (default: http://localhost:7890)")
    args = parser.parse_args()
    run_tui(connect_url=args.connect)
