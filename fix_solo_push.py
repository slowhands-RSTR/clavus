#!/usr/bin/env python3
with open("/Users/slowhands/Developer/clavus/clavus/tui.py") as f:
    content = f.read()

old_block = """            # Allow localhost (solo host mode) to work without relay
            is_localhost = remote.url.startswith("http://localhost")
            if not self._peer_reachable and not is_localhost:
                self._sync_status = ""
                self._update_header()
                await asyncio.sleep(0)
                self._status("⚠️ relay unreachable — is 'clavus share' running?")
                self._log_event("push blocked: relay not reachable — run 'clavus share' first")
                return
            # Auto-snapshot local changes before pushing (conflict resolution, cue edits, etc.)
            # This ensures HEAD matches what we're about to send.
            try:
                als_path = Path(proj_index.root_als)
                if als_path.exists():
                    raw_als = als_path.read_bytes()
                    current_hash = hashlib.sha256(raw_als).hexdigest()
                    if current_hash != (proj_index.head or ""):
                        from clavus import parse_als
                        project = parse_als(als_path)
                        if project:
                            snap = self.store.save_snapshot(
                                project,
                                message="auto-snapshot before push",
                                parent=proj_index.head,
                            )
                            if snap.hash != proj_index.head:
                                self.store.update_ref("HEAD", snap.hash)
                                proj_index.head = snap.hash
                                self.store.set_index(proj_index)
                                self._log_event(f"● auto-snapshot {snap.hash[:8]} (local changes saved)")
            except Exception:
                pass  # best-effort — don't block push on snapshot failure
            self._sync_status = f"⬆ {time.strftime('%H:%M')} {remote.name}..."
            self._update_header()
            await asyncio.sleep(0)
            self._status(f"⬆ {'force-' if force else ''}pushing to {remote.name}...")"""

new_block = """            # Allow localhost (solo host mode) to work without relay
            is_localhost = remote.url.startswith("http://localhost")
            if not self._peer_reachable and not is_localhost:
                self._sync_status = ""
                self._update_header()
                await asyncio.sleep(0)
                self._status("⚠️ relay unreachable — is 'clavus share' running?")
                self._log_event("push blocked: relay not reachable — run 'clavus share' first")
                return
            # Auto-snapshot local changes before pushing (conflict resolution, cue edits, etc.)
            # This ensures HEAD matches what we're about to send.
            try:
                als_path = Path(proj_index.root_als)
                if als_path.exists():
                    raw_als = als_path.read_bytes()
                    current_hash = hashlib.sha256(raw_als).hexdigest()
                    if current_hash != (proj_index.head or ""):
                        from clavus import parse_als
                        project = parse_als(als_path)
                        if project:
                            snap = self.store.save_snapshot(
                                project,
                                message="auto-snapshot before push",
                                parent=proj_index.head,
                            )
                            if snap.hash != proj_index.head:
                                self.store.update_ref("HEAD", snap.hash)
                                proj_index.head = snap.hash
                                self.store.set_index(proj_index)
                                self._log_event(f"● auto-snapshot {snap.hash[:8]} (local changes saved)")
            except Exception:
                pass  # best-effort — don't block push on snapshot failure

            # Solo host mode: localhost remote with relay down — save locally only
            if is_localhost and not self._peer_reachable:
                self._sync_status = f"💾 {time.strftime('%H:%M')} local"
                self._update_header()
                await asyncio.sleep(0)
                self._status("💾 saved locally — relay offline, no remote sync needed")
                self._log_event("solo push: saved locally, relay not running")
                return

            self._sync_status = f"⬆ {time.strftime('%H:%M')} {remote.name}..."
            self._update_header()
            await asyncio.sleep(0)
            self._status(f"⬆ {'force-' if force else ''}pushing to {remote.name}...")"""

if old_block not in content:
    print("❌ Could not find old block in _do_push")
else:
    content = content.replace(old_block, new_block, 1)
    with open("/Users/slowhands/Developer/clavus/clavus/tui.py", "w") as f:
        f.write(content)
    print("✅ _do_push solo mode fix applied")

# Verify syntax
import py_compile
try:
    py_compile.compile("/Users/slowhands/Developer/clavus/clavus/tui.py", doraise=True)
    print("Syntax OK")
except py_compile.PyCompileError as e:
    print(f"Syntax error: {e}")