/**
 * clavus-api.js — Max for Live JS bridge to Clavus server.
 *
 * This file is loaded by a [js] object in the Max patch.
 * Max's JS environment has access to:
 *   - outlets (this.outlet, this.messnamed)
 *   - dict object creation
 *   - task scheduling
 *   - Max message passing
 *
 * HTTP communication goes through [maxurl] objects.
 * This JS handles message routing and JSON formatting.
 *
 * Patch wiring:
 *   Inlet 0: control messages (bang, list, anything)
 *   Outlet 0: connection status (0/1)
 *   Outlet 1: JSON string for [dict] response parsing
 *   Outlet 2: status text for display
 *   Outlet 3: cue data (formatted symbols for UI)
 */

// ─── Configuration ─────────────────────────────────────────────────────

var CLAVUS_BASE = "http://127.0.0.1:7890";
var MAXURL_NAME = "maxurl";

// ─── Helpers ────────────────────────────────────────────────────────────

function log(msg) {
    post("[clavus] " + msg + "\n");
}

// ─── Inlet Handler ─────────────────────────────────────────────────────

function anything() {
    var msg = arrayfromargs(messagename);
    var cmd = msg[0];
    var args = msg.slice(1);

    switch (cmd) {
        case "ping":
            ping();
            break;
        case "snapshot":
            snapshot(args[0], args.slice(1).join(" "));
            break;
        case "cues":
            getCues(args[0]);
            break;
        case "addcue":
            // addcue <project> <position> <text...>
            addCue(args[0], args[1], args.slice(2).join(" "), "");
            break;
        case "addcuetrack":
            // addcuetrack <project> <position> <track> <text...>
            addCue(args[0], args[1], args[2], args.slice(3).join(" "));
            break;
        case "restore":
            restore(args[0]);
            break;
        case "inject":
            inject(args[0]);
            break;
        case "project":
            getProject(args[0]);
            break;
        default:
            log("unknown command: " + cmd);
            break;
    }
}

// ─── API Calls ──────────────────────────────────────────────────────────

/**
 * Ping the Clavus server to check connectivity.
 * Outlet 0: 1 if alive, 0 if not
 */
function ping() {
    var url = CLAVUS_BASE + "/api/ping";
    var dictName = "clavus_ping";
    var request = new Dict(dictName);
    request.set("url", url);
    request.set("http_method", "get");
    request.set("response_dict", "clavus_ping_rsp");
    request.set("timeout", 3000);

    // Sending the dict to maxurl will trigger the request
    outlet(2, "connecting...");
    this.messnamed(MAXURL_NAME, "dictionary", "clavus_ping");
    maxurl_send(request);

    // Max's [maxurl] is asynchronous — response comes back
    // via the dict update. We set up a task to read it.
    // In practice, the maxpatch will handle the response dict
    // in a separate [dict] object.
}

/**
 * Create a Clavus snapshot with a message.
 * @param {string} project - Project name
 * @param {string} message - Snapshot message
 */
function snapshot(project, message) {
    if (!message) {
        message = "snapshot from Live";
    }
    var url = CLAVUS_BASE + "/api/projects/snapshot?name=" + encodeURIComponent(project);
    var dictName = "clavus_snap";
    var request = new Dict(dictName);
    request.set("url", url);
    request.set("http_method", "post");
    request.set("response_dict", "clavus_snap_rsp");
    request.set("timeout", 15000);

    // post_data as dictionary = auto JSON-encoded body
    var payload = new Dict("clavus_snap_payload");
    payload.set("message", message);
    request.set("post_data", "clavus_snap_payload");

    outlet(2, "snapshotting...");
    this.messnamed(MAXURL_NAME, "dictionary", "clavus_snap");
    maxurl_send(request);
}

/**
 * Fetch pending cues from Clavus.
 * @param {string} project - Project name
 */
