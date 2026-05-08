# Clavus ALS Integrity Diagnostic
# Run from PowerShell on Windows

$ErrorActionPreference = "Stop"

Write-Host "=== Clavus .ALS Integrity Diagnostic ===" -ForegroundColor Cyan
Write-Host ""

# ─── 1. Find the source .als ───
$desktop = [Environment]::GetFolderPath("Desktop")
$projectsDir = "$env:USERPROFILE\.clavus\projects"
$objectsDir = "$env:USERPROFILE\.clavus\objects"

Write-Host "[1] Source .als files on Desktop:" -ForegroundColor Yellow
$alsFiles = Get-ChildItem -Path $desktop -Filter "*.als" -Recurse -Depth 3 | Where-Object { $_.FullName -notmatch "Backup" -and $_.FullName -notmatch "Ableton Project Info" }
foreach ($f in $alsFiles) {
    $hash = (Get-FileHash -Path $f.FullName -Algorithm SHA256).Hash
    $size = $f.Length
    Write-Host "  $($f.Name)  ($size bytes)  SHA256: $hash"
}

# ─── 2. Find Clavus copies ───
Write-Host ""
Write-Host "[2] Clavus project copies:" -ForegroundColor Yellow
if (Test-Path $projectsDir) {
    $projAls = Get-ChildItem -Path $projectsDir -Filter "*.als" -Recurse -Depth 3
    foreach ($f in $projAls) {
        $hash = (Get-FileHash -Path $f.FullName -Algorithm SHA256).Hash
        $size = $f.Length
        Write-Host "  $($f.FullName)  ($size bytes)  SHA256: $hash"
    }
} else {
    Write-Host "  (no projects directory)" -ForegroundColor DarkGray
}

# ─── 3. Check objects store ───
Write-Host ""
Write-Host "[3] Objects store (stored .als blobs):" -ForegroundColor Yellow
if (Test-Path $objectsDir) {
    # Read index.json to find als_hashes
    $indexPath = "$env:USERPROFILE\.clavus\index.json"
    if (Test-Path $indexPath) {
        $index = Get-Content $indexPath -Raw | ConvertFrom-Json
        foreach ($projName in $index.projects.PSObject.Properties.Name) {
            $proj = $index.projects.$projName
            $snapHash = $proj.head
            if ($snapHash) {
                $shortPrefix = $snapHash.Substring(0,2)
                $metaPath = "$objectsDir\$shortPrefix\$snapHash.meta"
                if (Test-Path $metaPath) {
                    $meta = Get-Content $metaPath -Raw | ConvertFrom-Json
                    $alsHash = $meta.als_hash
                    if ($alsHash) {
                        $alsPrefix = $alsHash.Substring(0,2)
                        $alsPath = "$objectsDir\$alsPrefix\$alsHash"
                        if (Test-Path $alsPath) {
                            $alsSize = (Get-Item $alsPath).Length
                            Write-Host "  $projName : als_hash=$alsHash ($alsSize bytes)"
                        } else {
                            Write-Host "  $projName : als_hash=$alsHash — BLOB NOT FOUND" -ForegroundColor Red
                        }
                    } else {
                        Write-Host "  $projName : no als_hash in snapshot" -ForegroundColor DarkGray
                    }
                }
            }
        }
    } else {
        Write-Host "  (no index.json)" -ForegroundColor DarkGray
    }
} else {
    Write-Host "  (no objects directory)" -ForegroundColor DarkGray
}

# ─── 4. CROSS-CHECK ───
Write-Host ""
Write-Host "[4] Cross-check: source vs copy vs stored blob" -ForegroundColor Yellow
Write-Host "  If any hashes differ, the corruption point is between those two stages."
Write-Host "  If all hashes match, the .als files are fine — it's Ableton's state."

# ─── 5. Check for gzip validity ───
Write-Host ""
Write-Host "[5] Gzip integrity check (Python):" -ForegroundColor Yellow
python3 -c "
import gzip, sys, hashlib
from pathlib import Path
import json

# Check all .als files found
als_files = []
desktop = Path.home() / 'Desktop'
projects = Path.home() / '.clavus' / 'projects'

for d in [desktop, projects]:
    if d.exists():
        for f in d.rglob('*.als'):
            if 'Backup' not in str(f) and 'Ableton Project Info' not in str(f):
                als_files.append(f)

for f in als_files:
    try:
        raw = f.read_bytes()
        gzip.decompress(raw)
        h = hashlib.sha256(raw).hexdigest()
        print(f'  OK gzip: {f.name}  ({len(raw)} bytes)  sha256={h[:16]}...')
    except Exception as e:
        print(f'  CORRUPT: {f.name}  ({len(raw)} bytes)  {e}')
        sys.exit(1)

# Check stored blobs
objects = Path.home() / '.clavus' / 'objects'
index = Path.home() / '.clavus' / 'index.json'
if index.exists():
    idx = json.loads(index.read_text())
    for name, proj in idx.get('projects', {}).items():
        snap_hash = proj.get('head', '')
        if snap_hash:
            meta_path = objects / snap_hash[:2] / f'{snap_hash}.meta'
            if meta_path.exists():
                meta = json.loads(meta_path.read_text())
                ah = meta.get('als_hash')
                if ah:
                    blob_path = objects / ah[:2] / ah
                    if blob_path.exists():
                        data = blob_path.read_bytes()
                        gzip.decompress(data)
                        h = hashlib.sha256(data).hexdigest()
                        print(f'  OK blob: {name}  ({len(data)} bytes)  sha256={h[:16]}...')
                    else:
                        print(f'  MISSING blob: {name}  als_hash={ah[:16]}...')
"
