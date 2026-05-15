#!/bin/bash
# Clavus one-command installer
# Usage: curl -fsSL https://get.clavus.sh | bash

set -e

CLAVUS_REPO="https://github.com/castle-queenside/clavus.git"
INSTALL_DIR="${CLAVUS_HOME:-$HOME/.local/clavus}"
CLAVUS_SH="${CLAVUS_HOME:-$HOME}/.clavus.sh"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

info()    { echo -e "${GREEN}[+]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✗]${NC} $1" >&2; }
bold()    { echo -e "${BOLD}$1${NC}"; }

detect_os() {
    case "$(uname -s)" in
        Darwin*)    echo "macos";;
        Linux*)     echo "linux";;
        *)          echo "unsupported";;
    esac
}

check_python() {
    local pycmd=""
    # Try python3 first, then python
    for cmd in python3 python python; do
        if command -v "$cmd" &>/dev/null; then
            pycmd="$cmd"
            break
        fi
    done

    if [ -z "$pycmd" ]; then
        error "Python is not installed."
        echo ""
        bold "Please install Python 3.10 or later:"
        echo "  macOS:  brew install python"
        echo "  Linux:  sudo apt install python3 python3-pip  (Debian/Ubuntu)"
        echo "          sudo dnf install python3              (Fedora)"
        echo "  Or download from: https://www.python.org/downloads/"
        exit 1
    fi

    local ver
    ver=$("$pycmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    local major minor
    major=$(echo "$ver" | cut -d. -f1)
    minor=$(echo "$ver" | cut -d. -f2)

    if [ "$major" -eq 3 ] && [ "$minor" -ge 10 ] || [ "$major" -gt 3 ]; then
        info "Python $ver detected"
        echo "$pycmd"
    else
        error "Python $ver found — Clavus requires 3.10+"
        exit 1
    fi
}

check_pip() {
    local pycmd="$1"
    if ! "$pycmd" -m pip --version &>/dev/null; then
        warn "pip not found — installing pip first..."
        if [ "$(detect_os)" = "macos" ]; then
            if command -v brew &>/dev/null; then
                brew install python@3.11 pip
            else
                error "Homebrew not found. Install Python 3.10+ from https://www.python.org/downloads/"
                exit 1
            fi
        else
            "$pycmd" -m ensurepip --default-pip 2>/dev/null || {
                error "pip install failed. Try: sudo apt install python3-pip"
                exit 1
            }
        fi
    fi
}

install_uv() {
    if command -v uv &>/dev/null; then
        info "uv already installed"
        return
    fi
    info "Installing uv (fast package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source the env if installed
    if [ -f "$HOME/.local/bin/uv" ]; then
        export PATH="$HOME/.local/bin:$PATH"
    elif [ -f "$HOME/.cargo/bin/uv" ]; then
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
}

do_install() {
    local pycmd="$1"
    local os="$(detect_os)"

    bold "═══════════════════════════════════════"
    bold "  Clavus Installer  ·  v0.1.0-beta"
    bold "═══════════════════════════════════════"
    echo ""

    info "Installing to: $INSTALL_DIR"
    info "OS: $os"
    echo ""

    # Check/create install directory
    if [ -d "$INSTALL_DIR/.git" ]; then
        info "Clavus already installed — updating..."
        cd "$INSTALL_DIR" && git pull origin main
    else
        info "Cloning Clavus..."
        mkdir -p "$(dirname "$INSTALL_DIR")"
        git clone "$CLAVUS_REPO" "$INSTALL_DIR"
    fi

    # Install deps
    if command -v uv &>/dev/null; then
        info "Installing via uv..."
        cd "$INSTALL_DIR" && uv pip install -e . --system
    else
        check_pip "$pycmd"
        info "Installing via pip..."
        cd "$INSTALL_DIR" && "$pycmd" -m pip install -e .
    fi

    # Create convenient shell helper
    info "Creating ~/.clavus.sh helper..."
    cat > "$CLAVUS_SH" << 'SHELL_HELPER'
# Clavus convenience commands
export PATH="$HOME/.local/bin:$PATH"

clavus() {
    python3 -m clavus "$@"
}

alias c="clavus"
alias ctui="clavus tui"
alias cshare="clavus share"
alias cpull="clavus pull"
alias cpush="clavus push"
SHELL_HELPER

    echo ""
    bold "═══════════════════════════════════════"
    info "Install complete!"
    echo ""
    bold "Next steps:"
    echo "  1. Source the helper:  source ~/.clavus.sh"
    echo "     (Or restart your terminal)"
    echo ""
    echo "  2. Run setup wizard:   clavus setup"
    echo "     This guides you through first-time config."
    echo ""
    echo "  3. Start the TUI:      clavus tui"
    echo ""
    echo "Shell aliases added: c, ctui, cshare, cpull, cpush"
    echo ""

    read -p "Run setup wizard now? [Y/n] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        cd "$INSTALL_DIR" && "$pycmd" -m clavus setup
    fi
}

# ── Main ──────────────────────────────────────────
main() {
    local pycmd
    local os

    os=$(detect_os)
    if [ "$os" = "unsupported" ]; then
        error "Unsupported OS: $(uname -s)"
        echo "Clavus supports: macOS, Linux"
        exit 1
    fi

    pycmd=$(check_python)

    # Prefer uv if available, otherwise install it
    if ! command -v uv &>/dev/null; then
        install_uv
    fi

    do_install "$pycmd"
}

main "$@"