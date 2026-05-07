#!/usr/bin/env python3
"""Test the full CLI workflow end-to-end. Self-contained, uses temp dirs."""
import sys, os, shutil, tempfile, gzip
from pathlib import Path
from argparse import Namespace

TMP = Path(tempfile.mkdtemp(prefix="clavus_test_"))
CLAVUS_DIR = TMP / ".clavus"
os.environ["CLAVUS_DIR"] = str(CLAVUS_DIR)

FIXTURE = Path(__file__).parent / "fixtures" / "test_project.als"
if not FIXTURE.exists():
    print(f"❌ Fixture not found: {FIXTURE}")
    sys.exit(1)

test_dir = TMP / "project"
test_dir.mkdir(parents=True, exist_ok=True)
test_als = test_dir / "Test Project.als"
shutil.copy2(str(FIXTURE), str(test_als))

sys.path.insert(0, str(Path(__file__).parent))

from clavus.cli import cmd_init, cmd_snapshot, cmd_log, cmd_diff, cmd_status
from clavus.store import BlobStore

cwd = os.getcwd()

print(f"📁 Test dir: {TMP}")
print(f"📁 Clavus dir: {CLAVUS_DIR}")

print("\n═══ 1. clavus init ═══")
args = Namespace(path=str(test_als), command="init", clavus_dir=str(CLAVUS_DIR))
cmd_init(args)

print("\n═══ 2. clavus status ═══")
args = Namespace(command="status", clavus_dir=str(CLAVUS_DIR))
cmd_status(args)

print("\n═══ 3. clavus snapshot (first change) ═══")
args = Namespace(message="added reverb on master", tag="mix", parent=None,
                 verbose=True, command="snapshot", clavus_dir=str(CLAVUS_DIR))
cmd_snapshot(args)

print("\n═══ 4. clavus snapshot (second change) ═══")
args = Namespace(message="brought kick up 2dB", tag="mix,kick",
                 parent=None, verbose=False, command="snapshot",
                 clavus_dir=str(CLAVUS_DIR))
cmd_snapshot(args)

print("\n═══ 5. clavus log ═══")
args = Namespace(limit=10, verbose=True, graph=False, command="log",
                 clavus_dir=str(CLAVUS_DIR))
cmd_log(args)

print("\n═══ 6. clavus diff HEAD ═══")
args = Namespace(hash=None, verbose=True, command="diff",
                 clavus_dir=str(CLAVUS_DIR))
cmd_diff(args)

print("\n═══ 7. clavus diff (first snapshot by hash) ═══")
store = BlobStore(CLAVUS_DIR)
head = store.read_ref("HEAD")
snap = store.load_snapshot(head)
if snap:
    args = Namespace(hash=snap.short_hash(), verbose=True, command="diff",
                     clavus_dir=str(CLAVUS_DIR))
    cmd_diff(args)

# Cleanup
os.chdir(cwd)
shutil.rmtree(str(TMP), ignore_errors=True)
print(f"\n✅ CLI workflow test complete! (cleaned up {TMP})")
