#!/usr/bin/env python3
"""Debug pull_stems_from_remote."""
import subprocess, os, tempfile, time, requests, sys
from pathlib import Path

tmp = Path(tempfile.mkdtemp())

os.environ["CLAVUS_DIR"] = str(tmp / "chris")
sys.path.insert(0, "/Users/slowhands/Developer/clavus")

from clavus.store import BlobStore, ClavusProject, StemStore, StemManifest, StemEntry
import hashlib, struct, math

# Setup Chris store
chris_dir = tmp / "chris"
chris_dir.mkdir()
chris_store = BlobStore(chris_dir)
chris_store.init()
snap_hash = hashlib.sha256(b"test").hexdigest()
chris_proj = ClavusProject(name="chris-project", root_als=str(tmp / "chris.als"), created_at=time.time())
chris_store.set_index(chris_proj)
chris_proj.head = snap_hash
chris_store.update_ref("HEAD", snap_hash)
chris_store.set_index(chris_proj)

# Create WAV
wav = tmp / "Kick.wav"
n = 441; ds = n * 4
with open(wav, "wb") as f:
    f.write(b"RIFF" + struct.pack("<I", 36+ds) + b"WAVE")
    f.write(b"fmt ")
    f.write(struct.pack("<I", 16))
    f.write(struct.pack("<H", 1))    # PCM
    f.write(struct.pack("<H", 2))    # stereo
    f.write(struct.pack("<I", 44100))# sample rate
    f.write(struct.pack("<I", 176400))# byte rate
    f.write(struct.pack("<H", 4))    # block align
    f.write(struct.pack("<H", 16))   # bits per sample
    f.write(b"data")
    f.write(struct.pack("<I", ds))
    for i in range(n):
        v = int(math.sin(2*math.pi*440*i/44100)*32767)
        f.write(struct.pack("<hh", v, v))

# Import stem
stem_store = StemStore("chris-project", chris_store)
entry = stem_store.store_stem_file(str(wav), "Kick")
stem_store.save_manifest(StemManifest(snapshot_hash=snap_hash, stems=[entry]))

# Start server in subprocess  
proc = subprocess.Popen(
    ["python3", "-m", "uvicorn", "clavus.web:app",
     "--host", "127.0.0.1", "--port", "9875", "--log-level", "error"],
    cwd="/Users/slowhands/Developer/clavus",
    env={**os.environ, "CLAVUS_DIR": str(chris_dir)},
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
time.sleep(2)

# Setup Steven store (different dir)
steven_dir = tmp / "steven"
steven_dir.mkdir()
steven_store = BlobStore(steven_dir)
steven_store.init()
steven_proj = ClavusProject(name="chris-project", root_als=str(tmp / "steven.als"), created_at=time.time())
steven_store.set_index(steven_proj)
steven_proj.head = snap_hash
steven_store.update_ref("HEAD", snap_hash)
steven_store.set_index(steven_proj)

from clavus.sync import pull_stems_from_remote, Remote

remote = Remote(name="chris", url="http://127.0.0.1:9875")

print(f"Steven store dir: {steven_dir}")
print(f"Steven HEAD: {steven_store.read_ref('HEAD')[:12]}")
print(f"Project name: {steven_proj.name}")
print(f"Remote URL: {remote.url}")

# Monkey-patch to avoid store path issues in sync function
# Actually, the sync function takes store and proj as args - it should use those
# But SyncClient might construct new BlobStore() internally
from clavus.sync import SyncClient
client = SyncClient("http://127.0.0.1:9875")

# Test the URL directly
url = f"http://127.0.0.1:9875/api/stems/chris-project/manifest/{snap_hash}"
print(f"\nDirect URL: {url}")
r = requests.get(url, timeout=3)
print(f"Direct: {r.status_code} -> {r.text[:300]}")

# Now try the real pull
count = pull_stems_from_remote(steven_store, steven_proj, remote)
print(f"\nPull result: {count}")

steven_stem_store = StemStore("chris-project", steven_store)
print(f"Steven has kick: {steven_store.has_object(entry.hash)}")
print(f"Steven has manifest: {steven_stem_store.get_manifest(snap_hash) is not None}")

proc.terminate()
proc.wait()
import shutil; shutil.rmtree(tmp)
