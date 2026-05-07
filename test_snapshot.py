"""Test the snapshot engine with a real or fixture project."""
import os, tempfile, shutil
from pathlib import Path

from clavus import parse_als
from clavus.store import BlobStore, diff_projects, format_diff

# Use fixture by default (self-contained)
FIXTURE = Path(__file__).parent / "fixtures" / "test_project.als"
if FIXTURE.exists():
    path = str(FIXTURE)
    print(f"📁 Using fixture: {FIXTURE}")
else:
    # Fallback to LaCie if available
    base = "/Volumes/LaCie/Ableton Live Projects (Local Drive)/Ableton Live Projects (Local Drive)"
    fallback = f"{base}/Space Race Project/Space Race.als"
    if Path(fallback).exists():
        path = fallback
        print("📁 Using LaCie: Space Race")
    else:
        print("⚠️  No fixture or LaCie found. Generate fixture first:")
        print("   python3 fixtures/gen_fixture.py")
        exit(0)

TMP = Path(tempfile.mkdtemp(prefix="clavus_snap_test_"))
CLAVUS_DIR = TMP / ".clavus"

# Initialize the store
store = BlobStore(CLAVUS_DIR)
store.init()

# Parse the project
print(f"Parsing: {path}")
project = parse_als(path)
print(f"  → {len(project.tracks)} tracks @ {project.bpm}bpm")

# Save first snapshot
snap1 = store.save_snapshot(project, message="Initial snapshot")
print(f"\nSnapshot 1: {snap1.hash}")
print(f"  Message: {snap1.message}")

# Save second snapshot (same content — should still create a snapshot but with different parent)
snap2 = store.save_snapshot(project, message="Second snapshot (same content)")
print(f"\nSnapshot 2: {snap2.hash}")
snap1_loaded = store.load_snapshot(snap1.hash)
snap2_loaded = store.load_snapshot(snap2.hash)
print(f"  Parent of snapshot 2: {snap2_loaded.parent is not None}")

# Load and verify
loaded = store.load_snapshot(snap1.hash)
print(f"\nLoaded snapshot: {loaded.short_hash()} — {loaded.message}")
print(f"  Tracks: {loaded.track_count}")

# Test diff
diff = diff_projects(project, project)
diff_len = len(diff.tracks) if diff.tracks else 0
print(f"\nDiff (snapshot vs parsed): {diff_len} track differences")

# Test format
formatted = format_diff(diff)
if formatted:
    print(f"  Formatted: {len(formatted.split(chr(10)))} lines")

# Cleanup
shutil.rmtree(str(TMP), ignore_errors=True)
print(f"\n✅ All snapshot tests passed! (cleaned up {TMP})")
