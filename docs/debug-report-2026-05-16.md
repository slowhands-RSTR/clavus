# Debug Report — May 16, 2026

Improving cross-platform sample sync reliability and sync progress feedback.

---

## Problem: Samples Not Reaching Windows After Initial Sync

### User Symptom
"Me And You" project had samples in the expected project folders on Mac (`~/Clavus/Projects/Me And You/Samples/Imported/`, `Samples/Recorded/`, etc.) but after a `pull` on Windows, the samples weren't there.

### Investigation

**What we found:** The sample detection pipeline was working correctly end-to-end in theory, but broke down at two conversion layers between Ableton's project file format and Clavus's sync logic.

**1. Ableton project format differences across versions**

Different Ableton Live versions serialize sample references in the `.als` project file differently. The sync pipeline assumed a single format. In practice, this meant Clavus was silently skipping sample detection on projects created in older Live versions — no error, just 0 samples found.

**2. Stale path references in legacy projects**

Projects that were moved or had samples imported from non-project locations can store path references that point to locations that no longer exist on disk. Clavus was strictly following these paths and reporting "file not found" for every sample, when a more flexible lookup within the project folder would have found the actual files.

### Changes

**parser.py** — Extended `extract_sample_paths()` to handle additional sample reference formats found in older Ableton Live projects. Also improved path reconstruction to avoid missing samples when directory structures vary.

**store.py** — Added fallback path resolution when the path stored in the project file doesn't resolve directly. Instead of failing, Clavus now searches within the project folder by filename to find the actual sample.

---

## Problem: Sync Progress Unclear During Pull

### User Symptom
During a `pull` that downloaded multiple files (snapshots, samples, audio), the UI showed minimal feedback. It was unclear how much remained or what was being downloaded.

### Investigation

**What we found:** The progress reporting callback was initialized incorrectly — it was reporting `0/X` throughout the download because the total count wasn't set before the first progress update.

### Changes

**sync.py** — Corrected the progress callback to report actual totals from the start, giving users visible `sample: 3/8` feedback during download instead of an unhelpful `sample: 0/X`.

---

## Problem: Relay Conflict Detection on Fresh Install

### User Symptom
First `push` from a new Clavus install triggered a conflict error instead of completing normally.

### Status
Investigated but not fully root-caused. The likely cause is stale state on the relay from a previous session. A workaround is available: `:push!` bypasses the conflict check and completes the push.

---

## Summary

| Area | Change |
|------|--------|
| Sample detection | Broader format support for Ableton project files |
| Sample sync | Fallback path resolution when stored paths are stale |
| Sync feedback | Accurate progress counters during pull operations |
| Documentation | Added `:push!` and `:remotes` to in-app help |

**Commits:** `88f8a7a`, `f2b43cf`