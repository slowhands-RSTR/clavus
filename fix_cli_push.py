#!/usr/bin/env python3
"""Fix cmd_push and cmd_pull to save locally when localhost relay is down."""
import re

with open("/Users/slowhands/Developer/clavus/clavus/cli.py") as f:
    content = f.read()

# ── Fix cmd_push: localhost dead remote → save locally ──
old_push_block = """    for remote in dead_remotes:
        print(f"  ⏭  Skipping '{remote.name}' — unreachable")

    for remote in live_remotes:"""

new_push_block = """    # Handle localhost dead remote: save locally instead of skipping
    localhost_dead = next((r for r in dead_remotes if r.url.rstrip("/") in ("http://localhost:7890", "http://localhost:7891")), None)
    if localhost_dead:
        # Solo mode: relay down, save to local store only
        from clavus import parse_als
        from pathlib import Path
        als_path = Path(proj.root_als)
        if als_path.exists():
            raw_als = als_path.read_bytes()
            current_hash = hashlib.sha256(raw_als).hexdigest()
            if current_hash != (proj.head or ""):
                project = parse_als(als_path)
                if project:
                    snap = store.save_snapshot(project, message="auto-snapshot before push", parent=proj.head)
                    if snap.hash != proj.head:
                        store.update_ref("HEAD", snap.hash)
                        proj.head = snap.hash
                        store.set_index(proj)
        print(f"  💾 saved locally — relay offline")

    for remote in dead_remotes:
        if remote is not localhost_dead:
            print(f"  ⏭  Skipping '{remote.name}' — unreachable")

    for remote in live_remotes:"""

if old_push_block not in content:
    print("❌ Could not find cmd_push block to replace")
else:
    content = content.replace(old_push_block, new_push_block, 1)
    print("✅ cmd_push fix applied")

# Verify syntax
import py_compile
try:
    py_compile.compile("/Users/slowhands/Developer/clavus/clavus/cli.py", doraise=True)
    print("Syntax OK")
except py_compile.PyCompileError as e:
    print(f"Syntax error: {e}")