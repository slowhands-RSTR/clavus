# Clavus Build Plan — v0.6.0 Release Prep

## Current State (May 2026)

Everything core is built and working. What remains is polish, hardening, and docs for public release.

## ✅ Complete

| Area | What | Status |
|------|------|--------|
| Parser | .als XML (Ableton 10+ wrapper + Live 9 root) | ✅ |
| Snapshots | Content-addressed, diff engine, visual diff | ✅ |
| CLI | init, snapshot, log, diff, status, restore | ✅ |
| Cues | CRUD, threaded replies, assignees, marker injection | ✅ |
| Watch daemon | File watcher + auto-snapshot | ✅ |
| TUI | Full keyboard-driven cues + history management | ✅ |
| Sync | P2P push/pull of cues, snapshots, stems | ✅ |
| WebSocket | Real-time sync between TUI and server | ✅ |
| Stems | Import, list, push, pull, dedup via blob store | ✅ |
| Restore | Full .als restore from snapshot (CLI + TUI + API) | ✅ |
| Diff in TUI | Inline text diff via `d` key | ✅ |
| Share/Join | Tailscale-first peer discovery, human-friendly codes | ✅ |
| Relay | Stripped-down API-only server | ✅ |
| Git integration | Branch, checkout, merge via CLI | ✅ |
| Keyboard | Hammerspoon (macOS) + AutoHotkey (Windows) | ✅ |
| mDNS discovery | LAN peer discovery via zeroconf | ✅ |
| Tailscale | Tailnet device scanning via local API | ✅ |
| Config | File/env/CLI inheritance, config wizard | ✅ |
| Repair | index.json auto-backup + recovery | ✅ |

## ❌ Removed

| Feature | Reason |
|---------|--------|
| Web companion (HTML/CSS/JS UI) | Bloat — TUI is the UI |
| M4L device endpoints | Not part of core product |

## 🔲 Remaining for Public Release

### 1. Testing & CI
- [ ] Add integration tests for share/join flow (mDNS → relay → pull)
- [ ] Add relay server API endpoint tests
- [ ] Ensure CI passes on all Python 3.10-3.13
- [ ] Add Windows Python 3.13 to CI matrix

### 2. Polish & UX
- [ ] `clavus tui` should auto-start a relay if none is running (one-command experience)
- [ ] Better error messages on connection loss in TUI
- [ ] `:share` from TUI should optionally start relay on different port if 7890 is busy
- [ ] Config: add `CLAVUS_AUTO_RELAY` env var for always-on relay

### 3. Documentation
- [x] README — stripped web companion refs, added share/join
- [ ] SETUP_STEVEN.md — remove web companion, add share/join flow
- [ ] BUILD_PLAN.md — this file, current
- [ ] CLI help text — clean up outdated references

### 4. Packaging
- [ ] Verify `pip install clavus` works clean (no web deps)
- [ ] Version bump to 0.7.0 or 1.0.0-beta
- [ ] Add PyPI long description from README

### 5. Edge Cases
- [ ] Handle port-in-use gracefully in relay/share
- [ ] Handle TUI starting without a project
- [ ] Auto-reconnect to relay after network interruption
- [ ] Cross-platform path handling (Windows vs macOS vs Linux)
