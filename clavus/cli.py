"""
Clavus CLI — the primary user interface.

Commands:
  clavus init [path]          Initialize a new clavus project
  clavus snapshot "message"   Tag current state of the .als file
  clavus log                  Show snapshot history
  clavus diff [hash]          Show what changed in a snapshot
  clavus status               Show current project state
  clavus cue "text" @time     Add a timeline-anchored comment
  clavus cues                 List all pending cues
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional

from clavus import parse_als, project_summary
from clavus.store import (
    BlobStore, ClavusProject, diff_projects, format_diff,
    DEFAULT_CLAVUS_DIR,
)
from clavus.cues import (
    CueStore, CueFilter, format_cue, format_cue_list,
    render_cues_as_markers, add_cue_command,
)
from clavus.helpers import find_als_file, get_store_and_project, resolve_snapshot
from clavus.watch import watch as cmd_watch_daemon

# Optional web server
try:
    from clavus.web import run_web_server
    _HAS_WEB = True
except ImportError:
    _HAS_WEB = False

# ─── Commands ──────────────────────────────────────────────────────────

def cmd_init(args: argparse.Namespace) -> None:
    """Initialize a new Clavus project."""
    target = args.path or os.getcwd()
    target = Path(target).resolve()

    als_path = find_als_file(target)
    if als_path is None:
        print(f"❌ No .als file found at {target}")
        print("   Specify the path to an .als file or a directory containing one.")
        sys.exit(1)

    store = BlobStore()
    store.init()

    # Check if already initialized
    existing = store.get_index(als_path.stem)
    if existing:
        print(f"⚠️  Project '{als_path.stem}' already tracked at {existing.root_als}")
        return

    # Parse the .als to get initial info
    project = parse_als(als_path)
    clavus_proj = ClavusProject(
        name=als_path.stem,
        root_als=str(als_path),
        created_at=time.time(),
    )

    # Create initial snapshot
    snap = store.save_snapshot(project, "Initial import", parent=None)
    clavus_proj.head = snap.hash
    store.update_ref("HEAD", snap.hash)
    store.update_ref(f"refs/tags/initial", snap.hash)

    # Save to index
    store.set_index(clavus_proj)

    print(f"📁 Initialized Clavus project '{clavus_proj.name}'")
    print(f"   .als: {als_path}")
    print(f"   Tracking {project.track_count} tracks @ {project.bpm}bpm")
    print(f"   Created snapshot: {snap.short_hash()}")
    print(f"")  # blank line for readability
    print(f"   Next: open the project, make changes, then run:")
    print(f"   clavus snapshot \"your message here\"")


def cmd_snapshot(args: argparse.Namespace) -> None:
    """Create a new snapshot of the current project state."""
    store, proj = get_store_and_project()
    als_path = Path(proj.root_als)
    if not als_path.exists():
        print(f"❌ .als file not found: {als_path}")
        sys.exit(1)

    # Parse current state
    project = parse_als(als_path)

    # Create snapshot
    snap = store.save_snapshot(
        project,
        message=args.message,
        parent=proj.head,
        tags=args.tag.split(",") if args.tag else [],
    )

    # Check if anything actually changed
    if snap.hash == proj.head and proj.head is not None:
        print(f"⚠️  No changes detected — project state is identical to last snapshot.")
        print(f"   Current HEAD: {snap.short_hash()} — '{store.load_snapshot(proj.head).message if store.load_snapshot(proj.head) else ''}'")
        return

    # Update references
    store.update_ref("HEAD", snap.hash)
    proj.head = snap.hash
    store.set_index(proj)

    # Show diff from previous snapshot
    if args.parent:
        parent_snap = store.load_snapshot(args.parent)
    elif snap.parent:
        parent_snap = store.load_snapshot(snap.parent)
    else:
        parent_snap = None

    if parent_snap:
        parent_project = store.load_project(parent_snap.hash)
        if parent_project:
            diff = diff_projects(parent_project, project)
            print(f"📸 Snapshot: {snap.short_hash()} — '{snap.message}'")
            print(f"   {diff.summary}")
            if args.verbose:
                print()
                print(format_diff(diff, verbose=True))
        else:
            print(f"📸 Snapshot: {snap.short_hash()} — '{snap.message}'")
    else:
        print(f"📸 Snapshot: {snap.short_hash()} — '{snap.message}'")
        print(f"   {project.track_count} tracks @ {project.bpm}bpm (initial state)")

    print(f"   📋 Run 'clavus log' to see history.")


def cmd_log(args: argparse.Namespace) -> None:
    """Show snapshot history."""
    store, proj = get_store_and_project()
    current_hash = proj.head
    count = 0

    if not current_hash:
        print("📋 No snapshots yet. Run 'clavus snapshot' to create one.")
        return

    print(f"📋 Snapshot history for '{proj.name}'")
    print()

    while current_hash and count < (args.limit or 20):
        snap = store.load_snapshot(current_hash)
        if not snap:
            break

        is_head = "➡ " if current_hash == store.read_ref("HEAD") else "  "
        time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(snap.timestamp))

        tags = ""
        if snap.tags:
            tags = f" [{', '.join(snap.tags[:3])}]"

        print(f"  {is_head}{snap.short_hash()}  {time_str}")
        if args.verbose:
            print(f"     Tracks: {snap.track_count}  BPM: {snap.bpm}")
        print(f"     {snap.message}{tags}")

        current_hash = snap.parent
        count += 1

        if count < (args.limit or 20) and current_hash:
            print()

    if current_hash and count >= (args.limit or 20):
        print()
        print(f"  ... and more. Use --limit to show more.")


def cmd_diff(args: argparse.Namespace) -> None:
    """Show what changed in a snapshot vs its parent."""
    store, proj = get_store_and_project()

    if args.hash:
        hash_str = resolve_snapshot(store, args.hash)
        if not hash_str:
            print(f"❌ Could not resolve '{args.hash}'")
            sys.exit(1)
    else:
        hash_str = store.read_ref("HEAD")
        if not hash_str:
            print("📋 No snapshots yet.")
            return

    snap = store.load_snapshot(hash_str)
    if not snap:
        print(f"❌ Snapshot not found: {hash_str}")
        return

    current_project = store.load_project(hash_str)
    if not current_project:
        print(f"❌ Could not load project data for {hash_str}")
        return

    if snap.parent:
        parent_project = store.load_project(snap.parent)
        if parent_project:
            diff = diff_projects(parent_project, current_project)
            print(f"📊 {snap.short_hash()} — '{snap.message}'")
            print()
            print(format_diff(diff, verbose=args.verbose))
            return

    # No parent — show basic info
    print(f"📊 {snap.short_hash()} — '{snap.message}'")
    print(f"   {snap.track_count} tracks @ {snap.bpm}bpm (initial state)")


def cmd_status(args: argparse.Namespace) -> None:
    """Show current project status."""
    store, proj = get_store_and_project()

    als_path = Path(proj.root_als)
    als_exists = als_path.exists()
    last_snap = store.load_snapshot(proj.head) if proj.head else None

    print(f"📁 '{proj.name}'")
    print(f"   Path: {proj.root_als}")
    print(f"   Branch: {proj.branch}")
    print(f"   Status: {'✅ exists' if als_exists else '❌ missing'}")
    print()

    if last_snap:
        project = None
        if als_exists:
            project = parse_als(als_path)
            old_project = store.load_project(last_snap.hash)
            if old_project and project:
                diff = diff_projects(old_project, project)
                print(f"   HEAD: {last_snap.short_hash()} — '{last_snap.message}'")
                if diff.summary != "No changes":
                    print(f"   ⚠️  Unsaved changes detected:")
                    print(f"      {diff.summary}")
                else:
                    print(f"   ✅ Up to date with last snapshot")
        else:
            print(f"   HEAD: {last_snap.short_hash()} — '{last_snap.message}'")
    else:
        print(f"   No snapshots yet.")


def cmd_watch(args: argparse.Namespace) -> None:
    """Start the file watcher daemon."""
    store, proj = _get_store_and_project()
    cmd_watch_daemon(
        store,
        proj,
        cooldown=args.cooldown,
        verbose=not args.quiet,
        once=args.once,
    )


def cmd_serve(args: argparse.Namespace) -> None:
    """Start the web companion server."""
    try:
        from clavus.web import run_web_server
    except ImportError:
        print("❌ Web companion requires fastapi and uvicorn.")
        print("   Install with: pip install fastapi uvicorn")
        sys.exit(1)
    run_web_server(host=args.host, port=args.port)


def cmd_tui(args: argparse.Namespace) -> None:
    """Launch the Textual TUI."""
    try:
        from clavus.tui import run_tui
    except ImportError:
        print("❌ TUI requires textual and httpx.")
        print("   Install with: pip install textual httpx")
        sys.exit(1)
    run_tui(connect_url=args.connect)


def cmd_cue(args: argparse.Namespace) -> None:
    """Add a timeline-anchored comment."""
    store, proj = get_store_and_project()
    head = store.read_ref("HEAD")

    position = args.position or "0.0.0"
    # Strip @ prefix if present
    if position.startswith("@"):
        position = position[1:]

    cue = add_cue_command(
        text=args.text,
        position=position,
        track=args.track or "",
        store=store,
    )

    if cue:
        print(f"💬 Cue added at @{position}")
        print(f"   \"{cue.text}\"")
        print(f"   id: {cue.id}")
        if args.track:
            print(f"   Track: {args.track}")
        print(f"   📋 Reply: clavus cue reply {cue.id} \"your response\"")


def cmd_cue_reply(args: argparse.Namespace) -> None:
    """Reply to a cue thread."""
    store, proj = get_store_and_project()
    cues = CueStore(proj.name, store=store)
    head = store.read_ref("HEAD")

    reply = cues.reply(args.cue_id, args.text, snapshot_hash=head or "")
    if reply:
        print(f"💬 Reply added to cue {args.cue_id}")
        print(f"   \"{args.text}\"")
    else:
        print(f"❌ Cue '{args.cue_id}' not found.")


def cmd_cue_resolve(args: argparse.Namespace) -> None:
    """Resolve a cue."""
    store, proj = get_store_and_project()
    cues = CueStore(proj.name, store=store)

    cue = cues.resolve(args.cue_id, note=args.note or "")
    if cue:
        print(f"✅ Cue {args.cue_id} resolved")
        if args.note:
            print(f"   \"{args.note}\"")
    else:
        print(f"❌ Cue '{args.cue_id}' not found.")


def cmd_cue_skip(args: argparse.Namespace) -> None:
    """Skip a cue."""
    store, proj = get_store_and_project()
    cues = CueStore(proj.name, store=store)

    cue = cues.skip(args.cue_id, reason=args.reason or "")
    if cue:
        print(f"⏭ Cue {args.cue_id} skipped")
        if args.reason:
            print(f"   \"{args.reason}\"")
    else:
        print(f"❌ Cue '{args.cue_id}' not found.")


def cmd_cues(args: argparse.Namespace) -> None:
    """List all cues."""
    store, proj = get_store_and_project()
    cues = CueStore(proj.name, store=store)

    filter_ = CueFilter()
    if args.pending_only:
        filter_.status = "pending"
    if args.author:
        filter_.author = args.author

    all_cues = cues.list_cues(filter_)
    print(format_cue_list(all_cues, verbose=args.verbose))


def cmd_cue_render(args: argparse.Namespace) -> None:
    """Export unresolved cues as Ableton markers — either to file or injected into the .als."""
    store, proj = get_store_and_project()
    cues = CueStore(proj.name, store=store)

    unresolved = cues.list_cues(CueFilter(status="pending"))
    if not unresolved:
        print("💬 No unresolved cues to render.")
        return

    if args.inject:
        # Inject directly into the project's .als file
        render_cues_as_markers(unresolved, "", inject_into_als=proj.root_als)
    else:
        output = args.output or f"{proj.name}_cues.xml"
        render_cues_as_markers(unresolved, output)
        print(f"📍 Rendered {len(unresolved)} cues to {output}")
        print(f"   Import into Ableton by merging <CuePoints> into your .als file.")


# ─── Main Entry Point ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Clavus — Git for Ableton Live projects.",
        prog="clavus",
    )
    parser.add_argument("--clavus-dir", help="Override clavus storage directory")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init
    p_init = subparsers.add_parser("init", help="Initialize a new clavus project")
    p_init.add_argument("path", nargs="?", default=None, help="Path to .als file or project directory")

    # Snapshot
    p_snap = subparsers.add_parser("snapshot", help="Create a new snapshot")
    p_snap.add_argument("message", help="Description of what changed")
    p_snap.add_argument("--tag", "-t", default="", help="Comma-separated tags")
    p_snap.add_argument("--parent", "-p", default=None, help="Override parent snapshot hash")
    p_snap.add_argument("--verbose", "-v", action="store_true", help="Show detailed diff")

    # Log
    p_log = subparsers.add_parser("log", help="Show snapshot history")
    p_log.add_argument("--limit", "-n", type=int, default=20, help="Max snapshots to show")
    p_log.add_argument("--verbose", "-v", action="store_true", help="Show detailed info per snapshot")

    # Diff
    p_diff = subparsers.add_parser("diff", help="Show changes in a snapshot")
    p_diff.add_argument("hash", nargs="?", default=None, help="Snapshot hash or ref name (default: HEAD)")
    p_diff.add_argument("--verbose", "-v", action="store_true", help="Show unchanged tracks")

    # Status
    subparsers.add_parser("status", help="Show current project status")

    # Cues
    p_cue = subparsers.add_parser("cue", help="Add a timeline-anchored comment")
    p_cue.add_argument("text", help="The comment text")
    p_cue.add_argument("position", nargs="?", default="0.0.0", help="Position (e.g. @1:23 or 4.1.1)")
    p_cue.add_argument("--track", "-t", default="", help="Which track this cue is about")
    p_cue.add_argument("--author", "-a", default="", help="Override author name")

    p_cue_reply = subparsers.add_parser("cue-reply", help="Reply to a cue thread")
    p_cue_reply.add_argument("cue_id", help="ID of the cue to reply to")
    p_cue_reply.add_argument("text", help="Reply text")

    p_cue_resolve = subparsers.add_parser("cue-resolve", help="Mark a cue as resolved")
    p_cue_resolve.add_argument("cue_id", help="ID of the cue to resolve")
    p_cue_resolve.add_argument("--note", "-n", default="", help="Optional resolution note")

    p_cue_skip = subparsers.add_parser("cue-skip", help="Skip a cue without resolving")
    p_cue_skip.add_argument("cue_id", help="ID of the cue to skip")
    p_cue_skip.add_argument("--reason", "-r", default="", help="Why it was skipped")

    p_cues = subparsers.add_parser("cues", help="List all cues")
    p_cues.add_argument("--pending", "-p", dest="pending_only", action="store_true",
                       help="Show only pending (unresolved) cues")
    p_cues.add_argument("--author", "-a", default="", help="Filter by author")
    p_cues.add_argument("--verbose", "-v", action="store_true", help="Show replies and resolved cues")

    p_cue_render = subparsers.add_parser("cue-render", help="Export cues as Ableton markers")
    p_cue_render.add_argument("--output", "-o", default="", help="Output file path")
    p_cue_render.add_argument("--inject", action="store_true",
                             help="Inject cues directly into the project's .als file (creates backup)")

    # Watch
    p_watch = subparsers.add_parser("watch", help="Auto-snapshot on file changes")
    p_watch.add_argument("--cooldown", "-c", type=int, default=30,
                        help="Seconds to wait after last change before snapshotting (default: 30)")
    p_watch.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress detailed output")
    p_watch.add_argument("--once", action="store_true",
                        help="Take one snapshot and exit (useful for cron jobs)")

    # Serve (web companion)
    p_serve = subparsers.add_parser("serve", help="Start the web companion UI")
    p_serve.add_argument("--host", default="0.0.0.0",
                        help="Host to bind to (default: 0.0.0.0)")
    p_serve.add_argument("--port", "-p", type=int, default=7890,
                        help="Port to listen on (default: 7890)")

    # TUI (terminal dashboard)
    p_tui = subparsers.add_parser("tui", help="Launch the TUI dashboard")
    p_tui.add_argument("--connect", "-c", default="",
                       help="Clavus server URL (default: http://localhost:7890)")

    args = parser.parse_args()

    # Override clavus directory if specified
    if args.clavus_dir:
        DEFAULT_CLAVUS_DIR = Path(args.clavus_dir)

    # Dispatch
    commands = {
        "init": cmd_init,
        "snapshot": cmd_snapshot,
        "log": cmd_log,
        "diff": cmd_diff,
        "status": cmd_status,
        "watch": cmd_watch,
        "serve": cmd_serve,
        "tui": cmd_tui,
        "cue": cmd_cue,
        "cue-reply": cmd_cue_reply,
        "cue-resolve": cmd_cue_resolve,
        "cue-skip": cmd_cue_skip,
        "cues": cmd_cues,
        "cue-render": cmd_cue_render,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
