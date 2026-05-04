"""Clavus — visual diff renderer for Ableton project snapshots.

Transforms ProjectDiff into ASCII/Unicode timeline visualizations
that show how the arrangement changed between snapshots.

Two output modes:
  1. Terminal (ANSI colors, Unicode box drawing) — for CLI and TUI
  2. HTML/SVG — for the web companion

The parser doesn't extract individual clip positions yet, so the
visual diff focuses on what we CAN extract:
  - Track structure (added/removed/reordered tracks)
  - BPM changes (timeline scaling)
  - Marker positions (arrangement landmarks)
  - Device chain changes
  - Track state changes (mute/freeze)

This gives a "forest level" view of arrangement changes.
Clip-level detail can be added later when the parser extracts clip data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from clavus.store import ProjectDiff, TrackDiff


# ─── Color constants (CRUX theme — same as TUI) ────────────────────────

C = {
    "bg": "#0b1418",
    "surface": "#0f1a20",
    "border": "#1a3040",
    "accent": "#1a9e9e",
    "fg": "#b8c8c8",
    "dim": "#6a8a8a",
    "muted": "#3a5a65",
    "yellow": "#d4a030",
    "green": "#44cc44",
    "red": "#ff4444",
    "orange": "#ff8844",
    "blue": "#4488ff",
}

# ANSI terminal color codes
ANSI = {
    "accent": "\033[36m",
    "green": "\033[32m",
    "red": "\033[31m",
    "yellow": "\033[33m",
    "dim": "\033[2m\033[37m",
    "bold": "\033[1m",
    "reset": "\033[0m",
    "orange": "\033[38;5;208m",
    "blue": "\033[34m",
}

# ─── Timeline Layout ──────────────────────────────────────────────────

TIMELINE_WIDTH = 60  # Characters wide for each timeline
TRACK_LABEL_WIDTH = 20  # Characters for track name column


def _format_bpm(bpm: float) -> str:
    return f"{bpm:.0f}"


def _track_symbol(td: TrackDiff) -> str:
    """Return a status symbol for a track diff."""
    symbols = {
        "added": ("+", ANSI["green"]),
        "removed": ("-", ANSI["red"]),
        "modified": ("~", ANSI["yellow"]),
        "unchanged": (" ", ANSI["reset"]),
    }
    sym, color = symbols.get(td.status, (" ", ANSI["reset"]))
    return f"{color}{sym}{ANSI['reset']}"


def _marker_bar(markers: list[str], highlight: set[str] | None = None) -> str:
    """Render a marker/landmark bar for the timeline."""
    if not markers:
        return ""
    # Place markers proportionally
    highlight = highlight or set()
    parts = []
    spacing = max(1, TIMELINE_WIDTH // (len(markers) + 1))
    for i, m in enumerate(markers):
        pos = (i + 1) * spacing
        if pos >= TIMELINE_WIDTH - 2:
            pos = TIMELINE_WIDTH - 4
        if m in highlight:
            parts.append(f"{ANSI['accent']}▼{ANSI['reset']}")
        else:
            parts.append(f"{ANSI['dim']}◆{ANSI['reset']}")
        # We'll just return a flat string — actual positioning needs more work
        # For now, show markers inline
    return "  " + " ".join(
        f"{ANSI['accent'] if m in highlight else ANSI['dim']}[{m[:12]}]{ANSI['reset']}"
        for m in markers[:8]
    )


# ─── ASCII Timeline Renderer ──────────────────────────────────────────


def render_timeline_bar(
    track_name: str,
    status: str,
    width: int = TIMELINE_WIDTH,
) -> str:
    """Render a single track's arrangement as a filled bar.

    Different statuses get different fill patterns:
      - added:    solid accent color
      - removed:  dim with X pattern
      - modified: striped yellow
      - unchanged: dim solid
    """
    bar = "█" * width

    if status == "added":
        return f"{ANSI['green']}{bar}{ANSI['reset']}"
    elif status == "removed":
        pattern = ""
        for i in range(width):
            pattern += "█" if i % 3 == 0 else " "
        return f"{ANSI['red']}{pattern}{ANSI['reset']}"
    elif status == "modified":
        # Striped pattern
        pattern = ""
        for i in range(width):
            pattern += "█" if i % 4 < 2 else "▓"
        return f"{ANSI['yellow']}{pattern}{ANSI['reset']}"
    else:
        return f"{ANSI['dim']}{bar}{ANSI['reset']}"


def render_side_by_side(
    before: list[TrackDiff],
    after: list[TrackDiff],
    before_markers: list[str],
    after_markers: list[str],
    before_bpm: Optional[float] = None,
    after_bpm: Optional[float] = None,
) -> str:
    """Render a side-by-side visual diff of before and after.

    Layout:
    ```
    ┌─ Before ──────────────┐  ┌─ After ───────────────┐
    │ Kick ████████████████  │  │ Kick ████████████████  │  ◄ unchanged
    │ Clap ████████████████  │  │ Clap ████████████████  │
    │ Hat  ████████████████  │  │ Hat  ████████████████  │
    │                   │  │ BASS ████████████████  │  ◄ ▲ added
    │ Vox  ████████████████  │  │ Vox  ████████████████  │
    │ Markers: [Int][Verse]  │  │ Markers: [Int][Ver][Br]│
    └────────────────────────┘  └────────────────────────┘
    ```

    Args:
        before: Track diffs for the "before" snapshot
        after: Track diffs for the "after" snapshot
        before_markers: Marker names for before
        after_markers: Marker names for after
        before_bpm: BPM of before snapshot
        after_bpm: BPM of after snapshot

    Returns:
        ANSI-colored string for terminal display
    """
    lines = []
    time_width = TIMELINE_WIDTH

    # ── Build ordered track lists ──
    # Start with all track names from both sides
    before_tracks: dict[str, TrackDiff] = {}
    after_tracks: dict[str, TrackDiff] = {}
    all_names: list[str] = []

    for td in before:
        before_tracks[td.name] = td
        if td.name not in all_names:
            all_names.append(td.name)
    for td in after:
        after_tracks[td.name] = td
        if td.name not in all_names:
            all_names.append(td.name)

    # ── Header ──
    bpm_before = f" {_format_bpm(before_bpm)}bpm" if before_bpm else ""
    bpm_after = f" {_format_bpm(after_bpm)}bpm" if after_bpm else ""
    lines.append("")
    header_before = f"Before{bpm_before}"
    header_after = f"After{bpm_after}"
    half = time_width // 2
    lines.append(
        f"  {ANSI['bold']}{header_before}{ANSI['reset']}"
        f"{' ' * (TRACK_LABEL_WIDTH + time_width - len(header_before) - len(header_after) - 2)}"
        f"{ANSI['bold']}{header_after}{ANSI['reset']}"
    )

    divider = "  " + "─" * (TRACK_LABEL_WIDTH + time_width) + "  " + "─" * time_width
    lines.append(divider)

    # ── Track rows ──
    for name in all_names:
        bt = before_tracks.get(name)
        at = after_tracks.get(name)

        # Determine row annotation
        annotation = ""
        if bt and not at:
            annotation = f" {ANSI['red']}◄ removed{ANSI['reset']}"
        elif at and not bt:
            annotation = f" {ANSI['green']}◄ ▲ added{ANSI['reset']}"
        elif bt and at and bt.status != "unchanged":
            detail_parts = []
            if at.devices_added:
                detail_parts.append(f"+{','.join(d[:8] for d in at.devices_added)}")
            if at.devices_removed:
                detail_parts.append(f"-{','.join(d[:8] for d in at.devices_removed)}")
            if at.frozen_changed is not None:
                detail_parts.append("frozen" if at.frozen_changed else "unfrozen")
            if at.mute_changed is not None:
                detail_parts.append("muted" if at.mute_changed else "unmuted")
            if detail_parts:
                annotation = f" {ANSI['yellow']}◄ {', '.join(detail_parts)}{ANSI['reset']}"

        # Left side (before)
        left_label = f"{name:<{TRACK_LABEL_WIDTH}}"
        if bt:
            left_bar = render_timeline_bar(name, bt.status, time_width)
        else:
            left_bar = " " * time_width

        # Right side (after)
        if at:
            right_bar = render_timeline_bar(name, at.status, time_width)
        else:
            right_bar = " " * time_width

        lines.append(f"  {left_label}{left_bar}  {right_bar}{annotation}")

    # ── Marker rows ──
    marker_tags_before = " ".join(
        f"{ANSI['dim']}[{m[:10]}]{ANSI['reset']}"
        for m in before_markers[:5]
    )
    marker_tags_after = " ".join(
        f"{ANSI['accent'] if m in after_markers and m not in before_markers else ANSI['dim']}[{m[:10]}]{ANSI['reset']}"
        for m in after_markers[:5]
    )

    # Highlight new markers
    new_markers = set(after_markers) - set(before_markers)
    marker_tags_after = " ".join(
        f"{ANSI['accent'] if m in new_markers else ANSI['dim']}[{m[:10]}]{ANSI['reset']}"
        for m in after_markers[:5]
    )

    lines.append(
        f"  {'Markers':<{TRACK_LABEL_WIDTH}}{marker_tags_before}"
        f"  {marker_tags_after}"
    )

    # ── BPM change indicator ──
    if before_bpm and after_bpm and before_bpm != after_bpm:
        bpm_diff = after_bpm - before_bpm
        direction = "▲ faster" if bpm_diff > 0 else "▼ slower"
        lines.append("")
        lines.append(
            f"  {ANSI['yellow']}● Tempo: {before_bpm:.0f} → {after_bpm:.0f} bpm "
            f"({direction} by {abs(bpm_diff):.0f}){ANSI['reset']}"
        )

    # ── Summary footer ──
    added_count = len([t for t in all_names if after_tracks.get(t) and not before_tracks.get(t)])
    removed_count = len([t for t in all_names if before_tracks.get(t) and not after_tracks.get(t)])
    modified_count = len([t for t in all_names
                         if before_tracks.get(t) and after_tracks.get(t)
                         and before_tracks[t].status != "unchanged"])

    summary_parts = []
    if added_count:
        summary_parts.append(f"{ANSI['green']}+{added_count} tracks{ANSI['reset']}")
    if removed_count:
        summary_parts.append(f"{ANSI['red']}-{removed_count} tracks{ANSI['reset']}")
    if modified_count:
        summary_parts.append(f"{ANSI['yellow']}~{modified_count} modified{ANSI['reset']}")
    if new_markers:
        summary_parts.append(f"{ANSI['accent']}+{len(new_markers)} markers{ANSI['reset']}")

    if summary_parts:
        lines.append("")
        lines.append(f"  {'':<{TRACK_LABEL_WIDTH}}{' | '.join(summary_parts)}")

    lines.append("")
    return "\n".join(lines)


def render_diff_cli(diff: ProjectDiff) -> str:
    """Render a ProjectDiff as a visual timeline for the terminal/CLI.

    This is called by `clavus diff --visual`.

    Args:
        diff: The structured diff between two snapshots

    Returns:
        ANSI-colored visual diff string for terminal output
    """
    # Extract before/after track state from the diff
    # We don't have full Project objects here, just the diff summary
    # The CLI calls this after loading both snapshots
    return render_side_by_side(
        before=diff.tracks,
        after=diff.tracks,  # Same list — the TrackDiff has status for each
        before_markers=diff.markers_removed,
        after_markers=diff.markers_added,
    )


# ─── Web HTML Renderer ────────────────────────────────────────────────


def render_diff_html(diff: ProjectDiff) -> str:
    """Render a ProjectDiff as HTML for the web companion.

    Returns an HTML string with inline styles matching the CRUX theme.
    """
    added = [t for t in diff.tracks if t.status == "added"]
    removed = [t for t in diff.tracks if t.status == "removed"]
    modified = [t for t in diff.tracks if t.status == "modified"]

    rows = []
    for td in diff.tracks:
        color = "#6a8a8a"
        symbol = " "
        if td.status == "added":
            color = "#44cc44"
            symbol = "+"
        elif td.status == "removed":
            color = "#ff4444"
            symbol = "-"
        elif td.status == "modified":
            color = "#d4a030"
            symbol = "~"

        details = ""
        if td.status == "modified":
            parts = []
            if td.devices_added:
                parts.append(f"+{','.join(td.devices_added[:3])}")
            if td.devices_removed:
                parts.append(f"-{','.join(td.devices_removed[:3])}")
            if td.frozen_changed is not None:
                parts.append("frozen" if td.frozen_changed else "unfrozen")
            if td.mute_changed is not None:
                parts.append("muted" if td.mute_changed else "unmuted")
            if parts:
                details = f'<span style="color:{color};font-size:0.8em"> {", ".join(parts)}</span>'

        rows.append(
            f'<tr>'
            f'<td style="color:{color};width:20px">{symbol}</td>'
            f'<td style="color:#b8c8c8">{td.name}</td>'
            f'<td style="color:{color}">{td.status}{details}</td>'
            f'</tr>'
        )

    marker_html = ""
    if diff.markers_added or diff.markers_removed:
        markers = []
        for m in diff.markers_added:
            markers.append(f'<span style="color:#1a9e9e">+{m}</span>')
        for m in diff.markers_removed:
            markers.append(f'<span style="color:#ff4444">-{m}</span>')
        marker_html = f'<p style="color:#6a8a8a">Markers: {", ".join(markers)}</p>'

    bpm_html = ""
    if diff.bpm_changed:
        b, a = diff.bpm_changed
        arrow = "→"
        bpm_html = f'<p style="color:#d4a030">Tempo: {b} {arrow} {a} bpm</p>'

    return f"""
    <div style="background:#0f1a20;border:1px solid #1a3040;border-radius:4px;padding:12px;font-family:monospace;font-size:13px">
      <p style="color:#1a9e9e;margin:0 0 8px 0;font-weight:bold">{diff.summary}</p>
      {bpm_html}
      <table style="border-collapse:collapse;width:100%">
        <thead>
          <tr style="border-bottom:1px solid #1a3040">
            <th style="width:20px"></th>
            <th style="text-align:left;color:#6a8a8a;padding:4px 8px">Track</th>
            <th style="text-align:left;color:#6a8a8a;padding:4px 8px">Change</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
      {marker_html}
    </div>
    """
