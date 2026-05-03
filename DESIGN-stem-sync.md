# Stem Sync — Design (Built)

**Goal:** Eliminate the freeze→bounce→zip→upload→download→extract→re-import nightmare.

## Architecture

### Stem Registry (`store.py`)
- `StemEntry` dataclass — metadata for one stem file (track name, hash, size, format, duration)
- `StemManifest` dataclass — maps a snapshot hash to its list of stems
- `StemStore` class — manages manifests, stores/receives stem blobs, materializes working trees

### Storage Layout
```
~/.clavus/
  objects/           ← content-addressed blob store (dedup'd by SHA256)
    4a/8f1b...       ← stem audio blob (same store as snapshot JSONs)
    7c/2e9a...       ← another stem blob
  stems/
    Project Name/
      abc123def456/  ← per-snapshot directory (truncated hash)
        StemManifest.json
        Kick.wav     ← materialized from blob store
        Bass.wav
```

### Dedup
Stems are stored as content-addressed blobs in the existing `objects/` store. SHA256 hash ensures:
- Same stem file = same blob = stored once
- Only changed stems consume new space
- v1→v2 where only Kick changed = 40MB new, not 600MB

## API Endpoints (`web.py`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/stems/{project}/manifest/{hash}` | Get stem manifest for a snapshot |
| POST | `/api/stems/{project}/manifest/{hash}` | Receive manifest from remote |
| GET | `/api/stems/blob/{hash}` | Download a stem blob |
| POST | `/api/stems/blob/{hash}` | Upload a stem blob |
| POST | `/api/stems/check` | Check which stem hashes are missing |

## Commands (`cli.py`)

```
clavus stem import Stems/Kick.wav --track "Kick"     # Import with current snapshot
clavus stem list                                       # List stems for HEAD
clavus stem list --snapshot abc123def                  # List for specific snapshot
clavus stem push                                       # Push stems to remotes
clavus stem pull                                       # Pull stems from remotes
```

## Sync Flow (`sync.py`)

### Push
1. Fetch remote's `POST /api/stems/check` with all stem hashes
2. Remote returns hashes it's missing
3. Upload each missing blob via `POST /api/stems/blob/{hash}`
4. Upload manifest via `POST /api/stems/{project}/manifest/{hash}`

### Pull
1. Fetch remote's manifest via `GET /api/stems/{project}/manifest/{hash}`
2. Check which stems are missing locally
3. Download each via `GET /api/stems/blob/{hash}`
4. Store blob + update local manifest
5. Materialize working tree: reconstruct WAV files from blobs

## Roadmap
- [x] Store: StemEntry, StemManifest, StemStore classes
- [x] CLI: stem import, stem list, stem push, stem pull
- [x] Web: GET/POST endpoints for manifests and blobs
- [x] Sync: push and pull stem files between remotes
- [x] Working tree: materialize stems from blobs
- [ ] Auto-push stems on `clavus push` (cues + stems together)
- [ ] Auto-pull stems on `clavus pull` (cues + stems together)
- [ ] Auto-materialize on pull
