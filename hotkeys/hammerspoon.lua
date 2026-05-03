-- Clavus Hotkeys — FINAL
-- Using Ctrl+Shift+letter — works inside Ableton

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

-- ─── Quick Cue (Ctrl+Shift+N) ─────────────────────────
hs.hotkey.bind({"ctrl", "shift"}, "N", function()
    hs.alert.show("Quick Cue activated")
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

-- ─── List Cues (Ctrl+Shift+L) ─────────────────────────
hs.hotkey.bind({"ctrl", "shift"}, "L", function()
    hs.alert.show("Listing cues...")
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

-- ─── Inject Markers (Ctrl+Shift+I) ────────────────────
hs.hotkey.bind({"ctrl", "shift"}, "I", function()
    hs.alert.show("Injecting markers...")
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

-- ─── Toggle TUI (Ctrl+Shift+T) ───────────────────────
hs.hotkey.bind({"ctrl", "shift"}, "T", function()
    hs.osascript.applescript([[
        tell application "Terminal"
            do script "cd ~/Developer/clavus && python3 -m clavus.tui"
            activate
        end tell
    ]])
end)

-- ─── Switch Project (Ctrl+Shift+P) ───────────────────
hs.hotkey.bind({"ctrl", "shift"}, "P", function()
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

-- ─── Where Am I? (Ctrl+Shift+W) ──────────────────────
hs.hotkey.bind({"ctrl", "shift"}, "W", function()
    notify("Position", "Playhead tracking coming soon.\nEnter manually in cue dialog.")
end)

-- ─── Menu bar ─────────────────────────────────────────
hs.menubar.new():setTitle("♮"):setToolTip("Clavus: Ctrl+Shift+N Cue  L List  I Inject  T TUI  P Project")

-- ─── Ready! ───────────────────────────────────────────
hs.alert.show("♮ Clavus: 6 hotkeys (Ctrl+Shift+letter)")
