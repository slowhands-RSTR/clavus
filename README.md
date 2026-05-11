# Clavus — Ableton Live Project Collaboration

**Version:** 0.8.0-beta  **Platforms:** macOS · Windows · Linux

Clavus snapshots, syncs, and helps you collaborate on Ableton Live projects. Think of it as Git for your `.als` files — threaded comments pinned to timeline positions, push/pull sync over Tailscale, and a keyboard-driven terminal dashboard. No cloud, no plugins, no accounts.

## Quick Start

```bash
# Install
git clone https://github.com/castle-queenside/clavus
cd clavus
pip install -e .            # macOS / Linux
# Windows: py -m pip install -e .

# First-time setup (guided wizard)
clavus setup

# Open the dashboard
clavus tui
```

## How It Works

**Two paths — pick yours:**

### Solo (no relay needed)
Just you, your `.als`, and the TUI. Snapshots, cues, diffs, and restores all work locally. Great for version control and leaving yourself notes.

### Collaborating (one person hosts, everyone else joins)

```
┌─────────┐                    ┌───────────────┐                    ┌─────────┐
│   You   │ ◄── push/pull ───► │     Relay     │ ◄── push/pull ───► │  Peer   │
│  (Mac)  │   via Tailscale    │(any machine)  │   via Tailscale    │  (Win)  │
└─────────┘                    └───────────────┘                    └─────────┘
```

Clavus uses **Tailscale** for the private network between machines. The relay machine runs `clavus share` plus a `tailscale serve` proxy — everyone else joins via a MagicDNS URL.

**⚠️ Important: Tailscale doesn't automatically let shared users reach your machine.**

