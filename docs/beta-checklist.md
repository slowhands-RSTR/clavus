# Clavus Beta Readiness Checklist

**Target:** A clean round-trip between two people with no manual workarounds.
**Gate:** Everything in the **Core Flow** section must pass on both Mac and Windows.

---

## 🔴 Core Flow (must pass to call it beta)

| # | Test | Who | Status | Notes |
|---|------|-----|--------|-------|
| B1 | Fresh install: clone → `pip install -e .` → `clavus setup` works | Both | 🔲 | |
| B2 | Host starts relay: `clavus share` → prints Tailscale URL | Host | ✅ 5/13 | |
| B3 | Collaborator joins: `clavus join <url>` → projects appear | Steven | 🟡 5/13 | Worked after nuke + reinstall |
| B4 | Pull: `p` in TUI → snapshots + cues land | Both | 🟡 5/13 | Cues synced ✅. Samples need re-test with latest code |
| B5 | Make change in Ableton → `S` snapshot → `P` push → relay receives | Steven | 🟡 5/13 | Steven pushed successfully after HEAD fix |
| B6 | Other side pulls → sees the pushed snapshot + samples on disk | Host | 🔲 | **Needs re-test** — samples should materialize now |
| B7 | Both edit → push/pull → conflict detected → resolve with `!` | Both | ✅ 5/11 | C3-C4 from testing matrix |
| B8 | Switch projects via `:project <name>` → pull/push works | Both | 🟡 5/13 | Cross-project HEAD bug fixed, needs re-test |
| B9 | Open project in Ableton with `o` | Both | ✅ 5/11 | |
| B10 | Cue inject: `:inject` → markers appear in Ableton | Both | ✅ 5/11 | |

---

## 🟡 Important But Not Blocking

| # | Test | Status | Notes |
|---|------|--------|-------|
| I1 | Force push (`:push!`) works when needed | ✅ 5/13 | force=True now actually bypasses conflict check |
| I2 | Relay survives restart → clients reconnect | ✅ 5/12 | |
| I3 | Large project (100+ tracks, 10MB .als) → push/pull | 🔲 | Need a real project to test |
| I4 | Non-ASCII project names | ✅ 5/12 | "Shades Of Love Edit (7) 2022" works |
| I5 | Pull-all (`:pull-all`) fetches all projects from relay | ✅ 5/11 | |
| I6 | P2P direct sync (no relay) for one-off sync | ✅ 5/13 | TCP transport, conflict detection, full blob sync |
| I7 | Windows: TUI renders correctly | ✅ 5/11 | |
| I8 | Cross-platform round trip: Mac snap → Win restores → opens | ✅ 5/12 | |
| I9 | Cross-platform round trip: Win snap → Mac restores → opens | ✅ 5/12 | |

---

## 🔵 Stretch (post-beta)

| # | Test | Notes |
|---|------|-------|
| S1 | Network drop mid-push → retry → clean state | Low priority |
| S2 | `clavus doctor` shows relay health, sample integrity | Nice-to-have |
| S3 | OneDrive / cloud-synced project folders | Windows-specific |
| S4 | Linux: install + TUI runs | No DAW needed |
| S5 | Sample blob surrogate character edge case (rare .als files) | Happens if .als has unicode surrogates in XML |

---

## Steps to Beta

### For Host (Chris)

- [ ] Pull latest `perf-improvements`
- [ ] `py -m pip install -e .`
- [ ] Restart relay (`kill` old → `clavus share --port 7891`)
- [ ] Verify Tailscale serve proxy: `curl http://localhost:7891/api/ping` → 200
- [ ] Re-push any projects that need samples synced
- [ ] Confirm Steven can pull samples now

### For Collaborator (Steven)

- [ ] `cd C:\Users\soulb\clavus && git pull && py -m pip install -e .`
- [ ] `clavus pull` (or `p` in TUI) — confirm samples land on disk
- [ ] Open project in Ableton with `o`
- [ ] Make a small edit → `S` snapshot → `P` push
- [ ] Have host pull back and verify changes landed

### Clean Round-Trip (gate to beta)

1. Host pushes `italovibez` to relay ✅
2. Steven pulls → sees project, cues, samples on disk ✅
3. Steven makes a change, snapshots, pushes ✅
4. Host pulls → sees Steven's changes ✅
5. Both edit same thing → conflict detected → resolved ✅

**If all 5 pass without manual intervention: ship beta.**
