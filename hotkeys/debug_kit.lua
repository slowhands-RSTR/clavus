-- Clavus Hotkey Debug Kit (v2 — one alert per test)
-- Each Ctrl+Shift+letter tests ONE thing

hs.hotkey.bind({"ctrl", "shift"}, "Q", function()
    local ok, out = pcall(function()
        return hs.execute("echo 'q test'")
    end)
    hs.alert.show("Q: execute? " .. tostring(ok))
end)

hs.hotkey.bind({"ctrl", "shift"}, "W", function()
    local ok, out = pcall(function()
        local f = io.popen("echo 'w test'")
        if f then
            local r = f:read("*a")
            f:close()
            return r
        end
        return "popen nil"
    end)
    hs.alert.show("W: popen? " .. tostring(ok))
end)

hs.hotkey.bind({"ctrl", "shift"}, "E", function()
    local ok, msg = pcall(function()
        local f = io.open("/tmp/clavus_debug.txt", "w")
        if f then
            f:write("e test\n")
            f:close()
            return "wrote file"
        end
        return "file nil"
    end)
    hs.alert.show("E: io.open(w)? " .. tostring(ok))
end)

hs.hotkey.bind({"ctrl", "shift"}, "R", function()
    local ok, n = pcall(function()
        local note = hs.notify.new()
        note:title("Clavus Debug")
        note:informativeText("R hotkey fired")
        note:send()
        return "notified"
    end)
    hs.alert.show("R: notify? " .. tostring(ok))
end)

hs.hotkey.bind({"ctrl", "shift"}, "T", function()
    local ok, msg = pcall(function()
        local skt = require("hs.socket")
        return "socket loaded"
    end)
    hs.alert.show("T: socket? " .. tostring(ok))
end)

hs.hotkey.bind({"ctrl", "shift"}, "Y", function()
    local ok, msg = pcall(function()
        return hs.osascript.applescript('return "y test"')
    end)
    hs.alert.show("Y: osascript? " .. tostring(ok))
end)

hs.hotkey.bind({"ctrl", "shift"}, "U", function()
    local ok, msg = pcall(function()
        return hs.fs.write("/tmp/clavus_debug.txt", "u test")
    end)
    hs.alert.show("U: fs.write? " .. tostring(ok))
end)

hs.hotkey.bind({"ctrl", "shift"}, "I", function()
    local ok, msg = pcall(function()
        local f = io.open("/tmp/clavus_debug.txt", "r")
        if f then
            local c = f:read("*a")
            f:close()
            return "read: " .. c
        end
        return "file nil"
    end)
    hs.alert.show("I: io.open(r)? " .. tostring(ok))
end)

hs.alert.show("🔍 CLAVUS DEBUG KIT READY — hit Q/W/E/R/T/Y/U/I")
