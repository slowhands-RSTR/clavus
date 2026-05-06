#!/usr/bin/env bash
# Install Clavus Relay as a macOS LaunchAgent for always-on operation.
#
# Usage:
#   ./install-relay.sh                    # Install for current user
#   ./install-relay.sh --uninstall        # Remove the LaunchAgent
#
# The relay runs clavus relay on port 7890 and auto-starts on login.
# Logs go to ~/.clavus/relay.log and ~/.clavus/relay.err

set -euo pipefail

CLAVUS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_NAME="com.slowhands.clavus-relay"
PLIST_SRC="$CLAVUS_DIR/clavus/relay/launchd.plist.template"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"
LAUNCHCTL_LABEL="$PLIST_NAME"

if [ "${1:-}" = "--uninstall" ]; then
    echo "🛑 Uninstalling Clavus Relay LaunchAgent..."
    if [ -f "$PLIST_DEST" ]; then
        launchctl bootout "gui/$(id -u)" "$PLIST_DEST" 2>/dev/null || true
        rm "$PLIST_DEST"
        echo "   Removed $PLIST_DEST"
    else
        echo "   No LaunchAgent found at $PLIST_DEST"
    fi
    echo "✅ Done"
    exit 0
fi

echo "🔧 Installing Clavus Relay LaunchAgent..."
echo "   Source: $CLAVUS_DIR"
echo "   User:   $(whoami)"

# Create the plist from template
mkdir -p "$HOME/Library/LaunchAgents"
sed -e "s|__CLAVUS_DIR__|$CLAVUS_DIR|g" \
    -e "s|__USER__|$(whoami)|g" \
    "$PLIST_SRC" > "$PLIST_DEST"

echo "   Wrote $PLIST_DEST"

# Use full path for python3
PYTHON_PATH=$(which python3 || echo "/usr/local/bin/python3")
sed -i '' "s|/usr/local/bin/python3|$PYTHON_PATH|" "$PLIST_DEST"

# Ensure relay log dir exists
mkdir -p "$HOME/.clavus"

# Load the LaunchAgent
echo "   Loading LaunchAgent..."
launchctl bootstrap "gui/$(id -u)" "$PLIST_DEST" 2>/dev/null || \
    launchctl load "$PLIST_DEST" 2>/dev/null || true

# Verify it's running
sleep 1
if launchctl print "gui/$(id -u)/$LAUNCHCTL_LABEL" 2>/dev/null | grep -q "state = running"; then
    echo "✅ Clavus Relay is running!"
    echo "   Logs: ~/.clavus/relay.log"
    echo "   Errors: ~/.clavus/relay.err"
    echo ""
    echo "   To stop:  launchctl bootout gui/$(id -u) $PLIST_DEST"
    echo "   To start: launchctl bootstrap gui/$(id -u) $PLIST_DEST"
    echo "   To view:  launchctl print gui/$(id -u)/$PLIST_NAME"
else
    echo "⚠️  LaunchAgent loaded but may need a moment to start."
    echo "   Check: launchctl print gui/$(id -u)/$PLIST_NAME"
    echo "   Logs:  tail -f ~/.clavus/relay.err"
fi
