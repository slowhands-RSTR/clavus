# Clavus Build Plan — Current State & What's Next

## Current Files

```
clavus/
├── __init__.py      # Format auto-detection (Ableton 10+ vs 9)
├── __main__.py      # CLI entry
├── cli.py           # CLI commands
├── cues.py          # Cue CRUD + marker injection (Live 10/11/12)
├── git_integration.py  # Git-aware branch/merge
├── helpers.py       # Shared utilities
├── parser.py        # .als XML parser
├── store.py         # BlobStore, Snapshot, diff engine
├── sync.py          # Peer-to-peer sync daemon
├── tui.py           # Textual TUI
├── watch.py         # File watcher daemon
└── web.py           # FastAPI server + WebSocket

hotkeys/
├── bindings.json        # Shared key mappings (single source of truth)
├── hammerspoon.lua      # macOS hotkey config
├── autohotkey.ahk       # Windows hotkey script
└── README.md            # Setup guide for both platforms
```

## Phase Status

| Phase | What | Status |
|-------|------|--------|
| 1 | .als parser + project model | ✅ Done |
| 2 | Blob storage + snapshots + diff | ✅ Done |
| 3 | CLI — init, snapshot, log, diff, status | ✅ Done |
| 4 | Cue system (CRUD, threaded replies, marker render) | ✅ Done |
| 5 | File watcher daemon + cue injection | ✅ Done |
| 6a | FastAPI web companion dashboard | ✅ Done |
| 6b | Sync endpoints (pull/push) | ✅ Done |
| 6c | Peer-to-peer sync daemon (sync.py) | ✅ Done |
| 6d | TUI — navigation, cue management, CRUD | ✅ Done |
| 6e | TUI — WebSocket real-time sync | ✅ Done |
| 6f | TUI — auto-reconnect + scroll preservation | ✅ Done |
| 6g | TUI — push format fix, cues model cleanup | ✅ Done |
| 6h | TUI — two-step cue input (text then position) | ✅ Done |
| 6i | TUI — :name, :projects, :init, :browse commands | ✅ Done |
| 6j | Live 12 marker support (Locators format) | ✅ Done |
| 7 | Git integration (branch/merge CLI) | ✅ Done |
| 8 | **Keyboard automation** — Hammerspoon (macOS) + AutoHotkey (Windows) | ✅ Done |
| 9 | P2P file/media transfer (audio stems over Tailscale/LAN) | ❌ Planned |
| 10 | Snapshot restore (`clavus restore <hash>`) | ❌ Not started |
| 11 | .als diff visualization in TUI | ❌ Not started |
| 12 | Tailscale + relay transport for sync | ❌ Planned |

## What Actually Needs Work

### 1. P2P File/Media Transfer (Phase 9 — NEXT)
File sharing between collaborators — stems, recordings, project files. See design doc in `./hotkeys/README.md` for the concept. Needs:
- `clavus share <file>` — register file in blob store, make available via HTTP
- `clavus pull-media` — fetch missing files from peer
- Attachment support in cues (attach audio to a cue)
- Resumable transfers via HTTP Range headers
- Content-addressed dedup

### 2. Snapshot restore (`clavus restore <hash>`)
- `cmd_snapshot` already parses `.als` — add step to save raw `.als` bytes to `~/.clavus/objects/<hash>.als`
- New `cmd_restore` — takes hash, loads stored `.als`, warns before overwriting current project
- `clavus log` should flag snapshots that have a full `.als` backup
- TUI `:restore <hash>` command
- ~1 day of focused work

### 3. Keyboard Automation — Next Steps
Hammerspoon config is in place and symlinked. To activate:
1. Open Hammerspoon from Applications
2. Grant Accessibility permissions when prompted
3. Click menu bar icon → Reload Config
4. Verify ♮ icon appears and 8 hotkeys are registered
5. Start `clavus serve` (or `clavus web --port 7890`)
6. Press ⌘⌥L to test

Future: Live playhead integration via MIDI/OSC for auto-positioning.

### 4. Test the full real-time flow
End-to-end tested ✅ — TUI connects, pulls, pushes. Live 12 locator injection verified.

### 5. TUI polish for jam sessions
- Status bar cue count
- Snapshot confirmation
- Better error messages on connection loss
