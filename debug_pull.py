#!/usr/bin/env python3
"""Debug why pull_stems_from_remote returns 0."""
import subprocess, os, tempfile, time, requests, sys
from pathlib import Path

tmp = Path(tempfile.mkdtemp())
store_dir = tmp / "chris"
store_dir.mkdir()

os.environ["CLAVUS_DIR"] = str(store_dir)
sys.path.insert(0, str(Path("/Users/slowhands/Developer/clavus")))

from clavus.store import BlobStore, ClavusProject, StemStore, StemManifest, StemEntry
import hashlib, struct

store = BlobStore(store_dir)
store.init()

proj = ClavusProject(name="chris-project", root_als=str(tmp / "chris-project.als"), created_at=time.time())
store.set_index(proj)

snap_hash = hashlib.sha256(b"test").hexdigest()
proj.head = snap_hash
store.update_ref("HEAD", snap_hash)
store.set_index(proj)

# Make a real-ish WAV
kick_wav = tmp / "Kick.wav"
with open(kick_wav, "wb") as f:
    import math
    sample_rate = 44100
    num_samples = 441  # 10ms
    data_size = num_samples * 2 * 2  # 16-bit stereo
    f.write(b"RIFF")
    f.write(struct.pack("<I", 36 + data_size))
    f.write(b"WAVE")
    f.write(b"fmt ")
    f.write(struct.pack("<I", 16))
    f.write(struct.pack("<H", 1))
    f.write(struct.pack("<H", 2))
    f.write(struct.pack("<I", sample_rate))
    f.write(struct.pack("<I", sample_rate * 2 * 2))
    f.write(struct.pack("<H", 4))
    f.write(struct.pack("<H", 16))
    f.write(b"data")
    f.write(struct.pack("<I", data_size))
    for i in range(num_samples):
        val = int(math.sin(2 * math.pi * 440 * i / sample_rate) * 32767)
        f.write(struct.pack("<h", val))
        f.write(struct.pack("<h", val))

stem_store = StemStore("chris-project", store)
entry = stem_store.store_stem_file(str(kick_wav), "Kick")
manifest = StemManifest(snapshot_hash=snap_hash, stems=[entry])
stem_store.save_manifest(manifest)

print(f"Project name: '{proj.name}'")
print(f"Snap hash: {snap_hash[:12]}...")
print(f"Manifest exists: {stem_store.get_manifest(snap_hash) is not None}")
print(f"Projects: {[p.name for p in store.list_projects()]}")
print(f"Stored stem: {entry.hash[:12]}")

# Start server
proc = subprocess.Popen(
    ["python3", "-m", "uvicorn", "clavus.web:app",
     "--host", "127.0.0.1", "--port", "9898", "--log-level", "error"],
    cwd="/Users/slowhands/Developer/clavus",
    env={**os.environ, "CLAVUS_DIR": str(store_dir)},
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
time.sleep(2)

# Test routes
print(f"\n--- Route tests ---")
r = requests.get("http://127.0.0.1:9898/api/projects", timeout=3)
print(f"GET /api/projects: {r.status_code} -> {r.json()}")

r = requests.get(f"http://127.0.0.1:9898/api/stems/chris-project/manifest/{snap_hash}", timeout=3)
print(f"GET /api/stems/chris-project/manifest/...: {r.status_code} -> {r.text[:200]}")

# The route uses path params. In FastAPI, hyphens should work fine.
# Let me check if the issue is the project lookup
r = requests.get(f"http://127.0.0.1:9898/api/project?name=chris-project", timeout=3)
print(f"GET /api/project?name=chris-project: {r.status_code} -> {'error' in r.json() if r.status_code == 200 else 'N/A'}")

if r.status_code == 200:
    data = r.json()
    print(f"  project name in response: {data.get('name')}")

proc.terminate()
proc.wait()

import shutil
shutil.rmtree(tmp)
print("\nDone")
