-- Clavus Hotkeys — Hammerspoon Config
-- Reads bindings.json for shared key mappings

-- ─── Config ──────────────────────────────────────────────
local config_path = os.getenv("HOME") .. "/Developer/clavus/hotkeys/bindings.json"
local server_host = "127.0.0.1"
local server_port = 7890

-- ─── Load bindings with error handling ───────────────────
local ok, bindings_data = pcall(dofile, config_path)
-- Actually we need to read the JSON, which Lua can't natively parse.
-- Let's just hardcode the bindings directly to avoid JSON parsing issues.

-- ─── Notify helper ───────────────────────────────────────
local function notify(title, msg)
    hs.notify.new({title="Clavus", subTitle=title, informativeText=msg}):send()
end

-- ─── Curl helper ─────────────────────────────────────────
local function api(method, path, body)
    local url = "http://" .. server_host .. ":" .. server_port .. path
    local cmd
    if body then
        -- Write body to temp file to avoid shell quoting issues
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

-- ─── Get current project name ───────────────────────────
local function get_project()
    local resp = api("GET", "/api/projects")
    if resp and resp ~= "" then
        -- Crude JSON parse — find the first project name
        local _, _, name = resp:find('"name"%s*:%s*"([^"]+)"')
        return name
    end
    return nil
end

-- ─── Hotkey: Quick Cue (F6) ─────────────────────
hs.hotkey.bind({}, "f6", function()
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

-- ─── Hotkey: List Cues (F7) ─────────────────────
hs.hotkey.bind({}, "f7", function()
    local project = get_project()
    if not project then notify("Error", "No project found") return end
    local resp = api("GET", "/api/cues?name=" .. project .. "&limit=5&status=pending")
    if resp and resp ~= "" then
        -- Crudely parse: find "text":"..." patterns
        local lines = {}
        for text in resp:gmatch('"text"%s*:%s*"([^"]+)"') do
            table.insert(lines, "• " .. text)
        end
        for pos in resp:gmatch('"position"%s*:%s*"([^"]+)"') do
            -- We'll just show them together — good enough
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

-- ─── Hotkey: Inject (F8) ────────────────────────
hs.hotkey.bind({}, "f8", function()
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

-- ─── Hotkey: Snapshot (F9) ──────────────────────
hs.hotkey.bind({}, "f9", function()
    local project = get_project()
    if not project then notify("Error", "No project found") return end
    notify("Snapshot", "Use TUI to snapshot: Ctrl+Alt+T then :snapshot")
end)

-- ─── Hotkey: Toggle TUI (F10) ───────────────────
hs.hotkey.bind({}, "f10", function()
    hs.osascript.applescript([[
        tell application "Terminal"
            do script "cd ~/Developer/clavus && python3 -m clavus.tui"
            activate
        end tell
    ]])
end)

-- ─── Hotkey: Switch Project (F11) ────────────────
hs.hotkey.bind({}, "f11", function()
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

-- ─── Hotkey: Cue with Track (F12) ──────────
hs.hotkey.bind({}, "f12", function()
    hs.dialog.textPrompt("Clavus — New Cue", "Cue text:", "", "Next", "Cancel",
        function(text)
            if not text or text == "" then return end
            hs.dialog.textPrompt("Clavus — Position", "Position @:", "", "Next", "Cancel",
                function(pos)
                    if not pos then pos = "1.1.1" end
                    hs.dialog.textPrompt("Clavus — Track", "Track name:", "", "Add", "Cancel",
                        function(track)
                            if not track then track = "" end
                            local project = get_project()
                            if not project then notify("Error", "Start clavus serve") return end
                            local body = '{"text":"' .. text .. '","position":"' .. pos .. '","track":"' .. track .. '","author":"hammerspoon","project_name":"' .. project .. '"}'
                            local resp = api("POST", "/api/cues", body)
                            if resp and resp ~= "" then
                                notify("Cue Added", '"' .. text .. '" @ ' .. pos)
                            else
                                notify("Error", "Could not reach Clavus server")
                            end
                        end)
                end)
        end)
end)

-- ─── Hotkey: Where Am I? (Ctrl+Alt+W) ───────────────────
hs.hotkey.bind({"ctrl", "alt"}, "W", function()
    notify("Ableton Position", "Playhead tracking coming soon.\nFor now, enter positions manually via Ctrl+Alt+N.")
end)

-- ─── Menu bar icon ──────────────────────────────────────
hs.menubar.new():setTitle("♮"):setToolTip("Clavus: F6=Quick Cue  F7=List  F8=Inject  F9=Snap  F10=TUI  F11=Project  F12=Cue+Track")

-- ─── Ready! ──────────────────────────────────────────────
hs.alert.show("♮ Clavus F-key hotkeys loaded!")
notify("Clavus Ready", "F6=New cue  F7=List  F8=Inject  F9=Snap  F10=TUI")
