# Clavus — Ableton Live Project Collaboration

**Version:** 0.2.0 (stable)

Clavus is a Git-for-Ableton collaboration tool. It parses `.als` files, snapshots project state, tracks threaded comments (cues) pinned to timeline positions, computes visual diffs between versions, and syncs everything over Tailscale or LAN — no cloud, no plugins, no hassle.

## Quick Start

```
pip install -e .
clavus serve          # start the web companion
clavus tui            # terminal dashboard (main interface)
```

## Features

- **Snapshot version control** — content-addressed snapshots of your `.als` project
- **Visual diffs** — see what changed between snapshots (tracks, clips, BPM, markers)
- **Cues** — threaded comments pinned to timeline positions (e.g. `@2:1.1 fix the kick`)
- **Stem sync** — content-addressed audio WAV transfer between peers
- **P2P sync** — pull/push over Tailscale or LAN, no server needed
- **TUI dashboard** — keyboard-driven terminal interface (main way to use it)
- **Web companion** — mobile-friendly browser view with Project/Cues/Snapshots tabs
- **Auto-snapshot** — file watcher daemon for automatic checkpoints

## Keybindings (TUI)

| Key | Action |
|-----|--------|
| `c` | New cue |
| `C` | Snapshot — save a checkpoint |
| `r` | Reply to a cue |
| `e` | Edit cue text |
| `a` | Assign a cue |
| `R` | Resolve/unresolve |
| `D` | Delete cue |
| `x` | Archive |
| `U` | Push stems |
| `T` | Restore to selected snapshot |
| `d` | Show diff of selected snapshot |
| `p` | Pull cues from remotes |
| `P` | Push cues to remotes |
| `Tab` | Switch between cues/history panes |
| `j` / `k` | Navigate up/down |
| `q` | Quit |
| `:` | Command mode (`:snapshot msg`, `:stem push`, etc.) |

## Setup for Collaborators

See [SETUP_STEVEN.md](SETUP_STEVEN.md) — step-by-step Windows setup guide.

**Collaborator needs:** Python 3.13+, Git, Tailscale, and `pip install -e .`

## Architecture

```
clavus/
├── clavus/
│   ├── parser.py         # .als XML parser
│   ├── store.py          # BlobStore, snapshots, diff engine
│   ├── visual_diff.py    # Clip-level side-by-side arrangement diff
│   ├── cues.py           # Cue CRUD + Ableton marker injection
│   ├── config.py         # User config
│   ├── helpers.py        # Shared utilities
│   ├── watch.py          # File watcher daemon
│   ├── sync.py           # P2P sync over HTTP
│   ├── discovery.py      # mDNS + Tailscale peer discovery
│   ├── web.py            # FastAPI web companion
│   ├── tui.py            # Textual terminal dashboard
│   └── cli.py            # CLI entry point
├── SETUP_STEVEN.md       # Windows collaborator guide
└── pyproject.toml
```

## What's Stable (May 2026)

- Full TUI with cues list, snapshot history, assignee tracking
- P2P push/pull of cues and audio stems over Tailscale/LAN
- Snapshots with visual diffs (arrangement, tracks, clips, BPM)
- Mobile-friendly web companion with tabbed layout
- Live 12 `.als` format support (Ableton wrapper, tracks container, palette colors)
- Cue injection as Ableton markers
- Assignees survive push/pull cycles (fix applied)
- Cues sorted by timeline position
- Full teal border focus indicator on active panel + orange highlight on active item
- `j`/`k` navigation works on both cues and snapshot panes

## License

MIT
