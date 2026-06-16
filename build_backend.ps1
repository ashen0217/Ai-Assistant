# Jarvis -- Python Backend Build Script
# Compiles server.py into a standalone Windows executable via PyInstaller.
#
# Run from the repo root:
#   .\build_backend.ps1
#
# Prerequisites:
#   - Python 3.x venv at .\venv\
#   - All packages installed in venv (pip install -r requirements.txt)

$ErrorActionPreference = 'Stop'
$RepoRoot = $PSScriptRoot

Write-Host ''
Write-Host '========================================================'
Write-Host '   JARVIS -- Backend Build (PyInstaller)'
Write-Host '========================================================'
Write-Host ''

# Step 1: Check venv exists
$VenvPython = Join-Path $RepoRoot 'venv\Scripts\python.exe'
$VenvActivate = Join-Path $RepoRoot 'venv\Scripts\Activate.ps1'
if (-not (Test-Path $VenvPython)) {
    Write-Host '[ERROR] venv not found at .\venv\' -ForegroundColor Red
    Write-Host '  Create it with: python -m venv venv' -ForegroundColor Yellow
    Write-Host '  Then install deps: pip install -r requirements.txt' -ForegroundColor Yellow
    exit 1
}

Write-Host '[1/4] Activating virtual environment...' -ForegroundColor Green
& $VenvActivate

# Step 2: Install / upgrade PyInstaller in venv
Write-Host '[2/4] Installing/upgrading PyInstaller...' -ForegroundColor Green
& $VenvPython -m pip install --upgrade pyinstaller | Out-Null
Write-Host '      PyInstaller ready.' -ForegroundColor DarkGreen

# Step 3: Clean previous build artifacts
Write-Host '[3/4] Cleaning previous build artifacts...' -ForegroundColor Green
$BuildDir = Join-Path $RepoRoot 'build'
$DistDir  = Join-Path $RepoRoot 'backend-dist'

if (Test-Path $BuildDir) { Remove-Item $BuildDir -Recurse -Force }
if (Test-Path $DistDir)  { Remove-Item $DistDir  -Recurse -Force }

# Step 4: Run PyInstaller
Write-Host '[4/4] Running PyInstaller...' -ForegroundColor Green
Write-Host '      Spec: server.spec' -ForegroundColor DarkGray
Write-Host '      Output: .\backend-dist\core_engine\core_engine.exe' -ForegroundColor DarkGray
Write-Host ''

& $VenvPython -m PyInstaller server.spec `
    --distpath $DistDir `
    --workpath (Join-Path $BuildDir 'pyinstaller-work') `
    --clean

# Verify output
$ExePath = Join-Path $DistDir 'core_engine\core_engine.exe'
if (Test-Path $ExePath) {
    $SizeMB = [math]::Round((Get-Item $ExePath).Length / 1MB, 1)
    Write-Host ''
    Write-Host '========================================================'
    Write-Host '  BUILD SUCCESSFUL' -ForegroundColor Green
    Write-Host "  Output: $ExePath" -ForegroundColor White
    Write-Host "  Size:   ${SizeMB} MB" -ForegroundColor White
    Write-Host '========================================================'
    Write-Host ''
    Write-Host 'Next steps:' -ForegroundColor Yellow
    Write-Host '  1. Test:   .\backend-dist\core_engine.exe' -ForegroundColor Yellow
    Write-Host '  2. Verify: curl http://localhost:8000/api/status' -ForegroundColor Yellow
    Write-Host '  3. Build:  cd jarvis-dashboard; npm run build:full' -ForegroundColor Yellow
    Write-Host ''
} else {
    Write-Host ''
    Write-Host '========================================================'
    Write-Host '  BUILD FAILED -- core_engine.exe not found' -ForegroundColor Red
    Write-Host '========================================================'
    Write-Host ''
    Write-Host 'Check the PyInstaller output above for errors.' -ForegroundColor Yellow
    Write-Host 'Common fixes:' -ForegroundColor Yellow
    Write-Host '  - Missing hidden import: add to server.spec hiddenimports[]' -ForegroundColor Yellow
    Write-Host '  - Missing data file: add to server.spec datas[]' -ForegroundColor Yellow
    exit 1
}
