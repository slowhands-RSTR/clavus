# Debug Report — May 16, 2026

Session notes from debugging relay conflicts, sample parsing, and path resolution issues.

---

## 1. Relay Conflict Detection False Positives

**Symptom:** Fresh `clavus init` on Mac, first push triggered conflict detection error (409 from relay). Required `:push!` to force through.

**Root cause (suspected):** Stale `last_head` ref persisted on the localhost relay from a previous Clavus install session. The relay's `HEAD` had moved in a prior run, and the new init's `expected_parent` didn't match.

**Workaround:** `:push!` bypasses conflict check and force-pushes.

**Status:** Not fully root-caused. Needs investigation into whether `last_head` is being properly initialized on first push after a fresh install.

---

## 2. Sample Parser Missing Ableton Live 10 Samples

**Symptom:** "Me And You" project on Mac had 53 samples in `Samples/Imported`, `Samples/Processed`, `Samples/Recorded` — but Clavus found 0 samples during `clavus snap`.

**Root cause:** `extract_sample_paths()` in `parser.py` only handled the `<Path Value="...">` attribute format used in newer Ableton Live (12.x). Ableton Live 10 stores sample references differently:

```xml
<!-- Live 12 format (what parser expected) -->
<SampleRef>
  <FileRef>
    <Path Value="Samples/Processed/file.aif" />
  </FileRef>
</SampleRef>

<!-- Live 10 format (what was actually in the .als) -->
<SampleRef>
  <FileRef>
    <HasRelativePath Value="true" />
    <RelativePathType Value="3" />
    <RelativePath>
      <RelativePathElement Id="33" Dir="Samples" />
      <RelativePathElement Id="34" Dir="Processed" />
      <RelativePathElement Id="35" Dir="Consolidate" />
    </RelativePath>
    <Name Value="file.aif" />
  </FileRef>
</SampleRef>
```

**Fix:** Added a second parsing path in `extract_sample_paths()` that handles `RelativePathElement Dir="..."` + `Name Value="..."` blocks, reconstructing the relative path from dir parts + filename. Also fixed a split bug (`"<SampleRef>"` → `"<SampleRef"`) that was preventing block splitting.

---

## 3. Live 10 Absolute Path Corruption

**Symptom:** After fixing the parser, samples were found but paths were malformed — e.g. `Samples/Imported/Users/chriscarr/Desktop/Me And You Project/Samples/Imported/chl_rhd_chord_G7.wav` instead of `Samples/Imported/chl_rhd_chord_G7.wav`.

**Root cause:** Ableton Live 10 has a known bug where `RelativePathElement` stores the full absolute path of the original sample location instead of the relative path within the project folder. When users moved projects or stored them in different locations, the paths became stale and wrong.

**Fix:** Updated `save_snapshot()` in `store.py` to try multiple resolution strategies:
1. Path as-stored from .als
2. Path relative to project root
3. Filename-only `rglob` search within the project folder (last resort)

The `rglob` fallback successfully finds the actual samples in `~/Clavus/Projects/Me And You/Samples/Imported/` even when the .als stored an incorrect path.

---

## 4. Progress Callback Reporting Wrong Totals

**Symptom:** During `pull_snapshot_blobs`, the header progress would show `sample: 0/X` — the total was always 0 even when X samples were being downloaded.

**Root cause:** In `sync.py`, the `_report()` callback was defined as:
```python
def _report(category: str, done: int):
    if progress_callback:
        progress_callback(category, done, counters[category])
```
`counters[category]` tracks *completed* downloads and was always `0` at the time `_report` was called (before any downloads started). It should have been passing the actual work count.

**Fix:** Compute `cat_totals = {len(content_work), len(als_work), len(sample_work)}` *before* the download loop, then pass `cat_totals[category]` as the third argument to `_report()` instead of `counters[category]`.

---

## 5. Intermittent ListView Bug (Unresolved)

**Symptom:** Cue list would occasionally disappear from the TUI after returning from a modal (e.g., project picker). Cues were confirmed to exist on disk — the ListView simply wouldn't render them.

**Status:** Not reproducible reliably. Possible causes:
- Stale fingerprint cache across sessions
- Race condition in Textual event loop
- `_cue_fingerprint = None` not being triggered in some code paths

---

## Summary of Fixes Applied

| File | Issue | Fix |
|------|-------|-----|
| `clavus/parser.py` | Live 10 `RelativePathElement` format not parsed | Added second parse path for Live 10 format |
| `clavus/parser.py` | Split on `"<SampleRef>"` instead of `"<SampleRef"` | Fixed split string |
| `clavus/parser.py` | `Dir` attribute not matched due to preceding `Id` attr | Fixed regex to `Dir="[^"]+"` |
| `clavus/store.py` | Broken absolute paths from Live 10 not resolvable | Added `rglob` filename fallback in `save_snapshot` |
| `clavus/sync.py` | Progress total always 0 | Pass `cat_totals[category]` to `_report()` instead of `counters[category]` |
| `clavus/tui.py` | `:push!` not documented in help | Added to COMMANDS section |
| `clavus/tui.py` | Help screen missing `:remotes` command | Added to COMMANDS section |

---

## Related Commits

- `88f8a7a` — fix: Live 10 sample parsing, path resolution, progress totals, help docs
- `f2b43cf` — fix: materialize samples to Samples/ subfolder, not project root
- `3206a26` — fix: solo mode — local-only entry in :remotes picker
- `a41299d` — fix: add Projects/ to gitignore + remove from repo