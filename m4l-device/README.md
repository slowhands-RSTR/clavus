# Clavus M4L — Max for Live Device

Snapshot, cue, and control Clavus directly from Ableton Live.

## Architecture

```
┌─────────────────────┐       HTTP (localhost:7890)       ┌──────────────┐
│  Ableton Live 12    │  ────────────────────────────►   │  Clavus      │
│  ┌───────────────┐  │                                   │  Server      │
│  │ Clavus.amxd   │  │  ◄────────────────────────────   │  (FastAPI)   │
│  │               │  │                                   │              │
│  │ [Snapshot]    │  │  POST /api/projects/snapshot      │  port 7890   │
│  │ [Mark Cue]    │  │  GET  /api/cues?pending_only=1    │              │
│  │ [Inject]      │  │  POST /api/projects/inject         │              │
│  │ [Restore]     │  │  POST /api/projects/restore        │              │
│  │               │  │                                   │              │
│  │ — pending —   │  │                                   │              │
│  │ ● @1.1.1      │  │                                   │              │
│  │ ● @45.1.1     │  │                                   │              │
│  └───────────────┘  │                                   └──────────────┘
└─────────────────────┘
```

## Requirements

- Ableton Live 12 Suite (with Max for Live)
- Clavus server running (`clavus serve`)

## What It Does

The M4L device provides an in-Live panel with:

1. **Connection status** — Green dot when Clavus server is reachable
2. **Snapshot button** — Snapshots current .als state with auto-generated message (e.g. "Arrangement @ 3:45")
3. **Quick Cue button** — Marks the current playback position with a cue
4. **Pending cue count** — Shows how many unresolved cues exist
5. **Inject button** — Writes all pending cues as Ableton markers
6. **Restore button** — Restores last snapshot
7. **Cue list** — Scrollable list of pending cues showing position and text

## Max Patch Structure

```
clavus.amxd
└── clavus.maxpat           # Main Max patch
    ├── live.thisdevice      # M4L context — connects to Live API
    ├── live.text            # Reads current song name
    ├── live.remote          # Reads transport position
    ├── live.remote~         # Reads Tempo
    ├── js clavus-api.js     # HTTP calls via [maxurl]
    ├── maxurl               # libcurl wrapper — GET/POST/PUT/DELETE
    ├── dict                 # JSON response parsing
    └── ui/                  # UI elements (buttons, text, color)
        ├── bpatcher "btn_snapshot" ...
        └── ...
```

## Max Patch Diagram (Textual)

In Max, the patch connects like this:

```
live.thisdevice
    │
    ├──► live.text "thisdevice_songname" ──► js clavus-api.js (setProjectName)
    │
    ├──► live.remote "live_set current_song tempo" ──► /js
    │
    └──► [button] "Snapshot"
              │
              ▼
        [maxurl] POST /api/projects/snapshot
         { "message": "Arrangement @ 3:45" }
              │
              ▼
          [dict] response
              │
              ├──► [print] (status)
              └──► [led] green blink
```

## M4L Device UI

The device sits in Ableton's device chain area (like any other M4L device):

```
┌─────────────────────────────────────────────┐
│  ~▼~ clavus                          ● ●   │
│─────────────────────────────────────────────│
│                                              │
│  [📸 Snap]  [📍 Cue]  [📌 Inj]  [↩ Rest]  │
│                                              │
│  ───────────── Pending Cues ──────────────  │
│                                              │
│  ● @1.1.1  bridge feels long                │
│  ● @45.1.1  second drop needs more sub      │
│  ● @68.1.1  bass sidechain too aggressive   │
│                                              │
│  Last snapshot: a1b2c3d4  "arrangement v3"  │
│─────────────────────────────────────────────│
│  conn: ✓  snaps: 7  cues: 3                │
└─────────────────────────────────────────────┘
```

## API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/ping` | GET | Health check / connection test |
| `/api/project?name=<project>` | GET | Get current snapshot hash + project info |
| `/api/projects/snapshot?name=<project>` | POST | Create snapshot `{"message": "..."}` |
| `/api/cues?pending_only=1&name=<project>` | GET | List pending cues |
| `/api/cues?name=<project>` | POST | Add cue `{"text": "...", "position": "45.1.1", "track": "..."}` |
| `/api/projects/restore?name=<project>` | POST | Restore HEAD snapshot |
| `/api/projects/inject?name=<project>` | POST | Inject cues as Ableton markers |
| `/api/sync/pull?name=<project>` | GET | Pull cues + snapshots |

## Build Steps

Once Ableton Live 12 is installed:

1. Open Max for Live's Max Editor
2. Create new device
3. Add `[live.thisdevice]` for M4L context
4. Add `[maxurl]` for HTTP — this wraps libcurl and handles GET/POST JSON
5. Add `[js clavus-api.js]` — JavaScript glue that translates Max messages to HTTP calls
6. Add buttons, text, LEDs for UI
7. Save as `Clavus.amxd`

The `clavus-api.js` file handles:
- `ping()` — GET `/api/ping`, outlet connection status
- `snapshot(project, message)` — POST snapshot with message from current position
- `getCues(project)` — GET pending cues, output to Max text objects
- `addCue(project, text, position, track)` — POST a new cue
- `restore(project)` — POST restore
- `inject(project)` — POST inject