When a collaborator is on a *different Tailscale account*, you must:
1. **Share your node** from the [Tailscale admin console](https://login.tailscale.com/admin/machines) — click "Share" next to your machine, enter their email
2. **They must accept** the invite (email + Tailscale app)
3. **Use the MagicDNS URL, never the raw IP** — raw Tailscale IPs (like `100.x.x.x`) only work for machines on the *same* account. Shared users get blocked by Tailscale ACLs on raw TCP

#### Setup (relay host — do this once)

```bash
# 1. Install Tailscale: https://tailscale.com/download
#    Verify: tailscale ip -4

# 2. Start the relay on port 7891 (so tailscale serve can use 7890)
clavus share --port 7891 &

# 3. Start the Tailscale HTTP proxy (magic step — raw IP won't work)
tailscale serve --bg --http 7890 http://localhost:7891

# 4. Verify
tailscale serve status
# → http://slow-hands-studio-1.tail46b8d9.ts.net:7890
curl http://slow-hands-studio-1.tail46b8d9.ts.net:7890/api/ping
# → {"status":"ok","app":"clavus-web","version":"0.2.0"}

# 5. Share your node from the admin console
#    https://login.tailscale.com/admin/machines → your machine → Share...
```

**After reboot,** re-run step 3 (`tailscale serve --bg ...`). The relay auto-starts with `clavus share`, but `tailscale serve` doesn't survive restarts.

#### Setup (everyone else — do this once)

```bash
# 1. Install Tailscale, accept the node-share invite

# 2. Clone + install Clavus (see Quick Start above)

# 3. Join the relay — use the MagicDNS URL the host gave you
clavus join http://<magicdns-url>:7890
# Example: clavus join http://slow-hands-studio-1.tail46b8d9.ts.net:7890

clavus pull
clavus tui
```

**❌ Do NOT use** `http://100.127.1.109:7890` (raw IP) or `http://localhost:7890`. These only work for the host machine itself. Shared users **must use the MagicDNS URL**.

#### Daily rhythm

**Relay host:**
1. `clavus share --port 7891 &` and `tailscale serve --bg --http 7890 http://localhost:7891` (if not already running)
2. `clavus tui` in a second terminal
3. Work in Ableton → `C` to snapshot → `P` to push

**Everyone else:**
1. `clavus tui` — open dashboard
2. `p` — pull latest
3. Work in Ableton → `C` to snapshot → `P` to push

#### How Tailscale networking actually works

| Connection | Same account? | Shared user? |
|-----------|:---:|:---:|
| Raw Tailscale IP (`100.x.x.x:7890`) | ✅ Works | ❌ **Blocked by ACLs** |
| MagicDNS (`machine-name.tailxxxx.ts.net:7890`) via `tailscale serve --http` | ✅ Works | ✅ **Works (HTTP serve auto-allows)** |

`tailscale serve --http` acts as a reverse proxy that handles ACLs for shared users. Without it, shared users can ping your machine but can't open TCP connections to your ports. This is by design — Tailscale defaults to deny for cross-account traffic.

For full details: `references/tailscale-serve-relay.md` in the repo.

## Why It's Safe

Clavus is built to protect your work, not destroy it.

- **Optimistic locking** — if someone else pushes while you're working, your push is rejected with a "pull first" warning. You'll never silently overwrite someone's changes.
- **Auto-snapshot before pull** — the TUI snapshots your local changes before pulling from the relay, so nothing is ever lost.
- **Atomic push ordering** — snapshots land first, then cues. If snapshots fail (network drop, conflict), nothing touches the relay. No half-baked state.
- **Freeze detection** — frozen tracks crash Ableton on other platforms. Clavus warns you before snapshotting frozen tracks, so you don't accidentally ship a project that wrecks your collaborator's session.
- **Index backup & recovery** — your project index is backed up before every write (rotating `.bak`, `.bak2`, `.bak3`). A full store backup is created daily. If the index corrupts, Clavus auto-restores from backup.
- **Network retry** — transient failures (timeouts, connection resets) are retried up to 3 times with backoff. Only actual errors get through.

## Collaborator Onboarding

Send this to anyone joining your project:

**1. Install prerequisites**
```bash
# Python 3.10+
winget install Python.Python.3.13      # Windows
brew install python@3.13               # macOS
```

**2. Install Tailscale**
- Download from https://tailscale.com/download
- The host will share their machine with you — accept the invite

**3. Install Clavus + join**
```bash
git clone https://github.com/castle-queenside/clavus
cd clavus
pip install -e .            # macOS / Linux
py -m pip install -e .      # Windows (if pip isn't on PATH)
clavus setup

# Join the relay — use the MagicDNS URL the host gave you
# ❌ Do NOT use the raw Tailscale IP (100.x.x.x) — that only works
#    for same-account machines. Shared users MUST use the MagicDNS URL.
clavus join http://<magicdns-url>:7890
# Example: clavus join http://slow-hands-studio-1.tail46b8d9.ts.net:7890

clavus pull
clavus tui
```

Projects land at `~/Clavus/Projects/` (macOS) or `C:\Users\<you>\Clavus\Projects\` (Windows).

**4. Share your node back** (so the host can reach you)
- https://login.tailscale.com/admin/machines → your machine → Share → host's email
- This makes your project folders accessible for stem transfer

See the **Collaborating** section above for full relay setup and daily workflow.

## Keybindings (TUI)

| Key | Action |
|-----|--------|
| `c` | New cue — comment at current timeline position |
| `C` | Snapshot — save a checkpoint of your project |
| `r` | Reply to a cue |
| `e` | Edit cue text |
| `a` | Assign a cue to someone |
| `R` | Resolve / unresolve |
| `x` | Archive a cue |
| `!` | Resolve sync conflict (⚠ cue) |
| `T` | Restore to a previous snapshot |
| `d` | Show diff of selected snapshot |
| `p` | Pull from remotes (auto-snapshots local changes first) |
| `P` | Push to remotes |
| `U` | Push stems (WAV files) to remotes |
| `Tab` | Switch between cues / history pane |
| `j` / `k` | Navigate up / down |
| `q` | Quit |
| `:` | Command mode (`:snapshot msg`, `:share`, `:join URL`, `:browse`, `:init path`, `:stem push/pull`, `:backup`, `:restore`, `:doctor`, etc.) |

## Stem Sync

Sync WAV files alongside your `.als` project. Stems are content-addressed — only changed files transfer.

```bash
# CLI
clavus stem import ~/Samples/kick.wav     # add a stem to the project
clavus stem list                           # see what's tracked
clavus stem push                           # push stems to the relay
clavus stem pull                           # pull stems from the relay

# TUI
U                                          # push stems
:stem pull                                 # pull stems
```

Stems land in `~/Clavus/Projects/<name>/Stems/` after pull. Ableton finds them automatically (macOS).

## Backup & Recovery

```bash
clavus backup                   # create a full store backup (tar.gz)
clavus backups                  # list available backups
clavus restore-store <file>     # restore from a backup
clavus repair                   # repair corrupted index (auto-restores from .bak files)
```

Clavus also creates rotating index backups automatically before every write, and a daily full-store backup. If `index.json` goes missing, it auto-restores from `.bak` → `.bak2` → `.bak3` on next run.

## FAQ

### I just installed. Now what?

`clavus setup` walks you through first-time config. After that:

- **Working solo?** `clavus init "My Track"` then `clavus tui` — snapshots, cues, and restores work great solo. No relay needed.
- **Joining a project?** Get the host's Tailscale IP, then `clavus join http://<ip>:7890` then `clavus pull`.

### Nothing shows up in the TUI. It says "no project."

You need to either initialize a project or pull from a remote:

- **From the TUI:** type `:init C:\path\to\project.als` (or `:browse` to find one)
- **From the TUI:** type `:join http://IP:PORT` then press `p` to pull
- **From CLI:** `clavus init /path/to/project.als` then `clavus tui`

If you've already pulled via CLI, just open the TUI — it picks up your last project.

### How do I add a project from inside the TUI?

Type `:browse` to navigate your filesystem. When you find the directory with your `.als` file, type `:init` to import it. The TUI runs the init in-process — no subprocess, no waiting. See the log entries appear right in the cue area.

You can also type `:init /full/path/to/project.als` directly if you know the path. No quotes needed around paths with spaces.

### The dot in the header is yellow (or dim).

- **Green ●** — connected and synced. You're good.
- **Yellow ○** — remote configured but no data pulled yet. Press `p`.
- **Dim ○** — no remote configured. Use `:join http://IP:PORT` to add one.

### I pressed `p` and nothing happened.

Check `:status` in the TUI. If it says "no remotes," you need to add one with `:join http://IP:PORT`. If the relay is unreachable, make sure Tailscale is connected and the host is running `clavus share`.

### My collaborator can't connect.

1. Host: run `clavus share` — it prints the exact URL
2. Host: verify Tailscale is connected: `tailscale status`
3. Collaborator: `clavus join http://<host-ip>:7890`
4. Collaborator: `clavus pull`

If the relay says "No projects found" after joining, that's fine — it means the relay is empty. Push your own projects with `clavus push` or `P` in the TUI. The remote is saved regardless.

If it still fails, check the relay is reachable:
```bash
curl http://<host-tailscale-ip>:7890/api/ping
# Should return: {"status":"ok"}
```

### How do I run the relay in the background?

On macOS/Linux, add `&` to run it in the background:
```bash
clavus share &
```
To stop it later: `pkill -f "clavus relay"`

On Windows, just keep the relay terminal open (minimized is fine). You don't need to look at it.

### I got "HEAD has moved — pull first" when pushing.

This is conflict protection. Someone else pushed while you were working. Just press `p` to pull their changes (your work is auto-snapshotted first), then push again. You won't lose anything.

### How do I resolve a sync conflict?

If both people edit the same cue, the TUI shows ⚠ on that cue. Press `!` to open the conflict resolution screen — pick your version or theirs. Push after resolving. The other side pulls and gets the resolved version automatically.

### What's the difference between archiving and deleting a cue?

- **Archive (`x`) — sync-safe.** The cue is hidden from your list but stays on the relay. Your collaborator still sees it. Status propagates on next push/pull. This is the intended workflow — mark things done without losing history.
- **Delete (`:delete`) — hidden, local-only.** Available as an escape hatch, but deleted cues come back on next pull (the relay still has them). Only use delete if you made a cue by mistake before ever pushing. Archive is almost always what you want.

### Clavus warned me about frozen tracks. What do I do?

Frozen tracks crash Ableton when opened on a different platform (e.g. Mac → Windows). Unfreeze those tracks in Ableton before snapshotting. If you're sure everyone's on the same OS, pass `--allow-frozen` to skip the warning.

### I'm on Windows and the TUI looks weird or blank.

Use **Windows Terminal** (install from the Microsoft Store). The old PowerShell/conhost terminal has rendering issues with Textual apps. Also, make sure you only have ONE remote configured — remove any localhost entry with `clavus remote remove relay http://localhost:7890`.

### I have two remotes both named "relay." Is that a problem?

Yes — the localhost one (`http://localhost:7890`) will fail on Windows because the relay runs on the Mac, not your machine. Remove it:
```bash
clavus remote remove relay http://localhost:7890
```

### Can I use this without a collaborator?

Absolutely. Clavus works great solo:
- **Snapshots** — version control for your `.als` file. Roll back to any checkpoint.
- **Cues** — leave yourself notes at specific timeline positions. Injects as Ableton markers.
- **Diffs** — see what changed between snapshots (tracks, devices, clips).
- **Backups** — rotating index backups and daily full-store archives.

### Where are my files?

Everything lives under `~/Clavus/` (macOS/Linux) or `C:\Users\<you>\Clavus\` (Windows):
- `Projects/` — your `.als` files organized by project (and `Stems/` folder per project)
- `store/` — snapshots, cue data, and sync metadata
- `backups/` — automatic daily backups and manual archive files

### How do I update Clavus?

```bash
cd clavus
git pull
pip install -e .
```

If you're running the relay, restart it afterward: `pkill -f "clavus relay" ; clavus share`

### Something's broken. How do I debug?

```bash
clavus doctor           # health check
clavus log              # recent activity
clavus repair           # fix corrupted index (restores from backup)
clavus backups          # list available store backups
:status                 # connection status (in TUI)
curl http://<relay-ip>:7890/api/ping   # relay reachability
```

## Features

- **Snapshot version control** — content-addressed snapshots with diffs (tracks, devices, clips, markers)
- **Cues** — threaded comments pinned to timeline positions, injected as Ableton markers
- **P2P sync** — push/pull over Tailscale via a shared relay
- **Optimistic locking** — 409 conflict protection prevents overwriting collaborators' work
- **Conflict detection & resolution** — ⚠ warns on concurrent cue edits, `!` to pick a winner
- **Stem sync** — content-addressed WAV file push/pull alongside snapshots
- **Sample path rewriting** — Ableton finds samples immediately after pull (macOS)
- **Snapshot restore** — roll back to any saved checkpoint
- **Auto-snapshot before pull** — never lose local changes
- **Freeze detection** — warns before snapshotting frozen tracks (cross-platform crash risk)
- **Index backup & recovery** — rotating `.bak` files, daily full-store archives, auto-restore
- **Atomic push ordering** — snapshots → cues; partial failure = clean stop, no half-state
- **Network retry** — automatic retry with backoff on transient failures
- **TUI dashboard** — keyboard-driven, Ableton-style dark theme
- **Auto-snapshot daemon** — file watcher for automatic checkpoints while you work

## Architecture

```
clavus/
├── clavus/
│   ├── parser.py         # .als XML parser
│   ├── store.py          # BlobStore, snapshots, diff engine, index backup/recovery
│   ├── cues.py           # Cue CRUD + Ableton marker injection + conflict detection
│   ├── config.py         # User config
│   ├── helpers.py        # Shared utilities
│   ├── watch.py          # File watcher daemon (auto-snapshot)
│   ├── sync.py           # P2P sync over HTTP (atomic push, retry, optimistic lock)
│   ├── web.py            # FastAPI relay server (per-project mutex, 409 protection)
│   ├── visual_diff.py    # Clip-level ASCII timeline diff
│   ├── tui.py            # Textual terminal dashboard
│   └── cli.py            # CLI entry point
├── pyproject.toml
```

## License

MIT
