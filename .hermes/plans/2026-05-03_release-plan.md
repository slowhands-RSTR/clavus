# Clavus — Open Source Release Plan

**Date:** 2026-05-03
**Current state:** Working prototype. All core features exist but not release-ready.

---

## Goal

Ship Clavus v0.5.0 as a polished open-source tool that someone can `pip install clavus` and start using immediately — without any hardcoded references to Chris's machine.

---

## What's Hardcoded to Chris's Machine (And Everything Else)

### Core code (clavus/*.py) — SURPRISINGLY CLEAN
The main library code has **no hardcoded paths** to LaCie, `/Users/slowhands`, or any personal data. It uses:
- `DEFAULT_CLAVUS_DIR` via `CLAVUS_DIR` env var or `~/.clavus` — configurable ✅
- `CLAVUS_SERVER` env var or `localhost:7890` — configurable ✅  
- `os.environ.get("USER")` for author fallback — works everywhere ✅
- Port 7890 is the default but overridable via `--port` ✅

**What needs config:**
1. **Author name** — TUI saves to `~/.config/clavus/config.json` (good pattern but doesn't cover CLI or web)
2. **Default project** — CLI uses CWD matching, TUI auto-selects first project from server
3. **Default port/server** — 7890 hardcoded as default everywhere (good as a default, needs to be configurable via file)

### Test files — COMPLETELY HARDCODED
- `test_real_als.py` — `/Volumes/LaCie/Ableton Live Projects (Local Drive)/...`
- `test_snapshot.py` — same LaCie path
- `test_cli.py` — same LaCie path  
- `test_cli_full.py` — same LaCie path + `shutil.rmtree(~/.clavus)` (DESTROYS USER DATA)
- `test_env_debug.py` — `/Users/slowhands/Developer/clavus` hardcoded

### Hotkey scripts — NOT hardcoded
- `hammerspoon.lua` — port 7890 as a `local` variable at top ✅
- `autohotkey.ahk` — host + port as variables ✅  
Both just need a config file mechanism instead of inline variables.

### Web UI — GOOD
- No hardcoded paths in the generated HTML/CSS/JS (all API calls are relative)
- Tailscale URL detection uses `socket.gethostname()` — portable ✅

---

## Plan (Updated with Configuration Phase)

### Phase 0 — Configuration System
Before anything else, build a proper user config so nothing is tied to Chris's machine.

**Config file: `~/.config/clavus/config.json`**

```json
{
  "author": "Chris",
  "port": 7890,
  "host": "0.0.0.0",
  "default_server": "http://localhost:7890",
  "project": "Northern Lights"
}
```

- `config.py` module with `ClavusConfig` class
  - Loads from `~/.config/clavus/config.json`
  - Falls back to env vars (`CLAVUS_PORT`, `CLAVUS_HOST`, `CLAVUS_AUTHOR`)
  - Falls back to hardcoded defaults
- Used by: CLI, web server, TUI, hotkey scripts
- `clavus config` CLI command to view/edit (set key=value)
- Hotkeys: read config via `io.open` at startup instead of inline vars

**Files to create:** `clavus/config.py`
**Files to modify:** `clavus/cli.py`, `clavus/web.py`, `clavus/tui.py`, `hotkeys/hammerspoon.lua`, `hotkeys/autohotkey.ahk`, `hotkeys/bindings.json`

### Phase A — Clean Slate
1. **Fix `--graph` parser bug** in `cli.py`
2. **Fix test isolation** — all tests use `CLAVUS_DIR` env var pointing to temp dirs
3. **Fix LaCie hardcoding** — LaCie tests skip gracefully when drive not mounted
4. **Squash-commit** the assignee/in_progress work onto `main`
5. **Tag as `v0.5.0-alpha.1`**

### Phase B — Add TUI Archive Action
6. **`action_archive()`** — keybinding `x`, `:archive` command, dimmed rendering for archived cues

### Phase C — Release Hardening
7. **Real README** — install, quick start, feature tour, keyboard ref, hotkey setup
8. **LICENSE** (MIT)
9. **pyproject.toml** — author, license, URLs, Python classifiers, verify entry points
10. **GitHub CI** (`.github/workflows/ci.yml`)
11. **`--version` flag**
12. **Verify `pip install`** in fresh venv

### Phase D — Polish
13. Clean up stale debug scripts from git tracking
14. Push to GitHub as public repo

---

## Files That Change

| File | Change |
|------|--------|
| `clavus/config.py` | **NEW** — config load/save with env fallback |
| `clavus/cli.py` | Use config module, fix `--graph`, add `--version` |
| `clavus/web.py` | Read port/host from config |
| `clavus/tui.py` | Use config for author + server URL, add archive action |
| `clavus/cues.py` | Archive display helpers |
| `hotkeys/hammerspoon.lua` | Read config file at startup |
| `hotkeys/autohotkey.ahk` | Read config file at startup |
| `hotkeys/bindings.json` | Update with archive key |
| `test_*.py` | All: fix LaCie paths, fix graph, use temp dirs |
| `test_real_als.py` | Graceful skip when LaCie not mounted |
| `pyproject.toml` | License, URLs, classifiers |
| `README.md` | Complete rewrite |
| `LICENSE` | **NEW** (MIT) |
| `.github/workflows/ci.yml` | **NEW** |

---

## Risks & Tradeoffs

- **Config system is scope creep** for a "quick release" — but necessary because hardcoded paths prevent anyone else from using the tests, and the author name/config system is currently split across TUI config, env vars, and `os.getlogin()` — inconsistent.
- **Hotkey scripts reading JSON** — Hammerspoon is Lua, AutoHotkey is AHK. Both can read JSON with a bit of boilerplate. Worth it for portable config.
- **Test isolation is mandatory before open source** — `test_cli_full.py` destroying `~/.clavus` would be a PR nightmare if someone runs tests against their real projects.
- **LaCie tests** — the "real .als" tests are valuable but should silently skip when the drive isn't mounted. Currently they crash with a traceback.
- **Version**: 0.2.0 → 0.5.0 jump is intentional — the feature set (assignee, archive, config system, stem sync, TUI, web) is far beyond what 0.2.0 implies.

---

## Order of Execution (Updated)

```
00. Config module          (15 min) — new file + integrate into cli/web/tui
0a. Fix `--graph` bug     (2 min)
0b. Fix test isolation    (10 min) — temp dirs + LaCie graceful skip
0c. Run full test suite   (2 min)
0d. Commit + tag          (1 min)
0e. TUI archive           (20 min)
0f. Hotkey config read    (10 min) — make hammerspoon/ahk read config
1.  LICENSE file          (1 min)
2.  Rewrite README        (20 min)
3.  Update pyproject.toml (5 min)
4.  GitHub CI workflow    (10 min)
5.  `--version` flag      (5 min)
6.  Clean up stale files  (5 min)
7.  Verify in fresh venv  (5 min)
8.  Push to GitHub        (2 min)
```

Total estimated: ~2 hours.
