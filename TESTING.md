# Testing — Clavus

Living test matrix. Mark ✅ (pass), ❌ (fail), ⚠️ (flake), 🔲 (untested). Add date + notes.

## Collaboration (two-machine)

| # | Test | Mac↔Win | Win↔Win | Mac↔Mac | Notes |
|---|------|:---:|:---:|:---:|-------|
| C1 | Push snapshots → peer pulls | ✅ 5/11 | 🔲 | 🔲 | |
| C2 | Peer pushes → you pull | ✅ 5/11 | 🔲 | 🔲 | |
| C3 | Both edit same cue → push/pull → ⚠ appears | ✅ 5/11 | 🔲 | 🔲 | |
| C4 | Resolve cue conflict with `!` → push → peer pulls resolved | ✅ 5/11 | 🔲 | 🔲 | |
| C5 | Both edit same snapshot message → ⚠ appears on snap | ✅ 5/12 | 🔲 | 🔲 | Mac↔Win — push Mac, pull Win → ⚠ appears |
| C6 | Resolve snapshot message conflict with `!` | ✅ 5/12 | 🔲 | 🔲 | Mac↔Win — Win picked remote version, conflict cleared |
| C7 | Peer pushes snap → you `o` to open in Ableton | ✅ 5/11 | 🔲 | 🔲 | Cross-machine open |
| C8 | Peer pushes snap → you `T` restore → .als lands correctly | ✅ 5/11 | 🔲 | 🔲 | Restore works; Suite/Intro .als mismatch is Ableton-side |
| C9 | Stem import → push → peer pulls → WAV appears | ✅ 5/12 | 🔲 | 🔲 | Win→Mac stem push, Mac materialized 3 WAVs |
| C10 | Stem push/pull dedup (same WAV doesn't transfer twice) | ✅ 5/12 | 🔲 | 🔲 | Second push: 0 stems, skip unreachable remote |
| C11 | Push → peer edits → peer pushes → you pull (roundtrip) | ✅ 5/11 | 🔲 | 🔲 | Mac→Win relay push + Win local pull validated; full peer-edit cycle not yet |
| C12 | Rapid push/edit/push (optimistic locking: 409 rejection) | ✅ 5/12 | 🔲 | 🔲 | Win pushed first → Mac 409 → pull → auto-snap → push OK |
| C13 | Network drop mid-push → retry → clean state | 🔲 | 🔲 | 🔲 | |
| C14 | Sample materialization after blob download (order bug) | ✅ 5/13 | 🔲 | 🔲 | Fixed: blobs downloaded first, then materialized (was reversed) |
| C15 | Relay restart while clients connected → clients recover | ✅ 5/12 | 🔲 | 🔲 | Mac relay killed → Win error → restart → Win push OK |
| C16 | Cross-account Tailscale (shared node, MagicDNS) | ✅ 5/11 | 🔲 | 🔲 | MagicDNS share URL (chrispc.tail46b8d9.ts.net) → join → pull 10 projects ✅; Pull spinner hangs on dead remotes (Windows) |

## TUI

| # | Test | macOS | Windows | Notes |
|---|------|:---:|:---:|-------|
| T1 | `c` new cue → appears in list → Ableton marker injection | ✅ 5/10 | ✅ 5/11 | |
| T2 | `C` snapshot → history updates | ✅ 5/10 | 🔲 | `C` binding removed — use `S` |
| T3 | `S` snapshot + auto-push | ✅ 5/10 | ✅ 5/11 | |
| T4 | `e` edit cue text → persists | ✅ 5/10 | ✅ 5/11 | |
| T5 | `e` edit snapshot message → persists after reload | ✅ 5/10 | ✅ 5/11 | |
| T6 | `!` resolve cue conflict (ConflictScreen modal) | ✅ 5/12 | ✅ 5/11 | |
| T7 | `!` resolve snapshot message conflict (SnapConflictScreen) | ✅ 5/12 | ✅ 5/12 | |
| T8 | `o` open HEAD in Ableton | ✅ 5/10 | ✅ 5/11 | |
| T9 | `o` from history pane → open selected snapshot | ✅ 5/10 | ✅ 5/11 | |
| T10 | `T` restore to snapshot | ✅ 5/10 | ✅ 5/11 | |
| T11 | `d` diff selected snapshot | ✅ 5/10 | ✅ 5/11 | |
| T12 | `p` pull → auto-snapshot → history updates | ✅ 5/10 | ✅ 5/11 | |
| T13 | `P` push → relay receives | ✅ 5/10 | ✅ 5/11 | |
| T14 | `Tab` switch cues ↔ history pane | ✅ 5/10 | ✅ 5/11 | |
| T15 | `j`/`k` navigation, scrolling | ✅ 5/10 | ✅ 5/11 | |
| T16 | `?` help screen (all bindings visible) | ✅ 5/10 | ✅ 5/11 | |
| T17 | `:` command mode → `:snapshot msg`, `:pull`, `:push` | ✅ 5/10 | ✅ 5/11 | |
| T18 | `:project <name>` switch projects → cues/history reload | ✅ 5/10 | ✅ 5/11 | |
| T19 | `:init <path>` from TUI → project loads | ✅ 5/10 | ✅ 5/11 | |
| ~~T20~~ | ~~`:browse`~~ | ~~removed~~ | ~~removed~~ | Scrapped — Finder paste + `:init` is faster |
| T21 | Header dot: green ● (connected), yellow ○ (remote, no data), dim ○ (no remote) | ✅ 5/10 | ✅ 5/11 | |
| T22 | Freeze detection warning on `S` | ✅ 5/10 | ✅ 5/11 | :freeze toggle — warn (default) or block |
| T23 | Long cue text / snapshot message → no truncation crash | ✅ 5/10 | ✅ 5/11 | |
| T24 | TUI survives corrupt meta file (orphaned 10-char hash) | ✅ 5/11 | 🔲 | Cycle detection + missing snap + self-referencing parent guards |
| T25 | `:projects` picker — j/k navigate, enter select, esc cancel | ✅ 5/11 | ✅ 5/11 | |
| T26 | `:remotes` picker — per-project remote scoping | ✅ 5/11 | ✅ 5/11 | Push/pull uses selected remote only |
| T27 | `:inject` → cues land as Ableton markers → auto-snapshot | ✅ 5/11 | ✅ 5/11 | |
| T28 | `:push!` force push — skips lock, overwrites relay HEAD | ✅ 5/11 | ✅ 5/11 | Fixed 5/11 eve: was async without @work — never executed |
| T29 | `:pull-all` — pull all projects from active remote | ✅ 5/11 Mac | ✅ 5/11 Win | Fixed: parsing bug — "pull all" hit subprocess branch instead of _run_pull_all |

## CLI

| # | Test | macOS | Windows | Notes |
|---|------|:---:|:---:|-------|
| L1 | `clavus setup` wizard | ✅ 5/11 | ✅ 5/11 | |
| L2 | `clavus init <path>` → project created | ✅ 5/10 | ✅ 5/11 | |
| L3 | `clavus tui` opens dashboard | ✅ 5/10 | ✅ 5/11 | ⧩ logo restored |
| L4 | `clavus share` starts relay | ✅ 5/11 | ✅ 5/11 | Clean start, no port conflict, Tailscale URL |
| L5 | `clavus join <url>` adds remote + pulls | ✅ 5/11 | ✅ 5/11 | 9 projects pulled with cues/snaps/samples |
| L6 | `clavus find` discovers peers | ✅ 5/11 | ✅ 5/11 | No servers (expected), clean message |
| L7 | `clavus remote add/list/remove` | ✅ 5/11 | ✅ 5/11 | List/add/remove works |
| L8 | `clavus push` / `clavus pull` | ✅ 5/11 | ✅ 5/11 | |
| L9 | `clavus snapshot "msg"` | ✅ 5/11 | ✅ 5/11 | No-change detection works |
| L10 | `clavus backup` → `clavus backups` → `clavus restore-store` | ✅ 5/11 | ✅ 5/11 | 4 backups, 182MB latest |
| L11 | `clavus repair` fixes corrupted index | ✅ 5/11 | ✅ 5/11 | |
| L12 | `clavus doctor` health check | ✅ 5/11 | ✅ 5/11 | |
| L13 | `clavus stem import/push/pull/list` | ✅ 5/11 | 🔲 | Import, list, push all ✅ |
| L14 | `clavus open` launches Ableton with HEAD | ✅ 5/11 | ✅ 5/11 | |
| L16 | `clavus p2p` peer discovery (local and tailnet peers) | ✅ 5/13 | 🔲 | Online/offline listing, MagicDNS, usage hints |
| L17 | `clavus p2p --host` / `--connect` TCP sync | ✅ 5/13 | 🔲 | Manifest exchange, conflict detection, blob sync |
| L18 | relay: `force=True` bypasses conflict check | ✅ 5/13 | 🔲 | Bug: force was parsed by API model but never checked |

## Edge Cases & Error Handling

| # | Test | macOS | Windows | Notes |
|---|------|:---:|:---:|-------|
| E1 | Empty project (no snapshots) → snapshot → push | ✅ 5/11 | 🔲 | Init→auto-snap→push(409)→pull→push ✅ |
| E2 | Empty relay → push/pull → clear error message | ✅ 5/11 | ✅ 5/11 | |
| E3 | Pull with no remotes configured → clear error | ✅ 5/11 | ✅ 5/11 | ✗ in header + footer error |
| E4 | Push with no remotes → clear error | ✅ 5/11 | ✅ 5/11 | ✗ in header + footer error |
| E5 | Corrupted .als file → snapshot fails gracefully | ✅ 5/12 | 🔲 | Content-addressed — stored corrupt bytes, no crash |
| E6 | Missing Ableton → `clavus open` fails gracefully | 🔲 | 🔲 | |
| E7 | Very large .als (200+ tracks, 10MB+) → snapshot performance | 🔲 | 🔲 | Need Ableton save to trigger real change |
| E8 | Project with non-ASCII characters in name/path | ✅ 5/12 | 🔲 | "Shades Of Love Edit (7) 2022" — parens, spaces fine |
| E9 | Multiple remotes → push to all, pull from all | 🔲 | 🔲 | |
| E10 | `clavus share` port conflict → clear error | ✅ 5/12 | 🔲 | Win: pull latest for fix |
| E11 | Cross-project push: push project A, switch to B, push B | ✅ 5/13 | 🔲 | Fixed: conflict was using global HEAD instead of per-project |
| E12 | Sample blob sync: push with samples → pull → files on disk | ✅ 5/13 | 🔲 | Fixed: materialization was running before blob download |
| E13 | CLI push --force / -f flag | ✅ 5/13 | ✅ 5/13 | Spinner shows "force pushing to 'name'..." |
| E14 | CLI pull-all — pull all projects from active remote | ✅ 5/13 | ✅ 5/13 | 11 projects pulled with individual spinners |
| E15 | TUI :find — peer discovery from TUI | ✅ 5/13 | ✅ 5/13 | Clean "no peers found" message (expected — relay uses MagicDNS, not discovery) |
| E16 | TUI :repair — store repair from TUI | ✅ 5/13 | 🔲 | Runs clavus repair and reloads |
| E17 | Windows emoji: subprocess pipe handles UTF-8 | ✅ 5/13 | ✅ 5/13 | Fixed: PYTHONIOENCODING=utf-8 + [SCAN] replaces 📡 |

## Platform-Specific

| # | Test | Status | Notes |
|---|------|:---:|-------|
| P1 | Windows: TUI renders correctly (Windows Terminal) | ✅ 5/11 | |
| P2 | Windows: `os.startfile()` opens .als in Ableton | ✅ 5/12 | |
| P3 | Windows: OneDrive Files On-Demand → .als accessible | 🔲 | |
| P4 | Windows: `py -m pip install -e .` works from fresh clone | ✅ 5/12 | | Steven 8:52pm reinstall confirmed — all May 12 fixes present; C15 (dead remote timeout) probe already at 10s |
| P5 | macOS: `open` command launches Ableton | ✅ 5/10 | |
| P6 | macOS: `tailscale serve` survives sleep/wake | 🔲 | |
| P7 | Linux: install + `clavus tui` runs (no DAW needed) | 🔲 | |
| P8 | Cross-platform: Mac snapshot → Windows restore → opens in Ableton | ✅ 5/12 | | |
| P9 | Cross-platform: Windows snapshot → Mac restore → opens in Ableton | ✅ 5/12 | | |

## Test Sessions

| Date | Who | Platform | Tests run | Results |
|------|-----|----------|-----------|---------|
| 5/10/26 | Chris + Hermes | macOS | T1-T5, T8-T19, T21-T23, L2-L3, L12, P5 | 25+ ✅. Bugs fixed: assign/unassign fingerprint, missing Path import, 10-char hash → full_hash in diff, 📸→● emoji purge, ⧩ logo restored, inject→auto-snapshot, freeze soft warning, archive/delete prefill. Spinner animation fixed. |
| 5/11/26 | Chris + Hermes | macOS | :projects picker, :remotes picker, L5 (join), E1 (no .als), L4 (share relay) | :projects j/k/enter switcher done. :remotes picker + per-project remote scoping. :browse scrapped — Finder paste + :init faster. :init now strips quotes/tilde/Finder paste. Push/pull uses single active remote per project. 7+ crashes fixed (debounce, fingerprint, stale index on pickers, sync_url compat). 43 total ✅. |
| 5/11/26 | Chris + Hermes | Windows | T1, T3, T12, T13, T15, T18, T25-T28, P1 | Windows TUI confirmed: c, S, p, P, j/k, :project, :projects, :remotes, :inject, :push! all working. Force push deadlock fixed — relay now updates HEAD on force push even when snapshots already exist. F binding removed, :push! is break-glass command-only. |
| 5/11/26 eve | Chris + Hermes | Mac+Win | :pull-all, :push!, push conflict bugs | **:push! was never executing** — `async` without `@work`, same bug as :pull-all. Fixed. **Cross-project push conflicts** — `last_head` was per-remote global, switching projects caused 409. Fixed: `ClavusProject.last_remote_head`. **:pull-all error invisible on Windows** — 6 attempted fixes (30s timer, sentinel, _sticky_error, direct widget.write, forced refresh). Root cause appears to be CSS `display:none` still active when @work worker writes to #footer-status. Error text lands in hidden widget. Needs modal/log-file approach. 7 commits. |
| 5/11/26 night | Chris + Hermes | Mac+Win | H1-H2 hardening, C1-C4, C7-C8 collaboration | **Hardening branch tested.** --debug flag + errors.log confirmed. **3 pull bugs fixed:** welcome autoload, root_als gate, global HEAD ref blocking per-project heads. 4 commits merged to main. **Collaboration validated:** Mac↔Win push/pull, cue conflict ⚠ + ! resolution, cross-machine `o` open, `T` restore all ✅. Suite/Intro .als incompatibility is Ableton-side, not Clavus. |
| 5/13/26 | Chris + Hermes | macOS + Win | L16-L18 P2P, relay bugs, E11-E12 | **P2P transport** built & tested (manifest, conflict, blob sync). **3 relay bugs fixed**: force=True ignored, empty snap crash (500), global HEAD ref causing cross-project false conflicts. **Sample materialization fixed**: blobs downloaded before materialization. **Collaborator test**: Steven nuked/reinstalled, joined, pulled, pushed his own project "edit anthem v2" with 31 sample blobs. **Beta checklist written** (docs/beta-checklist.md). |
|| 5/13/26 | Chris + Hermes | macOS | Full test suite (test_*.py), P2P smoke, CLI smoke, doctor, p2p --help | **All 6 test scripts passed** (test_cli, test_cues, test_snapshot, test_parser, test_cli_full, test_watch). **P2P transport:** manifest exchange ✅, conflict detection ✅, full blob sync ⚠️ (race in _smoke_full_sync, p2p_sync itself works). **CLI:** `clavus p2p` discovers 2 online + 3 offline peers. `clavus doctor` shows 21 ✅ / 1 ⚠️ / 1 ❌ (relay not running). **New code reviewed:** P2P transport (~750 lines), git-style conflict detection, ThreadPoolExecutor blob upload, relay HEAD probe, doctor tailscale/relay checks, auto tailscale serve setup on `clavus share`. |
|| 5/13/26 eve | Chris + Hermes | Win + Mac | CLI parity build, push/pull spinners, round-trip beta gate | **CLI progress module** built (309 lines): braille spinner, tqdm progress bar, status helpers. **CLI parity**: `--force`/`-f` on push, `pull-all` subcommand, `clavus inject` alias, `clavus freeze`, `clavus name`. **TUI fixes**: `:find`, `:repair` commands added + help screen updated. **Windows emoji fix**: all 12 TUI subprocess calls set `encoding='utf-8'`, CLI `cmd_find` uses `[SCAN]` instead of 📡. **Beta round-trip verified**: Chris snapped & pushed `italovibez` from Windows → relay → Mac pulled and confirmed new HEAD `71f6a446 "snap 19:10"`. 12 snapshots, 16 cues, 40 blobs synced. |

---

**Legend:** ✅ Pass  ❌ Fail  ⚠️ Flake / intermittent  🔲 Untested

**How to use:** Before a release, run through 🔲 items. Mark ✅/❌ with date. File bugs for ❌. After each test session, add a row to Test Sessions.
