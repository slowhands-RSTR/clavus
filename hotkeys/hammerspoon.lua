-- Clavus: Hammerspoon hotkeys (works outside Ableton)
-- Inside Ableton, most primitives are sandboxed.
-- These work great when Ableton is NOT the focused app.

-- Read config from ~/.config/clavus/config.json
local CONFIG_PATH = os.getenv("HOME") .. "/.config/clavus/config.json"
local function read_config()
    local f = io.open(CONFIG_PATH, "r")
    if not f then return nil end
    local content = f:read("*a")
    f:close()
    return content
end

local function json_str(json, key)
    if not json then return nil end
    local pattern = '"' .. key .. '"%s*:%s*"([^"]*)"'
    local _, _, val = json:find(pattern)
    return val
end

local function json_num(json, key)
    if not json then return nil end
    local pattern = '"' .. key .. '"%s*:%s*(%d+)'
    local _, _, val = json:find(pattern)
    if val then return tonumber(val) end
    return nil
end

local config_raw = read_config()
local CLAVUS_PORT = json_num(config_raw, "port") or 7890
local API = "http://127.0.0.1:" .. CLAVUS_PORT
local CACHED_PROJECT = ""

-- helpers --------------------------------------------------------------------

local function log(msg)
    local f = io.open("/tmp/clavus_hammerspoon.log", "a")
    if f then
        f:write(os.date("%H:%M:%S") .. " " .. tostring(msg) .. "\n")
        f:close()
    end
end

log("=== Config loaded ===")

local function json_str(json, key)
    if not json then return nil end
    local pattern = '"' .. key .. '"%s*:%s*"([^"]*)"'
    local _, _, val = json:find(pattern)
    return val
end

local function api_get(endpoint)
    local cmd = "curl -s --max-time 3 " .. API .. endpoint
    local f = io.popen(cmd)
    if not f then return nil end
    local r = f:read("*a")
    f:close()
    return r
end

local function api_post(endpoint, body)
    local escaped = body:gsub("'", "'\"'\"'")
    local cmd = "curl -s --max-time 3 -X POST -H 'Content-Type: application/json' -d '" .. escaped .. "' " .. API .. endpoint
    local f = io.popen(cmd)
    if not f then return nil end
    local r = f:read("*a")
    f:close()
    return r
end

local function url_enc(name)
    return name:gsub(" ", "%%20")
end

local function get_project()
    if CACHED_PROJECT and CACHED_PROJECT ~= "" then
        return CACHED_PROJECT
    end
    local resp = api_get("/api/project")
    if resp then
        local name = json_str(resp, "name")
        if name and name ~= "" then
            CACHED_PROJECT = name
            log("Cached project: " .. name)
            return name
        end
    end
    resp = api_get("/api/projects")
    if resp then
        local name = json_str(resp, "name")
        if name and name ~= "" then
            CACHED_PROJECT = name
            return name
        end
    end
    return nil
end

-- hotkeys --------------------------------------------------------------------

-- F: New cue (dialog prompt)
hs.hotkey.bind({"ctrl", "shift"}, "F", function()
    local proj = get_project()
    if not proj then
        hs.alert.show("No Clavus project")
        return
    end
    local ok, text = hs.dialog.textPrompt(proj, "Enter cue text:", "", "Create", "Cancel")
    if not ok or not text or text == "" then
        hs.alert.show("Cancelled")
        return
    end
    local escaped = text:gsub('\\', '\\\\'):gsub('"', '\\"')
    local body = '{"text":"' .. escaped .. '","project_name":"' .. proj .. '"}'
    local resp = api_post("/api/cues", body)
    if resp then
        local id = json_str(resp, "id") or "?"
        hs.alert.show("Cue " .. id .. " saved")
    else
        hs.alert.show("Save failed")
    end
end)

-- G: List pending cues (notification)
hs.hotkey.bind({"ctrl", "shift"}, "G", function()
    local proj = get_project()
    if not proj then
        hs.alert.show("No Clavus project")
        return
    end
    local resp = api_get("/api/cues?name=" .. url_enc(proj) .. "&pending_only=true")
    if resp then
        local _, n = resp:gsub('"status":"pending"', '"status":"pending"')
        local display = (n > 0) and (n .. " pending cues") or "No pending cues"
        local note = hs.notify.new()
        note:title("Clavus: " .. proj)
        note:informativeText(display)
        note:send()
        hs.alert.show(display)
    else
        hs.alert.show("Fetch failed")
    end
end)

-- N: New cue (same as F)
hs.hotkey.bind({"ctrl", "shift"}, "N", function()
    hs.hotkey.bind({"ctrl", "shift"}, "F", function() end) -- no-op, just showing F
    local proj = get_project()
    if not proj then
        hs.alert.show("No Clavus project")
        return
    end
    local ok, text = hs.dialog.textPrompt(proj, "Enter cue text:", "", "Create", "Cancel")
    if not ok or not text or text == "" then
        hs.alert.show("Cancelled")
        return
    end
    local escaped = text:gsub('\\', '\\\\'):gsub('"', '\\"')
    local body = '{"text":"' .. escaped .. '","project_name":"' .. proj .. '"}'
    local resp = api_post("/api/cues", body)
    if resp then
        local id = json_str(resp, "id") or "?"
        hs.alert.show("Cue " .. id .. " saved")
    else
        hs.alert.show("Save failed")
    end
end)

-- J: Inject cues into .als
hs.hotkey.bind({"ctrl", "shift"}, "J", function()
    local proj = get_project()
    if not proj then
        hs.alert.show("No Clavus project")
        return
    end
    local resp = api_post("/api/projects/inject?name=" .. url_enc(proj), "{}")
    if resp then
        local injected = json_str(resp, "injected")
        if injected and injected ~= "" then
            hs.alert.show("Injected " .. injected .. " markers")
        else
            local msg = json_str(resp, "message") or json_str(resp, "error") or "Done"
            hs.alert.show(msg)
        end
    else
        hs.alert.show("Inject failed")
    end
end)

-- H: Help
hs.hotkey.bind({"ctrl", "shift"}, "H", function()
    local proj = get_project() or "(none)"
    local note = hs.notify.new()
    note:title("Clavus Hotkeys")
    note:informativeText("F - New cue (dialog)\nG - Pending cue count\nN - New cue\nJ - Inject markers into .als\nH - This help\n\nProject: " .. proj)
    note:send()
    hs.alert.show("Clavus ready — " .. proj)
end)

log("Hotkeys bound. Project: " .. (CACHED_PROJECT or "auto-detect"))
hs.alert.show("Clavus ready: Ctrl+Shift F/G/N/J/H")
