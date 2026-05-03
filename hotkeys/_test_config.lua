-- Hammerspoon TEST CONFIG — Clavus hotkeys
-- Just the bare minimum to test if hotkeys work

-- Show an alert when config loads
hs.alert.show("♮ Clavus TEST config loaded!")

-- Test hotkey: Ctrl+Alt+L → show alert and notification
hs.hotkey.bind({"ctrl", "alt"}, "L", function()
    hs.alert.show("Ctrl+Alt+L WORKED!")
    hs.notify.new({
        title = "Clavus TEST",
        informativeText = "Hotkey detected! Ctrl+Alt+L is working.",
    }):send()
end)

-- Test hotkey: Ctrl+Alt+N → show a text input dialog
hs.hotkey.bind({"ctrl", "alt"}, "N", function()
    hs.dialog.textPrompt("Clavus TEST", "Type something:", "", "OK", "Cancel",
        function(text)
            if text then
                hs.alert.show("You typed: " .. text)
            end
        end)
end)

-- Show a menubar item so we know it's loaded
hs.menubar.new():setTitle("♮"):setToolTip("Clavus TEST config — Ctrl+Alt+L to test")
