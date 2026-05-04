#!/usr/bin/env python3
"""Full CLI workflow test with simulated project changes. Self-contained, uses temp dirs."""
import sys, os, shutil, time, tempfile, gzip
from pathlib import Path
from xml.etree import ElementTree as ET
from argparse import Namespace

# Use temp dir — NEVER touch real ~/.clavus
TMP = Path(tempfile.mkdtemp(prefix="clavus_test_"))
CLAVUS_DIR = TMP / ".clavus"
os.environ["CLAVUS_DIR"] = str(CLAVUS_DIR)

# Use the fixture .als (committed in repo, no LaCie needed)
FIXTURE = Path(__file__).parent / "fixtures" / "test_project.als"
if not FIXTURE.exists():
    print(f"❌ Fixture not found: {FIXTURE}")
    print("   Run python3 fixtures/gen_fixture.py first")
    sys.exit(1)

test_dir = TMP / "project"
test_dir.mkdir(parents=True, exist_ok=True)
test_als = test_dir / "Test Project.als"
shutil.copy2(str(FIXTURE), str(test_als))

sys.path.insert(0, str(Path(__file__).parent))

from clavus.cli import cmd_init, cmd_snapshot, cmd_log, cmd_diff, cmd_status
from clavus.store import DEFAULT_CLAVUS_DIR

print(f"📁 Test dir: {TMP}")
print(f"📁 Clavus dir: {CLAVUS_DIR}")

print("\n═══ 1. clavus init ═══")
cmd_init(Namespace(path=str(test_als), command="init", clavus_dir=str(CLAVUS_DIR)))

print("\n═══ 2. clavus status ═══")
cmd_status(Namespace(command="status", clavus_dir=str(CLAVUS_DIR)))

print("\n═══ 3. clavus snapshot (no change — should warn) ═══")
cmd_snapshot(Namespace(message="just checking", tag="", parent=None,
                       verbose=True, command="snapshot", clavus_dir=str(CLAVUS_DIR)))

print("\n═══ 4. Modify the .als (simulate: rename a track) ═══")
with gzip.open(test_als, "rb") as f:
    raw = f.read()
root = ET.fromstring(raw)
# Handle Ableton 10+ wrapper
if root.tag == "Ableton":
    live_set = root.find("LiveSet")
else:
    live_set = root
if live_set is None:
    print(f"❌ No <LiveSet> in XML (root tag: {root.tag})")
    sys.exit(1)

# First audio track: set its UserName to mark it as modified
# Find tracks — fixture uses direct children (Live 9), real projects use <Tracks> wrapper
tracks = live_set.find("Tracks")
if tracks is None:
    # Live 9 format: tracks are direct children
    tracks = live_set
modded = False
for t in tracks:
    if t.tag == "AudioTrack":
        nv = t.find("Name")
        if nv is not None:
            if nv.get("Value"):
                old = nv.get("Value")
                nv.set("Value", "Kick_Modified")
                modded = True
                print(f"   Old name: {old} → Kick_Modified")
                break
            # Try nested EffectiveName (Live 10+)
            effective = nv.find("EffectiveName")
            if effective is not None:
                old = effective.get("Value")
                effective.set("Value", "Kick_Modified")
                modded = True
                print(f"   Old name: {old} → Kick_Modified")
                break
if not modded:
    print("⚠️  Could not find an AudioTrack to modify")
    sys.exit(1)

with gzip.open(test_als, "wb") as f:
    f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write(ET.tostring(root, encoding="utf-8"))
print("   ✅ Track renamed to Kick_Modified")

print("\n═══ 5. clavus snapshot (actual change) ═══")
cmd_snapshot(Namespace(message="renamed kick track", tag="arrangement",
                       parent=None, verbose=True, command="snapshot",
                       clavus_dir=str(CLAVUS_DIR)))

print("\n═══ 6. clavus log ═══")
cmd_log(Namespace(limit=10, verbose=True, graph=False, command="log",
                  clavus_dir=str(CLAVUS_DIR)))

print("\n═══ 7. Modifying again: rename track ═══")
with gzip.open(test_als, "rb") as f:
    raw = f.read()
root = ET.fromstring(raw)
if root.tag == "Ableton":
    live_set = root.find("LiveSet")
else:
    live_set = root
if live_set is None:
    print("❌ No <LiveSet> in XML")
    sys.exit(1)
# Find tracks — fixture uses direct children, real projects use <Tracks> wrapper
tracks = live_set.find("Tracks")
if tracks is None:
    tracks = live_set
for t in tracks:
    if t.tag == "AudioTrack":
        nv = t.find("Name")
        if nv is not None:
            if nv.get("Value"):
                nv.set("Value", "Kick_130")
                modded = True
                break
            effective = nv.find("EffectiveName")
            if effective is not None:
                effective.set("Value", "Kick_130")
                modded = True
                break

with gzip.open(test_als, "wb") as f:
    f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write(ET.tostring(root, encoding="utf-8"))
print("   ✅ Track renamed")

cmd_snapshot(Namespace(message="renamed kick track for new tempo", tag="",
                       parent=None, verbose=True, command="snapshot",
                       clavus_dir=str(CLAVUS_DIR)))

print("\n═══ 8. clavus log (full) ═══")
cmd_log(Namespace(limit=20, verbose=True, graph=False, command="log",
                  clavus_dir=str(CLAVUS_DIR)))

print("\n═══ 9. clavus diff HEAD ═══")
cmd_diff(Namespace(hash=None, verbose=True, visual=False, command="diff",
                   clavus_dir=str(CLAVUS_DIR)))

print("\n═══ 10. clavus status ═══")
cmd_status(Namespace(command="status", clavus_dir=str(CLAVUS_DIR)))

# Cleanup
shutil.rmtree(str(TMP), ignore_errors=True)
print(f"\n✅ Full CLI workflow test passed! (cleaned up {TMP})")
