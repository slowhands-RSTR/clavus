# Clavus one-command installer for Windows (PowerShell)
# Usage: irm https://raw.githubusercontent.com/castle-queenside/clavus/main/install.ps1 | iex

param(
    [string]$InstallDir = "$env:LOCALAPPDATA\Clavus"
)

$ErrorActionPreference = "Stop"
$REPO = "https://github.com/castle-queenside/clavus.git"

# Colors for output
function Write-Info($msg) { Write-Host "[+] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[!] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[*] $msg" -ForegroundColor Red }

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Clavus Installer  ·  v0.1.0-beta" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Info "Installing to: $InstallDir"
Write-Info "OS: Windows (PowerShell)"
Write-Host ""

# Check for Python
Write-Info "Checking Python..."
$pyCmd = $null

# Try common Python commands on Windows
foreach ($cmd in @("py", "python3", "python")) {
    try {
        $ver = & $cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($ver) {
            $major, $minor = $ver.Split('.')
            if ([int]$major -ge 3 -and [int]$minor -ge 10) {
                $pyCmd = $cmd
                Write-Info "Python $ver detected ($cmd)"
                break
            }
        }
    } catch { }
}

if (-not $pyCmd) {
    Write-Err "Python 3.10+ not found."
    Write-Host ""
    Write-Host "Please install Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Or open the Microsoft Store and search for 'Python 3.11'" -ForegroundColor Yellow
    exit 1
}

# Check for git
Write-Info "Checking git..."
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Warn "git not found. Installing via zip download instead..."
    # Fallback: download the repo as zip
    $zipPath = "$env:TEMP\clavus.zip"
    $githubZip = "https://github.com/castle-queenside/clavus/archive/refs/heads/main.zip"
    Write-Info "Downloading..."
    Invoke-WebRequest -Uri $githubZip -OutFile $zipPath -UseBasicParsing
    Expand-Archive -Path $zipPath -DestinationPath $InstallDir -Force
    # Move contents up one level
    $src = "$InstallDir\clavus-main"
    if (Test-Path $src) {
        Get-ChildItem $src | Move-Item -Destination $InstallDir -Force
        Remove-Item $src -Force
    }
} else {
    # Clone or update
    if (Test-Path "$InstallDir\.git") {
        Write-Info "Clavus already installed — updating..."
        Set-Location $InstallDir
        git pull origin main
    } else {
        Write-Info "Cloning Clavus..."
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
        git clone $REPO $InstallDir
    }
}

Set-Location $InstallDir

# Install via pip
Write-Info "Installing dependencies..."
& $pyCmd -m pip install -e . --quiet

# Add to PATH hint
$profilePath = $PROFILE
$profileDir = Split-Path $profilePath -Parent
if (-not (Test-Path $profileDir)) { New-Item -ItemType Directory -Path $profileDir -Force | Out-Null }

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Info "Install complete!"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Restart your terminal (or run: refreshenv)"
Write-Host "  2. Run setup:     py -m clavus setup"
Write-Host "  3. Start TUI:     py -m clavus tui"
Write-Host ""
Write-Host "Note: On first run, Windows may ask 'Allow Python to access firewall'" -ForegroundColor Gray
Write-Host ""

$response = Read-Host "Run setup wizard now? [Y/n]"
if ($response -ne "n" -and $response -ne "N") {
    & $pyCmd -m clavus setup
}