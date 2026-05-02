"""Tests for the clavus watch daemon.

Tests use a copy of the fixture .als and a temp clavus directory
to avoid interfering with the real project index.
"""

import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, os.path.expanduser("~/Developer/clavus"))

FIXTURE_ALS = os.path.expanduser(
    "~/Developer/clavus/fixtures/test_project.als"
)

TMP = tempfile.mkdtemp(prefix="clavus_watch_test_")
TEST_ALS = os.path.join(TMP, "test_project.als")
CLAVUS_DIR = os.path.join(TMP, ".clavus")

shutil.copy2(FIXTURE_ALS, TEST_ALS)

from clavus.watch import watch_once
from clavus.store import BlobStore, ClavusProject
from clavus import parse_als

# ─── Setup: init clavus in temp dir ─────────────────────────────────────

store = BlobStore(Path(CLAVUS_DIR))
store.init()

project = parse_als(TEST_ALS)
snap = store.save_snapshot(project, "Initial import", parent=None)
proj = ClavusProject(
    name="test_project",
    root_als=TEST_ALS,
    created_at=time.time(),
    head=snap.hash,
)
store.update_ref("HEAD", snap.hash)
store.set_index(proj)

first_hash = snap.hash
print(f"✅ Initial snapshot: {snap.short_hash()}")
print(f"   Tracks: {project.track_count}  BPM: {project.bpm}")

# ─── Test 1: No changes → no snapshot ───────────────────────────────────

taken = watch_once(store, proj, verbose=False)
assert not taken, "Should NOT snapshot when nothing changed"
print("✅ Test 1: No change → no snapshot (correct)")

# ─── Test 2: Modify the .als → should snapshot ──────────────────────────

# Simulate a change: rename a track the parser will detect
import gzip
import xml.etree.ElementTree as ET

with gzip.open(TEST_ALS, "rb") as f:
    raw = f.read()
root = ET.fromstring(raw)

# Find first audio track and rename it
for child in root:
    if child.tag in ("AudioTrack", "MidiTrack", "GroupTrack"):
        name_elem = child.find("Name")
        if name_elem is not None:
            name_elem.set("Value", "Kick (Watch Test)")
        break

xml_bytes = ET.tostring(root, encoding="unicode").encode("utf-8")
with gzip.open(TEST_ALS, "wb") as f:
    f.write(xml_bytes)

time.sleep(0.05)

taken = watch_once(store, proj, verbose=False)
assert taken, "Should snapshot when .als changes"
print(f"✅ Test 2: Change detected → snapshot taken ({proj.head[:8]})")

# Verify the new snapshot is different from the first
assert proj.head != first_hash, "Snapshot hash should differ after change"
print("   Hash differs from initial — correct")

# ─── Test 3: watch_once with no changes again ───────────────────────────

taken = watch_once(store, proj, verbose=False)
assert not taken, "Should NOT snapshot again on same content"
print("✅ Test 3: Same content → no snapshot (correct)")

# ─── Cleanup ────────────────────────────────────────────────────────────

shutil.rmtree(TMP, ignore_errors=True)
print(f"\n✅ All watch tests passed!")
