# Clavus

> *Latin: keel, nail, rudder — the thing that steers and holds together.*

**Git for Ableton Live.** Snapshot, diff, sync, and comment on Ableton Live projects. Work with collaborators over Tailscale or LAN. No cloud dependency.

## Features

- **Timeline-anchored cues** — add comments at any position (`@1:23`), reply in threads, resolve/skip/defer
- **Snapshot engine** — git-style content-addressed snapshots of .als state with diffs
- **Stem sync** — content-addressed audio file sharing between collaborators (dedup'd by SHA256)
- **File watcher** — auto-snapshot on .als changes (polling-based, pure Python, no extra deps)
- **Cue injection** — write unresolved cues as Ableton markers directly into the .als
- **Web companion** — FastAPI dashboard for cue management, project history, and stem transfer
- **Terminal UI** — Textual TUI for keyboard-first cue management
- **Keyboard automation** — Hammerspoon hotkeys (macOS) and AutoHotkey (Windows)
- **P2P sync** — push/pull cues and stems over Tailscale or LAN
- **Collaborators** — assign cues, track in-progress work, threaded replies

## Quick Start

```bash
# Install
pip install clavus

# Initialize a project from an Ableton .als file
clavus init ~/Projects/My\ Song/My\ Song.als

# Tag the current state with a message
clavus snapshot "initial arrangement"

# Add a timeline comment
clavus cue "bridge feels long, try 4 bars" @2:00

# View all cues
clavus cues

# Start the web dashboard
clavus serve
# → Open http://localhost:7890

# Or launch the terminal dashboard
clavus tui
```

## Commands

| Command | Description |
|---------|-------------|
| `init <path>` | Register an .als project |
| `snapshot <message>` | Save current project state |
| `log` | Snapshot history |
| `diff [hash]` | What changed between snapshots |
| `status` | Current project state |
| `cue <text> @pos` | Add a timeline comment |
| `cue-reply <id> <text>` | Reply to a cue thread |
| `cue-assign <id> <name>` | Assign a cue to someone |
| `cue-start <id>` | Mark as in-progress |
| `cue-stop <id>` | Stop working on a cue |
| `cue-delete <id>` | Permanently delete a cue |
| `cue-archive [id]` | Archive resolved/skipped cues |
| `cues` | List all cues |
| `cue-render [--inject]` | Write cues as Ableton markers |
| `watch` | Auto-snapshot on file changes |
| `serve` | Start web companion |
| `tui` | Launch terminal dashboard |
| `push` | Sync cues to remotes |
| `pull` | Fetch cues from remotes |
| `stem import <file> --track <name>` | Import a stem |
| `stem push` / `stem pull` | Sync stems with collaborators |
| `config` | View/edit settings |
| `branch` / `checkout` / `merge` | Branch management |

## Terminal UI

```
~▼~ clavus  Northern Lights                      ⬤ connected  12 cues

  ● @1.1.1  bridge feels long, try 4 bars  @chris        abcdef01
  ├─ chris  14:03  tried 8 bars, better but still off
  ╰─ steven 14:05  let me check the reference track
  
  ✓ @4.1.1  second drop needs more sub              12345678
  
  ● @6.1.1  bass sidechain too aggressive  ▶         9abcdef0
  
  – @9.1.1  hi-hat pattern at 48 bars            aabbccdd

  History
  ───────
  a1b2c3d4  05/03 13:22
  arrangement pass 2                

  ef123456  05/03 12:15
  arrangement pass 1                

r reply  R resolve  e edit  c cue  s skip  a assign  S start  x archive  p pull  P push  q quit  : cmd
```

**Keybindings:** `j`/`k` navigate, `r` reply, `R` resolve, `a` assign, `S` start/stop, `x` archive, `c` new cue, `:` command mode.

## Configuration

```bash
# View all settings
clavus config

# Set your author name
clavus config author "Your Name"

# Change the server port
clavus config port 7890
```

Config file: `~/.config/clavus/config.json`
Environment overrides: `CLAVUS_AUTHOR`, `CLAVUS_PORT`, `CLAVUS_HOST`, `CLAVUS_SERVER`
CLI flags (`--port`, `--host`, `--connect`) override everything.

## Hotkeys (macOS)

1. Install [Hammerspoon](https://www.hammerspoon.org/)
2. Symlink the config: `ln -sf ~/Developer/clavus/hotkeys/hammerspoon.lua ~/.hammerspoon/init.lua`
3. Relaunch Hammerspoon

**Ctrl+Shift+F** — New cue (dialog prompt)
**Ctrl+Shift+G** — List pending cues
**Ctrl+Shift+J** — Inject markers into .als
**Ctrl+Shift+H** — Help

## Hotkeys (Windows)

1. Install [AutoHotkey v2](https://www.autohotkey.com/)
2. Run `hotkeys/autohotkey.ahk`

## Architecture

```
clavus/
├── clavus/
│   ├── __init__.py    # .als parser (Live 9 + 10+ auto-detect)
│   ├── parser.py      # XML parsing, track/device/marker extraction
│   ├── store.py       # BlobStore, Snapshot, diff, stem sync
│   ├── cues.py        # Timeline-anchored comments CRUD
│   ├── config.py      # User configuration (file/env/CLI)
│   ├── cli.py         # CLI entry point + command dispatch
│   ├── web.py         # FastAPI web companion + sync endpoints
│   ├── tui.py         # Textual terminal UI
│   ├── sync.py        # P2P remote sync
│   ├── watch.py       # File watcher daemon (polling)
│   └── helpers.py     # Shared utilities
├── hotkeys/
│   ├── hammerspoon.lua    # macOS hotkeys
│   ├── autohotkey.ahk     # Windows hotkeys
│   └── bindings.json      # Shared key mapping definitions
└── pyproject.toml
```

## Requirements

- Python 3.10+
- Ableton Live 9, 10, 11, or 12 (.als files)
- Optional: Hammerspoon (macOS) or AutoHotkey (Windows) for hotkeys

## Development

```bash
git clone https://github.com/slowhands/clavus
cd clavus
pip install -e .
python3 fixtures/gen_fixture.py  # Generate test .als
python3 test_parser.py           # Run a test suite
python3 test_cues.py
python3 test_cli_full.py         # Full CLI workflow
```

## License

MIT
