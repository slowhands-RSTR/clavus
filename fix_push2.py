#!/usr/bin/env python3
"""Fix _do_push: for localhost remote, check relay live right before push."""
with open("/Users/slowhands/Developer/clavus/clavus/tui.py") as f:
    content = f.read()

old_block = """            # Solo host mode: localhost remote with relay down — save locally only
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

new_block = """            # Solo host mode: for localhost remote, check relay live right before push
            relay_live = False
            if is_localhost:
                try:
                    import urllib.request
                    r = urllib.request.urlopen(f"{remote.url.rstrip('/')}/api/ping", timeout=2)
                    relay_live = (r.status == 200)
                except Exception:
                    pass
                if not relay_live:
                    # Relay not running — save locally only
                    self._sync_status = f"💾 {time.strftime('%H:%M')} local"
                    self._update_header()
                    await asyncio.sleep(0)
                    self._status("💾 saved locally — relay offline")
                    self._log_event("solo push: saved locally, relay not running")
                    return

            self._sync_status = f"⬆ {time.strftime('%H:%M')} {remote.name}..."
            self._update_header()
            await asyncio.sleep(0)
            self._status(f"⬆ {'force-' if force else ''}pushing to {remote.name}...")"""

if old_block not in content:
    print("❌ Could not find old block")
else:
    content = content.replace(old_block, new_block, 1)
    with open("/Users/slowhands/Developer/clavus/clavus/tui.py", "w") as f:
        f.write(content)
    print("✅ Fix applied")

import py_compile
try:
    py_compile.compile("/Users/slowhands/Developer/clavus/clavus/tui.py", doraise=True)
    print("Syntax OK")
except py_compile.PyCompileError as e:
    print(f"Syntax error: {e}")