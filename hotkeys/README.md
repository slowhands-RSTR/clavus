# Clavus Keyboard Automation

Add timeline cues, take snapshots, and inject markers **without leaving your DAW**. No alt-tabbing, no context switching.

## How It Works

A hotkey layer sits between your keyboard and the Clavus server. Press a key, get a dialog box, type your note, done. The cue appears in the Clavus TUI and other collaborators see it in seconds.

```
┌──────────┐     ┌────────────────┐     ┌───────────────┐
│ Keyboard │────►│ Hammerspoon/AHK│────►│ Clavus Server │
│ ⌘⌥N      │     │ (system tray)  │     │ localhost:7890│
└──────────┘     └────────────────┘     └───────┬───────┘
                                                │
                                           ┌────▼────┐
                                           │ Ableton │
                                           │ .als    │
                                           └─────────┘
```

## Quick Reference

| Action | macOS | Windows | What It Does |
|--------|-------|---------|-------------|
| **Quick Cue** | `⌘⌥N` | `⊞ Alt N` | Pop a dialog to type cue text + position |
| **Cue w/ Track** | `⌘⌥⇧N` | `⊞ Alt Shift N` | Cue with an extra track name field |
| **Snapshot** | `⌘⌥S` | `⊞ Alt S` | Take a project snapshot |
| **Inject Markers** | `⌘⌥I` | `⊞ Alt I` | Write pending cues into the .als as Ableton locators |
| **List Cues** | `⌘⌥L` | `⊞ Alt L` | See recent unresolved cues as a notification |
| **Toggle TUI** | `⌘⌥T` | `⊞ Alt T` | Launch/focus the Clavus terminal UI |
| **Switch Project** | `⌘⌥P` | `⊞ Alt P` | See and switch between registered projects |

All key mappings are defined in **`bindings.json`** — the single source of truth. Both platforms read the same file.

## macOS Setup (Hammerspoon)

### 1. Install Hammerspoon

```bash
brew install --cask hammerspoon
```

Or download from [hammerspoon.org](https://www.hammerspoon.org/).

### 2. Enable Accessibility Permissions

The first time you launch Hammerspoon, macOS will ask for Accessibility access. Go to:
**System Settings → Privacy & Security → Accessibility** → toggle Hammerspoon ON.

### 3. Install the Config

```bash
# Symlink the Clavus config into Hammerspoon's config dir
mkdir -p ~/.hammerspoon
ln -sf ~/Developer/clavus/hotkeys/hammerspoon.lua ~/.hammerspoon/init.lua
```

Or copy it:
```bash
cp ~/Developer/clavus/hotkeys/hammerspoon.lua ~/.hammerspoon/init.lua
```

### 4. Restart Hammerspoon

Click the Hammerspoon menubar icon → **Reload Config**. You should see:

- A notification: "Clavus Ready — Keyboard automation loaded"
- A ♮ icon in the menu bar
- Alert: "Clavus: 8 hotkeys registered"

### 5. Verify

Press `⌘⌥L` to list cues. If you get "Could not reach Clavus server", start the server:

```bash
clavus serve
```

### Troubleshooting

| Problem | Fix |
|---------|-----|
| "bindings.json not found" | The symlink/copy may point to the wrong path. Edit the `config_path` variable at the top of `init.lua` |
| Hotkeys don't work | Check Accessibility permissions in System Settings |
| Server not reachable | Ensure `clavus serve` is running on port 7890 |

## Windows Setup (AutoHotkey)

### 1. Install AutoHotkey v2

Download from [autohotkey.com](https://www.autohotkey.com/) — get **v2.0+**.

### 2. Run the Script

```bash
# Direct run
.\clavus\hotkeys\autohotkey.ahk
```

Or compile to `.exe` for auto-start:
1. Right-click `autohotkey.ahk` → **Compile** (requires Ahk2Exe)
2. Place the `.exe` in `shell:startup`

### 3. Verify

You'll see a musical note icon in the system tray and a notification: "Clavus Ready — N hotkeys active".

## Customizing Bindings

All bindings are in **`hotkeys/bindings.json`**. Edit this file, then reload:

- **Hammerspoon:** Click ♮ menu icon → Reload Config
- **AutoHotkey:** Right-click tray icon → Reload This Script

```json
{
  "id": "cue_quick",
  "name": "Quick Cue",
  "mac_mods": ["cmd", "alt"],
  "mac_key": "N",
  "win_mods": ["win", "alt"],
  "win_key": "N",
  "action": "new_cue"
}
```

### Available Modifiers

| macOS | Windows |
|-------|---------|
| `cmd` | `win` |
| `alt` | `alt` |
| `shift` | `shift` |
| `ctrl` | `ctrl` |

### Available Actions

| Action | Description | Params |
|--------|-------------|--------|
| `new_cue` | Add a timeline cue | prompt_text, prompt_position, default_position, prompt_track |
| `snapshot` | Trigger project snapshot | prompt_message |
| `inject` | Write cues as Ableton markers | (none) |
| `list_cues` | Show recent cues | limit, filter |
| `toggle_tui` | Launch/focus terminal UI | (none) |
| `switch_project` | Pick a different project | (none) |

## Future: Playhead Integration

Right now positions are typed manually. Future versions will read Ableton's playhead position via:
- **macOS:** MIDI/Osculator or LiveOSC Python bridge
- **Windows:** Ableton's MIDI Remote Scripts API or M4L
- **Both:** A small script that polls Ableton's transport state

This will let you hit `⌘⌥N` and have the position auto-filled.
