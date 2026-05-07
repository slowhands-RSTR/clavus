# Clavus UX Cleanup — Two-Collaborator Flow

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Two musicians install Clavus, share a project, and start collaborating in under 2 minutes — no CLI arcana, no manual relay management, no "samples offline" confusion.

**Architecture:** A single `clavus setup` command handles first-run config. `clavus share` + `clavus join` handle everything else — relay lifecycle, discovery fallback (mDNS → Tailscale → direct URL), project pull, sample materialization with progress, and auto-opening Ableton. The TUI stays for power users but isn't required for basic collab.

**Tech Stack:** Python 3.10+, httpx, fastapi/uvicorn, zeroconf, Textual (TUI)

---

## Phase 1: First-Run Experience

### Task 1: Add `clavus setup` — single-command onboarding

**Objective:** First-run config in one step: author name, tailnet detection, relay port check.

**Files:**
- Modify: `clavus/cli.py:186` (near `cmd_doctor`)
- Modify: `clavus/config.py`

**Step 1: Add setup command to CLI**

In `clavus/cli.py`, add after `cmd_doctor`:

```python
def cmd_setup(args: argparse.Namespace) -> None:
    """Guided first-run setup — author, port, discovery check."""
    from clavus.config import ClavusConfig, CONFIG_PATH
    from clavus.store import BlobStore
    import socket, subprocess, platform

    print("🎹 Clavus Setup")
    print("───")
    print()

    cfg = ClavusConfig.load()

    # 1. Author name
    current_author = cfg.author or os.environ.get("USER") or os.environ.get("USERNAME") or ""
    print(f"👤 Author name [{current_author}]: ", end="")
    author = input().strip() or current_author
    cfg.set("author", author)

    # 2. Port check
    port = cfg.port or 7890
    print(f"🔌 Relay port [{port}]: ", end="")
    port_input = input().strip()
    if port_input:
        try:
            port = int(port_input)
        except ValueError:
            print(f"   ⚠️ Invalid port, using {port}")
    cfg.set("port", port)

    # Check if port is available
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    in_use = sock.connect_ex(("127.0.0.1", port)) == 0
    sock.close()
    if in_use:
        print(f"   ⚠️ Port {port} is in use. Choose another port with: clavus config set port <N>")

    # 3. Tailscale check
    print()
    print("🌐 Network discovery...")
    ts_installed = False
    try:
        result = subprocess.run(["tailscale", "version"], capture_output=True, text=True, timeout=5)
        ts_installed = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    if ts_installed:
        print("   ✅ Tailscale found — remote collab available")
        try:
            result = subprocess.run(["tailscale", "ip", "-4"], capture_output=True, text=True, timeout=5)
            ts_ip = result.stdout.strip()
            if ts_ip:
                print(f"   📡 Tailscale IP: {ts_ip}")
                cfg.set("tailscale_ip", ts_ip)
        except Exception:
            pass
    else:
        print("   ℹ️  Tailscale not found — LAN-only collab (same WiFi)")
        print("   Install Tailscale for remote collab: https://tailscale.com/download")

    # 4. Check for Ableton Live
    ableton_path = None
    if platform.system() == "Darwin":
        ableton_path = "/Applications/Ableton Live 12 Suite.app"
    elif platform.system() == "Windows":
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Ableton\Live 12")
            ableton_path = winreg.QueryValueEx(key, "InstallDir")[0]
        except Exception:
            pass

    if ableton_path and os.path.exists(ableton_path):
        print(f"   ✅ Ableton Live found at {ableton_path}")
        cfg.set("ableton_path", ableton_path)
    else:
        print("   ℹ️  Ableton Live not auto-detected")
        print(f"   Set manually: clavus config set ableton_path \"/path/to/Ableton\"")

    # 5. Save
    cfg.save()
    print()
    print("✅ Setup complete!")
    print()
    print("   Next steps:")
    print("     clavus init         — start tracking an Ableton project")
    print("     clavus share        — share with a collaborator")
    print("     clavus tui          — terminal dashboard")

    # Also ensure config dir exists
    store = BlobStore()
    print(f"   Data: {store.root}")
```

**Step 2: Register command in argparser**

In `main()`, add after doctor setup:
```python
subparsers.add_parser("setup", help="Guided first-run setup")
```
And in the dispatch dict:
```python
"setup": cmd_setup,
```

### Task 2: Auto-detect Ableton project on `clavus init`

**Objective:** When user runs `clavus init` without a path, scan Desktop/Documents for .als files and offer a picker.

**Files:**
- Modify: `clavus/cli.py:255` (cmd_init)

Replace the current `cmd_init` path handling:

