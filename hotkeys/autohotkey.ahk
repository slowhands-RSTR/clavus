; ───────────────────────────────────────────────────────────────────────
; clavus/hotkeys/autohotkey.ahk
; ───────────────────────────────────────────────────────────────────────
; AutoHotkey v2 script for Clavus keyboard automation (Windows).
; Reads bindings.json at startup so key mappings are shared between
; macOS (Hammerspoon) and Windows (AutoHotkey).
;
; REQUIREMENTS:
;   - AutoHotkey v2.0+ (https://www.autohotkey.com)
;   - curl.exe (ships with Windows 10/11 or from Git for Windows)
;   - Python 3.10+ (for TUI)
;
; INSTALLATION:
;   1. Install AutoHotkey v2
;   2. Right-click this file → Run Script
;   3. Or compile to .exe to auto-start with Windows
; ───────────────────────────────────────────────────────────────────────

#Requires AutoHotkey >=2.0
#SingleInstance Force

; ─── Config ──────────────────────────────────────────────────────────
CLAVUS_DIR := A_MyDocuments . "\Developer\clavus"
BINDINGS_FILE := CLAVUS_DIR . "\hotkeys\bindings.json"
SERVER_HOST := "127.0.0.1"
SERVER_PORT := 7890
TIMEOUT_MS := 3000

TraySetIcon("shell32.dll", 186)  ; musical note icon in system tray
A_IconTip := "Clavus Hotkeys (Windows)"

; ─── Load bindings.json ──────────────────────────────────────────────
Bindings := Map()
ServerConfig := Map()

if FileExist(BINDINGS_FILE) {
    try {
        raw := FileRead(BINDINGS_FILE)
        parsed := JSON.Parse(raw)

        if parsed.Has("server") {
            s := parsed["server"]
            if s.Has("host") and s["host"] != "" {
                SERVER_HOST := s["host"]
            }
            if s.Has("port") and s["port"] != "" {
                SERVER_PORT := s["port"]
            }
            if s.Has("timeout_ms") and s["timeout_ms"] != "" {
                TIMEOUT_MS := s["timeout_ms"]
            }
        }

        if parsed.Has("bindings") {
            for b in parsed["bindings"] {
                Bindings[b["id"]] := b
            }
        }
    } catch as e {
        TrayTip("⚠️ Clavus", "Failed to parse bindings.json: " . e.Message, "Error")
    }
} else {
    TrayTip("⚠️ Clavus", "bindings.json not found at " . BINDINGS_FILE, "Error")
}

; ─── Utility Functions ────────────────────────────────────────────────

ClavusAPI(method, path, body := "") {
    url := "http://" . SERVER_HOST . ":" . SERVER_PORT . path
    cmd := 'curl.exe -s -X ' . method . ' --max-time ' . (TIMEOUT_MS // 1000) . ' "' . url . '"'

    if body != "" {
        tmpFile := A_Temp . "\clavus_body.json"
        try FileDelete(tmpFile)
        FileAppend(body, tmpFile)
        cmd := 'curl.exe -s -X ' . method . ' --max-time ' . (TIMEOUT_MS // 1000) _
             . ' -H "Content-Type: application/json" -d @' . tmpFile . ' "' . url . '"'
    }

    try {
        return ComObject("WScript.Shell").Exec(A_ComSpec . " /c " . cmd).StdOut.ReadAll()
    } catch {
        return ""
    }
}

GetCurrentProject() {
    resp := ClavusAPI("GET", "/api/projects")
    if resp != "" {
        try {
            data := JSON.Parse(resp)
            if data.Length > 0 and data[0].Has("name") {
                return data[0]["name"]
            }
        }
    }
    return ""
}

Notify(title, message) {
    TrayTip(title, message, "Info", 5)
}

; JSON parser (minimal, handles our use case)
class JSON {
    static Parse(text, pos := 1) {
        ; Skip whitespace
        while pos <= StrLen(text) and SubStr(text, pos, 1) ~= "[ \t\r\n]" {
            pos++
        }
        if pos > StrLen(text) {
            return ""
        }

        char := SubStr(text, pos, 1)

        if char = "{" {
            return this.ParseObject(text, pos)
        } else if char = "[" {
            return this.ParseArray(text, pos)
        } else if char = `" {
            return this.ParseString(text, pos)
        } else if char = "t" or char = "f" {
            return this.ParseBool(text, pos)
        } else if char = "n" {
            pos += 4  ; "null"
            return ""
        } else {
            return this.ParseNumber(text, pos)
        }
    }

    static ParseObject(text, &pos) {
        obj := Map()
        pos++  ; skip {
        loop {
            while pos <= StrLen(text) and SubStr(text, pos, 1) ~= "[ \t\r\n]" {
                pos++
            }
            if SubStr(text, pos, 1) = "}" {
                pos++
                return obj
            }
            if pos > StrLen(text) {
                return obj
            }

            key := this.ParseString(text, pos)
            while pos <= StrLen(text) and SubStr(text, pos, 1) ~= "[ \t\r\n]" {
                pos++
            }
            pos++  ; skip :
            val := this.Parse(text, pos)
            obj[key] := val

            while pos <= StrLen(text) and SubStr(text, pos, 1) ~= "[ \t\r\n]" {
                pos++
            }
            if SubStr(text, pos, 1) = "," {
                pos++
            } else if SubStr(text, pos, 1) = "}" {
                pos++
                return obj
            }
        }
        return obj
    }

    static ParseArray(text, &pos) {
        arr := []
        pos++  ; skip [
        loop {
            while pos <= StrLen(text) and SubStr(text, pos, 1) ~= "[ \t\r\n]" {
                pos++
            }
            if SubStr(text, pos, 1) = "]" {
                pos++
                return arr
            }
            if pos > StrLen(text) {
                return arr
            }

            arr.Push(this.Parse(text, pos))

            while pos <= StrLen(text) and SubStr(text, pos, 1) ~= "[ \t\r\n]" {
                pos++
            }
            if SubStr(text, pos, 1) = "," {
                pos++
            } else if SubStr(text, pos, 1) = "]" {
                pos++
                return arr
            }
        }
        return arr
    }

    static ParseString(text, &pos) {
        pos++  ; skip opening quote
        start := pos
        while pos <= StrLen(text) {
            ch := SubStr(text, pos, 1)
            if ch = `" {
                result := SubStr(text, start, pos - start)
                pos++
                return result
            }
            if ch = "\" {
                pos += 2
            } else {
                pos++
            }
        }
        return SubStr(text, start)
    }

    static ParseNumber(text, &pos) {
        start := pos
        if SubStr(text, pos, 1) = "-" {
            pos++
        }
        while pos <= StrLen(text) and SubStr(text, pos, 1) ~= "[0-9]" {
            pos++
        }
        if SubStr(text, pos, 1) = "." {
            pos++
            while pos <= StrLen(text) and SubStr(text, pos, 1) ~= "[0-9]" {
                pos++
            }
        }
        numStr := SubStr(text, start, pos - start)
        if InStr(numStr, ".") {
            return Float(numStr)
        }
        return Integer(numStr)
    }

    static ParseBool(text, &pos) {
        if SubStr(text, pos, 4) = "true" {
            pos += 4
            return true
        }
        if SubStr(text, pos, 5) = "false" {
            pos += 5
            return false
        }
        pos += 5
        return false
    }
}