function getCues(project) {
    var url = CLAVUS_BASE + "/api/cues?pending_only=1&name=" + encodeURIComponent(project);
    var dictName = "clavus_cues";
    var request = new Dict(dictName);
    request.set("url", url);
    request.set("http_method", "get");
    request.set("response_dict", "clavus_cues_rsp");
    request.set("timeout", 5000);

    outlet(2, "fetching cues...");
    this.messnamed(MAXURL_NAME, "dictionary", "clavus_cues");
    maxurl_send(request);
}

/**
 * Add a cue at the current position.
 * @param {string} project - Project name
 * @param {string} position - Time position (e.g. "13.2.1")
 * @param {string} text - Cue text
 * @param {string} track - Track name (optional)
 */
function addCue(project, position, text, track) {
    var url = CLAVUS_BASE + "/api/cues?name=" + encodeURIComponent(project);
    var dictName = "clavus_newcue";
    var request = new Dict(dictName);
    request.set("url", url);
    request.set("http_method", "post");
    request.set("response_dict", "clavus_newcue_rsp");
    request.set("timeout", 5000);

    var payload = new Dict("clavus_cue_payload");
    payload.set("text", text);
    payload.set("position", position);
    payload.set("track", track);
    payload.set("project_name", project);
    request.set("post_data", "clavus_cue_payload");

    outlet(2, "adding cue...");
    this.messnamed(MAXURL_NAME, "dictionary", "clavus_newcue");
    maxurl_send(request);
}

/**
 * Restore the last snapshot.
 * @param {string} project - Project name
 */
function restore(project) {
    var url = CLAVUS_BASE + "/api/projects/restore?name=" + encodeURIComponent(project);
    var dictName = "clavus_restore";
    var request = new Dict(dictName);
    request.set("url", url);
    request.set("http_method", "post");
    request.set("response_dict", "clavus_restore_rsp");
    request.set("timeout", 15000);

    outlet(2, "restoring snapshot...");
    this.messnamed(MAXURL_NAME, "dictionary", "clavus_restore");
    maxurl_send(request);
}

/**
 * Inject pending cues as Ableton markers.
 * @param {string} project - Project name
 */
function inject(project) {
    var url = CLAVUS_BASE + "/api/projects/inject?name=" + encodeURIComponent(project);
    var dictName = "clavus_inject";
    var request = new Dict(dictName);
    request.set("url", url);
    request.set("http_method", "post");
    request.set("response_dict", "clavus_inject_rsp");
    request.set("timeout", 15000);

    outlet(2, "injecting markers...");
    this.messnamed(MAXURL_NAME, "dictionary", "clavus_inject");
    maxurl_send(request);
}

/**
 * Get project info (current snapshot, track count, BPM).
 * @param {string} project - Project name
 */
function getProject(project) {
    var url = CLAVUS_BASE + "/api/project?name=" + encodeURIComponent(project);
    var dictName = "clavus_proj";
    var request = new Dict(dictName);
    request.set("url", url);
    request.set("http_method", "get");
    request.set("response_dict", "clavus_proj_rsp");
    request.set("timeout", 5000);

    outlet(2, "loading project info...");
    this.messnamed(MAXURL_NAME, "dictionary", "clavus_proj");
    maxurl_send(request);
}

// ─── Max's weird JS bootstrap ──────────────────────────────────────────

// Max's JS doesn't expose setTimeout/fetch/XMLHttpRequest
// All HTTP is routed through [maxurl] which is a Max object
// that wraps libcurl. It responds asynchronously by updating
// a [dict] object, which triggers the rest of the Max patch.
//
// The [maxurl] object is patched like:
//
//   [maxurl]───►[dict clavus_snap_rsp]───►[unpack...]
//
// The response dict has keys: status_code, body, headers, error
//
// This JS file only handles message routing and dict construction.
// The actual HTTP lifecycle (request/response/timeout) is handled
// entirely by the Max patch using [maxurl] native objects.
