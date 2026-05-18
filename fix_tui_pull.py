#!/usr/bin/env python3
"""Fix _do_pull: for localhost, skip pull_snapshot_blobs when relay is down."""
with open("/Users/slowhands/Developer/clavus/clavus/tui.py") as f:
    content = f.read()

old_pull_block = """            if is_localhost:
                self._load_cues_from_disk()
                self._load_snapshots_from_disk()
                cues_n = len(self.cues)
                snaps_n = len(self.snaps)
                conflicts_n = sum(1 for c in self.cues if getattr(c, '_conflict', False))
                # Still pull blobs from relay (they may need materialization)
                _, failed = await asyncio.to_thread(pull_snapshot_blobs, self.store, proj_index, remote, _on_blob_progress)"""

new_pull_block = """            # Fast path: localhost → data's already on disk, just re-read
            is_localhost = remote.url.startswith("http://localhost") or remote.url.startswith("http://127.0.0.1")
            relay_live = True
            if is_localhost:
                # Check if relay is actually running before trying blob ops
                try:
                    import urllib.request
                    r = urllib.request.urlopen(f"{remote.url.rstrip('/')}/api/ping", timeout=2)
                    relay_live = (r.status == 200)
                except Exception:
                    relay_live = False
            blobs = 0
            failed: list[str] = []
            if is_localhost:
                self._load_cues_from_disk()
                self._load_snapshots_from_disk()
                cues_n = len(self.cues)
                snaps_n = len(self.snaps)
                conflicts_n = sum(1 for c in self.cues if getattr(c, '_conflict', False))
                # Only pull blobs if relay is running (solo mode: skip entirely)
                if relay_live:
                    _, failed = await asyncio.to_thread(pull_snapshot_blobs, self.store, proj_index, remote, _on_blob_progress)
                else:
                    self._log_event("solo pull: relay offline, using local data")"""

if old_pull_block not in content:
    print("❌ Could not find _do_pull block to replace")
else:
    content = content.replace(old_pull_block, new_pull_block, 1)
    print("✅ _do_pull fix applied")

import py_compile
try:
    py_compile.compile("/Users/slowhands/Developer/clavus/clavus/tui.py", doraise=True)
    print("Syntax OK")
except py_compile.PyCompileError as e:
    print(f"Syntax error: {e}")