```python
def cmd_init(args: argparse.Namespace) -> None:
    # ... existing imports ...

    if not args.path:
        # Auto-detect: scan Desktop, Documents, common locations for .als files
        from clavus.helpers import get_desktop_path
        search_dirs = [
            get_desktop_path(),
            Path.home() / "Documents",
            Path.home() / "Music" / "Ableton",
            Path.home() / "Ableton",
        ]
        als_files = []
        for d in search_dirs:
            if d.exists():
                for f in d.rglob("*.als"):
                    # Skip backup/project cache
                    if "Backup" not in str(f) and "Ableton Project Info" not in str(f):
                        als_files.append(f)

        if not als_files:
            print("❌ No .als files found on Desktop or in Documents/Music.")
            print("   Usage: clavus init /path/to/project.als")
            sys.exit(1)

        if len(als_files) == 1:
            args.path = str(als_files[0])
            print(f"📁 Found: {als_files[0].name}")
        else:
            print("📁 Found multiple .als files:")
            for i, f in enumerate(als_files[:20], 1):
                print(f"  {i}. {f.name}  ({f.parent})")
            print()
            print("  Enter number (or 0 to skip): ", end="")
            try:
                choice = int(input().strip())
                if 1 <= choice <= len(als_files):
                    args.path = str(als_files[choice - 1])
                else:
                    print("❌ No project selected.")
                    sys.exit(1)
            except (ValueError, EOFError):
                print("❌ No project selected.")
                sys.exit(1)

    # ... rest of existing cmd_init ...
```

---

## Phase 2: Pull UX

### Task 3: Progress indicators during pull

**Objective:** Show per-file progress when downloading samples, not just "1 snapshots" at the end.

**Files:**
- Modify: `clavus/sync.py:400-500` (pull_from_remote)

In `pull_from_remote`, wrap the sample download loop:

```python
# Download missing audio samples
total_samples = len(missing_samples)
if total_samples:
    print(f"   🎵 Downloading {total_samples} audio samples...")
    downloaded_samples = 0
    for h in list(missing_samples):
        if h in downloaded:
            continue
        try:
            r = client.client.get(
                f"{remote.url}/api/blobs/{h}",
                timeout=120,
            )
            if r.status_code == 200:
                store.put_object(r.content, h)
                downloaded_samples += 1
                count += 1
                downloaded.add(h)
                # Progress bar
                if total_samples > 1:
                    pct = downloaded_samples / total_samples
                    bar = "█" * int(pct * 20) + "░" * (20 - int(pct * 20))
                    size_mb = len(r.content) / (1024 * 1024)
                    print(f"\r   [{bar}] {downloaded_samples}/{total_samples} ({size_mb:.1f} MB)", end="")
        except Exception:
            pass
    if total_samples > 1:
        print()  # newline after progress bar
```

### Task 4: Post-pull summary

**Objective:** After pull completes, show what was received: snapshots, cues, samples, project folder.

**Files:**
- Modify: `clavus/sync.py:470-502` (materialize section)

Replace the silent materialize block:

```python
# Always materialize the latest snapshot to Desktop after any pull
try:
    head = proj.head
    if head:
        snap = store.load_snapshot(head)
        if snap and snap.als_hash:
            raw = store.get_object(snap.als_hash)
            if raw:
                project_name = proj.name.replace(" ", " ")
                project_dir = get_desktop_path() / f"{project_name} Project"
                out = project_dir / f"{project_name}.als"
                out.parent.mkdir(parents=True, exist_ok=True)

                # Materialize samples first
                samples_written = 0
                if snap.sample_hashes:
                    for sh in snap.sample_hashes:
                        fname = store.get_sample_filename(sh)
                        relpath = store.get_sample_relpath(sh) or ""
                        if fname and store.has_object(sh):
                            try:
                                store.materialize_sample(sh, out.parent, fname, relpath)
                                samples_written += 1
                            except Exception:
                                pass

                # Rewrite .als paths then write
                from clavus.parser import rewrite_als_sample_paths
                raw = rewrite_als_sample_paths(raw, out.parent)
                out.write_bytes(raw)

                # Summary
                print()
                print(f"   📁 {out.parent}")
                print(f"   ├── {project_name}.als")
                if samples_written:
                    print(f"   ├── Samples/ ({samples_written} files)")
                print(f"   └── Ready in Ableton")
                print()
                print(f"   💡 Tip: Run 'clavus open' to launch Ableton")
except Exception:
    pass
```

---

## Phase 3: Ableton Integration

### Task 5: Fix "samples offline" on first open

**Objective:** When Ableton opens a project from a new location, it shows samples as offline until you manually point it at one — then all resolve. Bypass this by launching Ableton with the project file passed as an argument, which forces it to resolve relative paths immediately.

