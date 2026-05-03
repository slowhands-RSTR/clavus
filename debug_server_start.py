#!/usr/bin/env python3
"""Quick debug: why does server not respond in the test?"""
import subprocess, os, tempfile, time, requests, sys
from pathlib import Path

tmp = Path(tempfile.mkdtemp())
chris = tmp / 'chris_store'
chris.mkdir()

os.environ['CLAVUS_DIR'] = str(chris)
sys.path.insert(0, '/Users/slowhands/Developer/clavus')
from clavus.store import BlobStore, ClavusProject, StemStore, StemManifest, StemEntry
import hashlib, struct, math

store = BlobStore(chris)
store.init()
snap_hash = 'a1b2c3d4e5f6' + '0'*52
proj = ClavusProject(name='chris-project', root_als=str(tmp / 'c.als'), created_at=time.time())
store.set_index(proj)
proj.head = snap_hash
store.update_ref('HEAD', snap_hash)
store.set_index(proj)

wav = tmp / 'Kick.wav'
with open(wav, 'wb') as f:
    n = 441; ds = n * 4
    f.write(b'RIFF' + struct.pack('<I', 36+ds) + b'WAVE')
    f.write(b'fmt ')
    f.write(struct.pack('<I', 16) + struct.pack('<H', 1) + struct.pack('<H', 2))
    f.write(struct.pack('<I', 44100) + struct.pack('<I', 176400))
    f.write(struct.pack('<H', 4) + struct.pack('<H', 16))
    f.write(b'data' + struct.pack('<I', ds))
    for i in range(n):
        v = int(math.sin(2*math.pi*440*i/44100)*32767)
        f.write(struct.pack('<hh', v, v))

sm = StemStore('chris-project', store)
entry = sm.store_stem_file(str(wav), 'Kick')
sm.save_manifest(StemManifest(snapshot_hash=snap_hash, stems=[entry]))

print(f'Data written. Projects: {[p.name for p in store.list_projects()]}')

# Start server with MINIMAL env
proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'clavus.web:app',
     '--host', '127.0.0.1', '--port', '9886', '--log-level', 'error'],
    cwd='/Users/slowhands/Developer/clavus',
    env={'CLAVUS_DIR': str(chris), 'PATH': os.environ.get('PATH', '')},
    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
)
time.sleep(2)

print(f'Server process alive: {proc.poll() is None}')
if proc.poll() is not None:
    stdout, stderr = proc.communicate()
    print(f'Exit code: {proc.returncode}')
    print(f'stderr: {stderr.decode()[:500]}')

try:
    r = requests.get('http://127.0.0.1:9886/api/projects', timeout=3)
    print(f'Projects response: {r.status_code} -> {r.json()}')
except Exception as e:
    print(f'Connection failed: {e}')

proc.terminate()
proc.wait()
import shutil; shutil.rmtree(tmp)
print('Done')
