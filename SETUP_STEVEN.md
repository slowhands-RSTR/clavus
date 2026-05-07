# Steven — Clavus Setup Checklist (Windows)

Here's everything you need to do, step by step.

---

## ☐ 1. Install Python

```cmd
winget install Python.Python.3.13
```

Or download from [python.org/downloads](https://www.python.org/downloads/) — **check "Add Python to PATH"** during install.

Verify:
```cmd
python --version
```
→ Should say `Python 3.13.x`

---

## ☐ 2. Install Git

```cmd
winget install Git.Git
```

Or from [git-scm.com](https://git-scm.com/).

Verify:
```cmd
git --version
```

---

## ☐ 3. Install Tailscale

Tailscale creates a secure private network between our machines. No port forwarding, no firewalls.

1. Go to [tailscale.com/download/windows](https://tailscale.com/download/windows)
2. Download and run the installer
3. Sign in with any email (Google, GitHub, Microsoft — doesn't matter)
4. **Find your Tailscale IP:**
   - Hover over the Tailscale icon in your system tray (bottom-right, grey whale)
   - Your IP shows as **100.x.x.x**
   - Or run: `tailscale ip -4`

**→ Send your 100.x.x.x IP to Chris**

---

## ☐ 4. Clone Clavus

```cmd
cd Desktop
git clone https://github.com/castle-queenside/clavus.git
cd clavus
pip install -e .
```

Verify:
```cmd
clavus --help
```
→ You should see a list of commands.

---

## ☐ 5. Connect to Chris

**Option A — Quick share (easiest):**

Chris will run `clavus share` and give you a share code like `BRIGHT-DUCK-7`.

Just run:
```cmd
clavus join
```
→ Auto-discovers Chris's relay, pulls the project, and configures the remote.

**Option B — Direct connection (if share doesn't work):**

Chris will give you his Tailscale IP. Run:
```cmd
clavus remote add chris http://100.126.94.21:7890
clavus pull
```

---

## ☐ 6. Open in Ableton

Pull the project first, then open it. Samples sync automatically with push/pull.

```cmd
clavus pull
```

The `.als` file is in `C:\Users\<you>\Clavus\Projects\`. Open it in Ableton Live. On first open, samples may show as offline — click any sample and Ableton will find them all.

---

## ☐ 7. Start the TUI

**This is the main way you'll use Clavus.** It's a terminal dashboard for managing comments (cues), snapshots, and sync.

```cmd
clavus tui
```

---

### TUI quickstart

When the TUI starts, you'll see two panels side-by-side:

| Left (Cues) | Right (History/Snapshots) |
|---|---|
| Threaded comments pinned to timeline positions | List of saved project versions |

**Navigate:**
- `Tab` — switch between the two panels
- `j` / `k` — move up/down in whichever panel has focus
- Arrow keys also work

### Keybinding reference

| Key | Action |
|-----|--------|
| `c` | **New cue** — add a comment pinned to a timeline position |
| `r` | **Reply** — reply to the selected cue |
| `e` | **Edit** — change the text of the selected cue |
| `a` | **Assign** — assign the cue to someone |
| `R` | **Resolve** — mark cue as resolved/done |
| `S` | **Start/stop** — toggle "in progress" on a cue |
| `x` | **Archive** — archive the cue |
| `!` | **Conflict** — resolve a sync conflict (keep yours or theirs) |
| `T` | **Restore** — restore the project to the selected snapshot |
| `d` | **Diff** — show what changed in the selected snapshot |
| `C` | **Snapshot** — save a new checkpoint |
| `p` | **Pull** — get latest from Chris |
| `P` | **Push** — send your changes to Chris |
| `:` | **Command mode** — type commands like `:project <name>` or `:snapshot <message>` |
| `q` | **Quit** — exit the TUI |

### Cue indicators

- **● Yellow** — pending (open)
- **✓ Green** — resolved (done)
- **▶ Yellow** — in progress (actively working on it)
- **– Grey** — skipped or archived
- **⚠ Yellow** — sync conflict (both people edited it)

### Sync conflicts

If you and Chris both edit the same cue, you'll see a ⚠ next to it. Navigate to it
and press `!` — a screen shows both versions side-by-side. Choose **Keep Mine**
or **Keep Theirs**.

---

### Sending changes back

When you've made edits in Ableton and saved:

```cmd
clavus snapshot "my first edit"
clavus push
```

Samples (audio files) sync automatically with push/pull — no separate step needed.

---

## Quick reference

| Command | What it does |
|---------|-------------|
| `clavus tui` | **Main interface** — terminal dashboard |
| `clavus relay` | Start server for collaboration |
| `clavus share` | Start share session with auto-discovery |
| `clavus join` | Find and connect to a share session |
| `clavus pull` | Get latest from remote |
| `clavus push` | Send your changes to remote |
| `clavus snapshot "msg"` | Save a checkpoint |
| `clavus restore <hash>` | Restore project from a snapshot |
| `clavus log` | See snapshot history |
| `clavus diff [hash]` | See what changed |
