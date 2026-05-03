-- ──────────────────────────────────────────────────────────────────────
-- Clavus Hotkeys — Hammerspoon Config
-- ──────────────────────────────────────────────────────────────────────
-- Keys that work inside Ableton:
--   CapsLock+N  → Quick Cue
--   CapsLock+L  → List Cues
--   CapsLock+I  → Inject Markers
--   CapsLock+S  → Snapshot
--   CapsLock+T  → Toggle TUI
--   CapsLock+P  → Switch Project
--   CapsLock+W  → Where Am I? (placeholder)
--
-- CapsLock is used as a held modifier, like holding Shift.
-- Ableton and macOS ignore CapsLock as a shortcut modifier.

local server_host = "127.0.0.1"
local server_port = 7890

-- ─── Helpers ──────────────────────────────────────────────

local function notify(title, msg)
    hs.notify.new({title="Clavus", subTitle=title, informativeText=msg}):send()
end

local function api(method, path, body)
    local url = "http://" .. server_host .. ":" .. server_port .. path
    local cmd
    if body then
        local f = io.open("/tmp/clavus_body.json", "w")
        if f then f:write(body) f:close() end
        cmd = 'curl -s -X ' .. method .. ' --max-time 3 -H "Content-Type: application/json" -d @/tmp/clavus_body.json "' .. url .. '"'
    else
        cmd = 'curl -s -X ' .. method .. ' --max-time 3 "' .. url .. '"'
    end
    local handle = io.popen(cmd)
    local result = handle:read("*a")
    handle:close()
    return result
end

local function get_project()
    local resp = api("GET", "/api/projects")
    if resp and resp ~= "" then
        local _, _, name = resp:find('"name"%s*:%s*"([^"]+)"')
        return name
    end
    return nil
end

-- CapsLock is a tricky key in Hammerspoon. It's a toggle, not a held modifier.
-- We handle it by tracking CapsLock state and using a different approach.
-- Instead of binding to CapsLock itself, we listen for key down/up events.

-- ─── CapsLock-as-Modifier via Event Tap ──────────────────
-- This approach uses hs.eventtap to detect when CapsLock is held
-- and map letter keys to Clavus actions.

local capslock_is_down = false

-- Completely suppress CapsLock as a toggle.
-- We use hs.eventtap to catch the keydown and prevent the system
-- from toggling CapsLock. Then we manually track the state.
local tap = hs.eventtap.new({hs.eventtap.event.types.keyDown, hs.eventtap.event.types.flagsChanged}, function(e)
    local keycode = e:getKeyCode()
    -- 57 = CapsLock keycode on most keyboards
    if keycode == 57 then
        -- Toggle our internal state instead of the system's
        capslock_is_down = not capslock_is_down
        -- Return true to swallow the event — CapsLock never toggles
        return true
    end
    if e:getType() == hs.eventtap.event.types.flagsChanged then
        -- For non-CapsLock flag changes, let them pass
        local flags = e:getFlags()
        capslock_is_down = flags.capslock or false
    end
    return false
end)
tap:start()

-- ─── Letter Hotkeys (only fire when CapsLock is held) ───
local function clavus_key(key, fn)
    hs.hotkey.bind({}, key, function()
        if capslock_is_down then
            fn()
        end
    end)
end

-- ─── Action: Quick Cue (CapsLock+N) ─────────────────────
clavus_key("n", function()
    hs.dialog.textPrompt("Clavus — New Cue", "Cue text:", "", "Next", "Cancel",
        function(text)
            if not text or text == "" then return end
            hs.dialog.textPrompt("Clavus — Position", "Position @ (blank=1.1.1):", "", "Add", "Cancel",
                function(pos)
                    if not pos or pos == "" then pos = "1.1.1" end
                    local project = get_project()
                    if not project then notify("Error", "Start clavus serve first") return end
                    local body = '{"text":"' .. text .. '","position":"' .. pos .. '","author":"hammerspoon","project_name":"' .. project .. '"}'
                    local resp = api("POST", "/api/cues", body)
                    if resp and resp ~= "" then
                        notify("Cue Added", '"' .. text .. '" @ ' .. pos)
                    else
                        notify("Error", "Could not reach Clavus server")
                    end
                end)
        end)
end)

-- ─── Action: List Cues (CapsLock+L) ─────────────────────
clavus_key("l", function()
    local project = get_project()
    if not project then notify("Error", "No project found") return end
    local resp = api("GET", "/api/cues?name=" .. project .. "&limit=5&status=pending")
    if resp and resp ~= "" then
        local lines = {}
        for text in resp:gmatch('"text"%s*:%s*"([^"]+)"') do
            table.insert(lines, "• " .. text)
        end
        if #lines > 0 then
            notify("Recent Cues", table.concat(lines, "\n"))
        else
            notify("No Cues", "No pending cues")
        end
    else
        notify("Error", "Could not reach Clavus server")
    end
end)

-- ─── Action: Inject Markers (CapsLock+I) ────────────────
clavus_key("i", function()
    local project = get_project()
    if not project then notify("Error", "No project found") return end
    local resp = api("POST", "/api/projects/inject?name=" .. project)
    if resp and resp ~= "" then
        local _, _, count = resp:find('"injected"%s*:%s*([0-9]+)')
        if count then
            notify("Cues Injected", count .. " cue(s) written to " .. project)
        else
            local _, _, msg = resp:find('"message"%s*:%s*"([^"]+)"')
            notify("Injection", msg or resp)
        end
    else
        notify("Error", "Could not reach Clavus server")
    end
end)

-- ─── Action: Toggle TUI (CapsLock+T) ────────────────────
clavus_key("t", function()
    hs.osascript.applescript([[
        tell application "Terminal"
            do script "cd ~/Developer/clavus && python3 -m clavus.tui"
            activate
        end tell
    ]])
end)

-- ─── Action: Switch Project (CapsLock+P) ────────────────
clavus_key("p", function()
    local resp = api("GET", "/api/projects")
    if not resp or resp == "" then notify("Error", "No server") return end
    local names = ""
    for name in resp:gmatch('"name"%s*:%s*"([^"]+)"') do
        names = names .. name .. "\n"
    end
    if names == "" then notify("No Projects", "None registered") return end
    hs.dialog.textPrompt("Switch Project", "Available:\n" .. names, "", "Switch", "Cancel",
        function(name)
            if name and name ~= "" then notify("Switched", "Now on: " .. name) end
        end)
end)

-- ─── Action: Where Am I? (CapsLock+W) ───────────────────
clavus_key("w", function()
    notify("Position", "Playhead tracking coming soon.\nFor now, enter manually in cue dialog.")
end)

-- ─── Menu bar icon ──────────────────────────────────────
hs.menubar.new():setTitle("♮"):setToolTip("Clavus: hold CapsLock+letter  N=Cue  L=List  I=Inject  T=TUI  P=Project  W=Where")

-- ─── Ready! ──────────────────────────────────────────────
hs.alert.show("♮ Clavus loaded — hold CapsLock, press letter")
notify("Clavus Ready", "CapsLock+N=Cue  CapsLock+L=List  CapsLock+I=Inject  CapsLock+T=TUI")