; ─── Action Implementations ──────────────────────────────────────────

NewCue(params) {
    ; Ask for cue text via input box
    result := InputBox("Cue text:", "Clavus — New Cue")
    if result.Result = "Cancel" {
        Notify("Cancelled", "No cue added")
        return
    }
    text := result.Value
    if text = "" {
        return
    }

    ; Ask for position
    defaultPos := params.Has("default_position") ? params["default_position"] : ""
    result := InputBox("Position @ (blank=1.1.1):", "Clavus — Cue Position", "w300", defaultPos)
    if result.Result = "Cancel" {
        return
    }
    position := result.Value
    if position = "" {
        position := "1.1.1"
    }

    ; Ask for track if configured
    track := ""
    if params.Has("prompt_track") {
        result := InputBox("Track name (optional):", "Clavus — Track", "w300")
        if result.Result = "Cancel" {
            return
        }
        track := result.Value
    }

    project := GetCurrentProject()
    if project = "" {
        Notify("Error", "No Clavus project found. Start clavus serve first.")
        return
    }

    body := '{"text":"' . EscapeJSON(text) . '","position":"' . EscapeJSON(position) _
          . '","track":"' . EscapeJSON(track) . '","author":"autohotkey","project_name":"' _
          . EscapeJSON(project) . '"}'

    resp := ClavusAPI("POST", "/api/cues", body)
    if resp != "" {
        Notify("Cue Added", '"' . text . '" @ ' . position . ' — ' . project)
    } else {
        Notify("Error", "Could not reach Clavus server at :7890")
    }
}

