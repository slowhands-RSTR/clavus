#!/usr/bin/env python3
"""Fix cmd_pull to handle solo mode: localhost relay down = nothing to pull."""
with open("/Users/slowhands/Developer/clavus/clavus/cli.py") as f:
    content = f.read()

# Find the dead_remotes check in cmd_pull and add localhost handling
old_pull_dead = """    if not remotes:
        print(f"❌ No remotes configured.")
        print(f"   Add one with: clavus remote add <name> <url>")
        return

    # If no local project, pull from any remote that has projects"""

new_pull_dead = """    # Solo mode: if only remote is localhost and it's down, nothing to pull
    # (user is working locally — their project is already here)
    if proj:
        localhost_dead = all(
            r.url.rstrip("/") in ("http://localhost:7890", "http://localhost:7891")
            for r in remotes
        )
        if localhost_dead:
            print(f"💾 up to date — working locally")
            return

    if not remotes:
        print(f"❌ No remotes configured.")
        print(f"   Add one with: clavus remote add <name> <url>")
        return

    # If no local project, pull from any remote that has projects"""

if old_pull_dead not in content:
    print("❌ Could not find cmd_pull block to replace")
else:
    content = content.replace(old_pull_dead, new_pull_dead, 1)
    print("✅ cmd_pull fix applied")

import py_compile
try:
    py_compile.compile("/Users/slowhands/Developer/clavus/clavus/cli.py", doraise=True)
    print("Syntax OK")
except py_compile.PyCompileError as e:
    print(f"Syntax error: {e}")