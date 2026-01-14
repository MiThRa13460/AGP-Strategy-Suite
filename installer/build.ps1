# AGP Strategy Suite - Complete Build Script
# ===========================================
#
# This script builds all components and creates the installer:
# 1. Python backend (PyInstaller)
# 2. Tauri desktop app
# 3. SimHub plugin
# 4. NSIS installer
#
# Requirements:
# - Node.js & pnpm
# - Rust & Cargo
# - Python 3.11+ & pip
# - .NET SDK 4.8
# - NSIS (optional, for installer)

param(
    [switch]$SkipBackend,
    [switch]$SkipDesktop,
    [switch]$SkipPlugin,
    [switch]$SkipInstaller,
    [switch]$Clean,
    [string]$Version = "1.0.0"
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $PSScriptRoot
$DistDir = Join-Path $RootDir "dist"

# Colors for output
function Write-Step { param($msg) Write-Host "`n[$([char]0x2713)] $msg" -ForegroundColor Cyan }
function Write-Info { param($msg) Write-Host "    $msg" -ForegroundColor Gray }
function Write-Success { param($msg) Write-Host "    $msg" -ForegroundColor Green }
function Write-Warning { param($msg) Write-Host "    $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "    $msg" -ForegroundColor Red }

# Banner
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   AGP Strategy Suite - Build System v$Version" -ForegroundColor White
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Clean if requested
if ($Clean) {
    Write-Step "Cleaning previous builds..."
    if (Test-Path $DistDir) {
        Remove-Item -Recurse -Force $DistDir
        Write-Info "Removed dist directory"
    }

    # Clean Tauri
    $tauriTarget = Join-Path $RootDir "apps\desktop\src-tauri\target"
    if (Test-Path $tauriTarget) {
        Remove-Item -Recurse -Force $tauriTarget
        Write-Info "Removed Tauri target directory"
    }

    # Clean SimHub plugin
    $pluginBin = Join-Path $RootDir "apps\simhub-plugin\AGPStrategy\bin"
    if (Test-Path $pluginBin) {
        Remove-Item -Recurse -Force $pluginBin
        Write-Info "Removed SimHub plugin bin directory"
    }
}

# Create dist directory
New-Item -ItemType Directory -Force -Path $DistDir | Out-Null

# ============================================
# 1. Build Python Backend
# ============================================
if (-not $SkipBackend) {
    Write-Step "Building Python Backend..."

    $backendDir = Join-Path $RootDir "packages\core"
    $backendDist = Join-Path $DistDir "backend"

    Push-Location $backendDir
    try {
        # Create virtual environment if needed
        if (-not (Test-Path "venv")) {
            Write-Info "Creating virtual environment..."
            python -m venv venv
        }

        # Activate and install dependencies
        Write-Info "Installing dependencies..."
        & ".\venv\Scripts\pip.exe" install -r requirements.txt -q
        & ".\venv\Scripts\pip.exe" install pyinstaller -q

        # Build with PyInstaller
        Write-Info "Building with PyInstaller..."
        & ".\venv\Scripts\pyinstaller.exe" `
            --name "agp-backend" `
            --onedir `
            --noconsole `
            --distpath $backendDist `
            --workpath "$env:TEMP\agp-build" `
            --specpath "$env:TEMP\agp-build" `
            --add-data "agp_core;agp_core" `
            main.py

        Write-Success "Backend built successfully"
    }
    catch {
        Write-Error "Backend build failed: $_"
        exit 1
    }
    finally {
        Pop-Location
    }
}

# ============================================
# 2. Build Tauri Desktop App
# ============================================
if (-not $SkipDesktop) {
    Write-Step "Building Tauri Desktop App..."

    $desktopDir = Join-Path $RootDir "apps\desktop"

    Push-Location $desktopDir
    try {
        # Install dependencies
        Write-Info "Installing npm dependencies..."
        pnpm install --frozen-lockfile

        # Build Tauri
        Write-Info "Building Tauri application..."
        pnpm tauri build

        # Copy output
        $tauriOutput = Join-Path $desktopDir "src-tauri\target\release"
        $desktopDist = Join-Path $DistDir "desktop"

        New-Item -ItemType Directory -Force -Path $desktopDist | Out-Null
        Copy-Item "$tauriOutput\AGPStrategySuite.exe" $desktopDist
        Copy-Item "$tauriOutput\*.dll" $desktopDist -ErrorAction SilentlyContinue

        if (Test-Path "$tauriOutput\resources") {
            Copy-Item "$tauriOutput\resources" "$desktopDist\resources" -Recurse
        }

        Write-Success "Desktop app built successfully"
    }
    catch {
        Write-Error "Desktop build failed: $_"
        exit 1
    }
    finally {
        Pop-Location
    }
}

# ============================================
# 3. Build SimHub Plugin
# ============================================
if (-not $SkipPlugin) {
    Write-Step "Building SimHub Plugin..."

    $pluginDir = Join-Path $RootDir "apps\simhub-plugin"

    Push-Location $pluginDir
    try {
        # Set SimHub path for build
        if (-not $env:SIMHUB_PATH) {
            $simhubPaths = @(
                "$env:ProgramFiles\SimHub",
                "${env:ProgramFiles(x86)}\SimHub",
                "$env:LOCALAPPDATA\SimHub"
            )
            foreach ($path in $simhubPaths) {
                if (Test-Path "$path\SimHub.Plugins.dll") {
                    $env:SIMHUB_PATH = $path
                    break
                }
            }
        }

        if (-not $env:SIMHUB_PATH) {
            Write-Warning "SimHub not found - using placeholder path"
            $env:SIMHUB_PATH = "C:\Program Files (x86)\SimHub"
        }

        Write-Info "Building plugin (SimHub path: $env:SIMHUB_PATH)..."
        dotnet build AGPStrategy\AGPStrategy.csproj -c Release

        # Copy output
        $pluginOutput = Join-Path $pluginDir "AGPStrategy\bin\Release\net48"
        $pluginDist = Join-Path $DistDir "plugin"

        New-Item -ItemType Directory -Force -Path $pluginDist | Out-Null
        Copy-Item "$pluginOutput\AGPStrategyPlugin.dll" $pluginDist
        Copy-Item "$pluginOutput\Newtonsoft.Json.dll" $pluginDist -ErrorAction SilentlyContinue
        Copy-Item "$pluginOutput\websocket-sharp.dll" $pluginDist -ErrorAction SilentlyContinue

        Write-Success "SimHub plugin built successfully"
    }
    catch {
        Write-Error "Plugin build failed: $_"
        exit 1
    }
    finally {
        Pop-Location
    }
}

# ============================================
# 4. Create NSIS Installer
# ============================================
if (-not $SkipInstaller) {
    Write-Step "Creating NSIS Installer..."

    # Check for NSIS
    $nsisPath = Get-Command makensis -ErrorAction SilentlyContinue
    if (-not $nsisPath) {
        $nsisPath = "C:\Program Files (x86)\NSIS\makensis.exe"
        if (-not (Test-Path $nsisPath)) {
            $nsisPath = "C:\Program Files\NSIS\makensis.exe"
        }
    }

    if (-not (Test-Path $nsisPath)) {
        Write-Warning "NSIS not found - skipping installer creation"
        Write-Info "Install NSIS from https://nsis.sourceforge.io/"
    }
    else {
        $installerDir = Join-Path $RootDir "installer\nsis"

        Push-Location $installerDir
        try {
            Write-Info "Running NSIS compiler..."
            & $nsisPath /V3 /DVERSION=$Version agp-strategy-suite.nsi

            Write-Success "Installer created: dist\AGPStrategySuite-$Version-Setup.exe"
        }
        catch {
            Write-Error "Installer creation failed: $_"
        }
        finally {
            Pop-Location
        }
    }
}

# ============================================
# Summary
# ============================================
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   Build Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Output directory: $DistDir" -ForegroundColor Gray
Write-Host ""

if (Test-Path "$DistDir\backend") {
    Write-Host "  [OK] Backend" -ForegroundColor Green
}
if (Test-Path "$DistDir\desktop") {
    Write-Host "  [OK] Desktop App" -ForegroundColor Green
}
if (Test-Path "$DistDir\plugin") {
    Write-Host "  [OK] SimHub Plugin" -ForegroundColor Green
}
if (Test-Path "$DistDir\AGPStrategySuite-$Version-Setup.exe") {
    Write-Host "  [OK] Installer" -ForegroundColor Green
}

Write-Host ""