**Files:**
- Modify: `clavus/cli.py:1958` (cmd_open)

**Investigation:** Test if launching Ableton with `open -a "Ableton Live 12 Suite" "/path/to/project.als"` on macOS, or `start "" "Ableton Live 12 Suite.exe" "C:\path\to\project.als"` on Windows, resolves samples automatically (vs opening Ableton first then loading the project).

If the direct-open approach works, update `cmd_open` to always pass the .als as an argument. If it doesn't, add a post-open instruction:

```python
# After launching Ableton:
print("   💡 If samples show as offline, click any missing sample →")
print("      Ableton will resolve all samples automatically.")
```

---

## Phase 4: Relay Lifecycle

### Task 6: `clavus share` auto-restarts relay on port conflict

**Objective:** If port 7890 is in use (stale relay), kill it and restart — don't make user do it manually.

**Files:**
- Modify: `clavus/cli.py:709` (cmd_share)

```python
def cmd_share(args: argparse.Namespace) -> None:
    # ... existing imports ...
    
    cfg = ClavusConfig.load()
    host = args.host or cfg.host
    port = args.port or cfg.port
    
    # Check if port is in use by another process (not us)
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if sock.connect_ex(("127.0.0.1", port)) == 0:
        # Port is in use — try to kill the old relay
        print(f"   ⚠️ Port {port} is in use. Checking if it's a Clavus relay...")
        try:
            import httpx
            r = httpx.get(f"http://127.0.0.1:{port}/api/health", timeout=2)
            if r.status_code == 200 and r.json().get("service") == "clavus":
                print(f"   🔄 Restarting existing Clavus relay on port {port}...")
                import subprocess, signal
                # Find and kill the process
                if platform.system() == "Darwin" or platform.system() == "Linux":
                    result = subprocess.run(
                        ["lsof", "-ti", f":{port}"], capture_output=True, text=True
                    )
                    for pid in result.stdout.strip().split("\n"):
                        if pid:
                            try:
                                os.kill(int(pid), signal.SIGTERM)
                            except Exception:
                                pass
                import time
                time.sleep(1)
        except Exception:
            print(f"   ❌ Port {port} is in use by another application.")
            print(f"   Use: clavus share --port <N>")
            sys.exit(1)
    
    # ... rest of existing share code ...
```

### Task 7: `clavus join` tries direct URL as last-resort fallback

**Objective:** When mDNS and Tailscale discovery both fail, prompt user to paste a direct URL instead of failing silently.

**Files:**
- Modify: `clavus/cli.py:779` (cmd_join)

At the end of the auto-discovery path (where no sessions are found):

```python
# No sessions found via discovery
print("   ❌ No Clavus sessions found via LAN or Tailscale.")
print()
print("   Options:")
print("   1. Ask your collaborator for their share URL")
print("   2. Or they can share their Tailscale IP directly")
print()
print("   Paste URL (e.g. http://100.127.1.109:7890): ", end="")
try:
    url = input().strip()
    if url:
        if not url.startswith("http"):
            url = f"http://{url}"
        args.code = url
        # Recurse into direct URL join path
        return cmd_join(args)
except (EOFError, KeyboardInterrupt):
    pass
sys.exit(1)
```

---

## Phase 5: Polish

### Task 8: Reduce visible commands for new users

**Objective:** `clavus --help` shows too much. Group commands into "Common" and "Advanced" sections. First-timers see 6 commands, not 45.

**Files:**
- Modify: `clavus/cli.py:2400+` (main/argparse setup)

Create a custom help formatter:

```python
class ClavusHelpFormatter(argparse.HelpFormatter):
    def __init__(self, prog):
        super().__init__(prog, max_help_position=30, width=100)

# Then in main(), organize subparsers into groups:
common = ["setup", "init", "share", "join", "push", "pull", "open", "tui", "log", "cue", "cues"]
# Everything else is advanced

# When printing help, show common first with a header, then "Advanced Commands" section
```

### Task 9: Add `clavus version` and `clavus doctor` to setup output

**Objective:** Mention these at the end of `clavus setup` so users have troubleshooting tools.

Already partially done — just add to the "Next steps" output in Task 1.

---

## Execution Order

1. Task 1 + 2: First-run onboarding
2. Task 3 + 4: Pull UX improvements  
3. Task 5: Ableton open fix (investigate + implement)
4. Task 6 + 7: Relay lifecycle improvements
5. Task 8 + 9: Help text + polish

**Verification:** After each phase, test end-to-end: `clavus setup` → `clavus share` → `clavus join` → `clavus open` → samples load in Ableton.
