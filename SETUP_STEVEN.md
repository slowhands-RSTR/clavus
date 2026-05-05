# Clavus Setup for Steven (Windows)

## 1. Install Python

1. Go to https://www.python.org/downloads/
2. Download Python 3.11 or 3.12 (the latest)
3. **Check "Add Python to PATH"** during install
4. Open **Command Prompt** and type:
   ```
   python --version
   ```
   Should say `Python 3.11.x` or similar

## 2. Install Clavus

In Command Prompt:
```
pip install clavus
```

To verify:
```
clavus --help
```
You should see a list of commands.

## 3. Install Tailscale

1. Go to https://tailscale.com/download
2. Install and sign in with whatever email you use
3. You'll see a "100.x.x.x" Tailscale IP — text that to Chris

## 4. Connect to Chris's project

Chris shares his Tailscale IP. In Command Prompt:

```
clavus remote add chris http://100.x.x.x:7890
```

Pull everything:
```
clavus pull chris
clavus stem pull chris
```

## 5. Open in Ableton

The `.als` file will be in whatever directory you ran the commands from. All tracks should be audio — no missing plugins. Chris will have frozen/bounced everything ahead of time on his end.

## 6. Send changes back

When you've made edits:

```
clavus snapshot "your message here"
clavus stem import --track "TrackName" path/to/your/bounce.wav
clavus push chris
```

## Cliff notes for Chris

- Tailscale gives you a private network — no port forwarding, no firewall config
- Steven only needs Python + `pip install clavus` + Tailscale
- Everything is content-addressed — only new data transfers
- Visual diff: `clavus diff --visual` shows what changed in the arrangement
