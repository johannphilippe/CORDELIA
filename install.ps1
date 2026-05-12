# CORDELIA installer — Windows (PowerShell)
# Run with: powershell -ExecutionPolicy Bypass -File install.ps1

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

Write-Host "=== CORDELIA installer ===" -ForegroundColor Cyan
Write-Host

# ── helpers ───────────────────────────────────────────────────────────────────
function Has-Command($cmd) {
    return [bool](Get-Command $cmd -ErrorAction SilentlyContinue)
}

function Python-Ok {
    if (Has-Command "python") {
        $ver = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($ver -and [version]$ver -ge [version]"3.11") { return $true }
    }
    return $false
}

# ── winget check ──────────────────────────────────────────────────────────────
if (-not (Has-Command "winget")) {
    Write-Host "[!] winget not found. Please install 'App Installer' from the Microsoft Store," -ForegroundColor Red
    Write-Host "    then re-run this script, or install Csound and Python manually:" -ForegroundColor Red
    Write-Host "    Csound : https://csound.com/download" -ForegroundColor Yellow
    Write-Host "    Python : https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# ── Csound ────────────────────────────────────────────────────────────────────
if (Has-Command "csound") {
    $v = csound --version 2>&1 | Select-Object -First 1
    Write-Host "[ok] Csound already installed ($v)"
} else {
    Write-Host "Installing Csound via winget..."
    winget install --id Csound.Csound --accept-package-agreements --accept-source-agreements
    # Refresh PATH so csound64.dll is visible in this session
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("PATH","User")
}

# ── Python ────────────────────────────────────────────────────────────────────
if (Python-Ok) {
    Write-Host "[ok] Python $(python --version) found"
} else {
    Write-Host "Installing Python 3.11 via winget..."
    winget install --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("PATH","User")
}

# ── virtual environment ────────────────────────────────────────────────────────
Write-Host
$venv = ".venv"
if (Test-Path $venv) {
    Write-Host "[ok] Virtual environment already exists at $venv"
} else {
    Write-Host "Creating virtual environment at $venv ..."
    python -m venv $venv
}

# ── Python deps ────────────────────────────────────────────────────────────────
Write-Host "Installing Python dependencies into $venv ..."
& "$venv\Scripts\pip.exe" install --upgrade pip --quiet
& "$venv\Scripts\pip.exe" install -r requirements.txt

# ── run helper ────────────────────────────────────────────────────────────────
@'
@echo off
cd /d "%~dp0"
.venv\Scripts\python.exe cordelia\cordelia.py %*
'@ | Set-Content -Path "run.bat" -Encoding ASCII

Write-Host
Write-Host "=== Done ===" -ForegroundColor Green
Write-Host
Write-Host "Run CORDELIA with:"
Write-Host "  run.bat" -ForegroundColor Yellow
Write-Host
Write-Host "Or activate the environment manually:"
Write-Host "  .venv\Scripts\activate"
Write-Host "  python cordelia\cordelia.py"