EscapeJSON(str) {
    str := StrReplace(str, "\", "\\")
    str := StrReplace(str, `"`, '\"')
    str := StrReplace(str, "`n", "\n")
    str := StrReplace(str, "`r", "\r")
    str := StrReplace(str, "`t", "\t")
    return str
}

DoSnapshot(params) {
    project := GetCurrentProject()
    if project = "" {
        Notify("Error", "No Clavus project found")
        return
    }

    result := InputBox("Snapshot description (optional):", "Clavus — Snapshot", "w400")
    if result.Result = "Cancel" {
        return
    }
    msg := result.Value
    if msg = "" {
        msg := "Snapshot via hotkey"
    }
    Notify("Snapshot Triggered", project . " — " . msg)
}

DoInject() {
    project := GetCurrentProject()
    if project = "" {
        Notify("Error", "No Clavus project found")
        return
    }

    resp := ClavusAPI("POST", "/api/projects/inject?name=" . UrlEncode(project))
    if resp != "" {
        try {
            data := JSON.Parse(resp)
            if data.Has("injected") {
                Notify("Cues Injected", data["injected"] . " cue(s) written to " . project)
            } else if data.Has("message") {
                Notify("Injection", data["message"])
            } else {
                Notify("Response", resp)
            }
        } catch {
            Notify("Response", resp)
        }
    } else {
        Notify("Error", "Could not reach Clavus server")
    }
}

ListCues(params) {
    limit := params.Has("limit") ? params["limit"] : 5
    project := GetCurrentProject()
    if project = "" {
        Notify("Error", "No Clavus project found")
        return
    }

    filter := ""
    if params.Has("filter") and params["filter"] = "unresolved" {
        filter := "&status=pending"
    }

    resp := ClavusAPI("GET", "/api/cues?name=" . UrlEncode(project) . "&limit=" . limit . filter)
    if resp != "" {
        try {
            data := JSON.Parse(resp)
            if data.Length > 0 {
                lines := ""
                for i, cue in data {
                    pos := cue.Has("position") ? cue["position"] : "?"
                    txt := cue.Has("text") ? cue["text"] : "?"
                    lines .= "📍 " . pos . " — " . txt . "`n"
                }
                Notify("Recent Cues — " . project, RTrim(lines, "`n"))
            } else {
                Notify("No Cues", "No pending cues for " . project)
            }
        } catch {
            Notify("Error", "Unexpected response")
        }
    } else {
        Notify("Error", "Could not reach Clavus server")
    }
}

ToggleTUI(params) {
    try {
        Run('cmd.exe /c start "Clavus TUI" wt.exe -d "' . CLAVUS_DIR . '" python3 -m clavus.tui')
    } catch {
        try {
            Run('cmd.exe /c start "Clavus TUI" python3 "' . CLAVUS_DIR . '\clavus\tui.py"')
        } catch {
            Notify("Error", "Could not launch TUI. Is Python in your PATH?")
        }
    }
}

SwitchProject(params) {
    resp := ClavusAPI("GET", "/api/projects")
    if resp = "" {
        Notify("Error", "Could not reach Clavus server")
        return
    }

    try {
        data := JSON.Parse(resp)
        if data.Length = 0 {
            Notify("No Projects", "No projects registered")
            return
        }

        names := ""
        for p in data {
            if p.Has("name") {
                names .= p["name"] . "`n"
            }
        }

        result := InputBox("Type a project name:`n" . RTrim(names, "`n"), "Clavus — Switch Project", "w400")
        if result.Result = "OK" and result.Value != "" {
            Notify("Switched", "Now working on: " . result.Value)
        }
    } catch {
        Notify("Error", "Could not parse project list")
    }
}

UrlEncode(str) {
    ; Simple URL encoding for ASCII strings
    str := StrReplace(str, " ", "%20")
    str := StrReplace(str, "&", "%26")
    str := StrReplace(str, "?", "%3F")
    str := StrReplace(str, "=", "%3D")
    return str
}

; ─── Hotkey Registration ─────────────────────────────────────────────

for id, binding in Bindings {
    if !binding.Has("win_mods") or !binding.Has("win_key") {
        continue
    }
    if !binding.Has("action") {
        continue
    }

    ; Convert mod strings to AHK modifier symbols
    modStr := ""
    for m in binding["win_mods"] {
        if m = "win" {
            modStr .= "#"
        } else if m = "alt" {
            modStr .= "!"
        } else if m = "shift" {
            modStr .= "+"
        } else if m = "ctrl" {
            modStr .= "^"
        }
    }

    keyName := binding["win_key"]
    params := binding.Has("params") ? binding["params"] : Map()

    ; Register hotkey based on action
    action := binding["action"]
    if action = "new_cue" {
        Hotkey(modStr . keyName, (*) => NewCue(params))
    } else if action = "snapshot" {
        Hotkey(modStr . keyName, (*) => DoSnapshot(params))
    } else if action = "inject" {
        Hotkey(modStr . keyName, (*) => DoInject())
    } else if action = "list_cues" {
        Hotkey(modStr . keyName, (*) => ListCues(params))
    } else if action = "toggle_tui" {
        Hotkey(modStr . keyName, (*) => ToggleTUI(params))
    } else if action = "switch_project" {
        Hotkey(modStr . keyName, (*) => SwitchProject(params))
    }
}

; ─── Ready ───────────────────────────────────────────────────────────

Notify("Clavus Ready", "Keyboard automation loaded — " . Bindings.Count . " hotkeys active")
