"""Test the .als parser against real Ableton projects.

Skips gracefully if LaCie drive is not mounted. Not run in CI by default."""
import os
from pathlib import Path

from clavus.parser import parse_als, project_summary

base = "/Volumes/LaCie/Ableton Live Projects (Local Drive)/Ableton Live Projects (Local Drive)"

if not Path("/Volumes/LaCie").exists():
    print("⚠️ LaCie drive not mounted — skipping real .als tests.")
    print("   Mount /Volumes/LaCie and re-run to test against real projects.\n")
    exit(0)

projects = [
    f"{base}/Space Race Project/Space Race.als",
    f"{base}/Me And You Project/Me And You.als",
    f"{base}/Bernard Wright Edit Project/Bernard Wright Edit.als",
]

found = 0
for path in projects:
    if not os.path.exists(path):
        print(f"⚠️ Skipping (not found): {path}")
        continue
    found += 1
    print(f"{'='*60}")
    try:
        proj = parse_als(path)
        print(project_summary(proj))
        print(f"   Return tracks: {len(proj.return_tracks)}")
        print(f"   Tempo events: {len(proj.tempo_events)}")

        # List all devices across all tracks
        all_devices = {}
        for t in proj.tracks:
            for d in t.devices:
                all_devices[d.device_type] = all_devices.get(d.device_type, 0) + 1
        if all_devices:
            print(f"   Device types: {all_devices}")

    except Exception as e:
        print(f"❌ {path}: {e}")
    print()

if found == 0:
    print("⚠️ No test projects found on LaCie.")
    print(f"   Expected them at: {base}")
