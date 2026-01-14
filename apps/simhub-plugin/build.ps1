# AGP Strategy Suite - SimHub Plugin Build Script
# ================================================

param(
    [switch]$Release,
    [switch]$Install,
    [string]$SimHubPath = ""
)

$ErrorActionPreference = "Stop"

# Configuration
$ProjectDir = Join-Path $PSScriptRoot "AGPStrategy"
$ProjectFile = Join-Path $ProjectDir "AGPStrategy.csproj"
$Configuration = if ($Release) { "Release" } else { "Debug" }

# Detect SimHub installation
function Get-SimHubPath {
    $possiblePaths = @(
        $env:SIMHUB_PATH,
        "C:\Program Files (x86)\SimHub",
        "C:\Program Files\SimHub",
        "$env:LOCALAPPDATA\SimHub"
    )

    foreach ($path in $possiblePaths) {
        if ($path -and (Test-Path (Join-Path $path "SimHubWPF.exe"))) {
            return $path
        }
    }
    return $null
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "AGP Strategy Suite - SimHub Plugin Builder" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Find SimHub
if (-not $SimHubPath) {
    $SimHubPath = Get-SimHubPath
}

if (-not $SimHubPath) {
    Write-Host "WARNING: SimHub installation not found." -ForegroundColor Yellow
    Write-Host "Set SIMHUB_PATH environment variable or use -SimHubPath parameter" -ForegroundColor Yellow
    Write-Host ""

    # Set a placeholder for build to proceed
    $env:SIMHUB_PATH = "C:\Program Files (x86)\SimHub"
} else {
    Write-Host "SimHub found at: $SimHubPath" -ForegroundColor Green
    $env:SIMHUB_PATH = $SimHubPath
}

Write-Host ""
Write-Host "Building $Configuration configuration..." -ForegroundColor Yellow
Write-Host ""

# Build
try {
    dotnet build $ProjectFile -c $Configuration

    if ($LASTEXITCODE -ne 0) {
        throw "Build failed with exit code $LASTEXITCODE"
    }

    Write-Host ""
    Write-Host "Build successful!" -ForegroundColor Green

    # Output location
    $OutputDir = Join-Path $ProjectDir "bin\$Configuration\net48"
    $DllPath = Join-Path $OutputDir "AGPStrategyPlugin.dll"

    Write-Host "Output: $DllPath" -ForegroundColor Gray

    # Install to SimHub if requested
    if ($Install -and $SimHubPath) {
        $PluginsDir = Join-Path $SimHubPath "Plugins"

        if (Test-Path $PluginsDir) {
            Write-Host ""
            Write-Host "Installing to SimHub..." -ForegroundColor Yellow

            # Copy main DLL
            Copy-Item $DllPath $PluginsDir -Force
            Write-Host "  Copied AGPStrategyPlugin.dll" -ForegroundColor Gray

            # Copy dependencies
            $deps = @(
                "Newtonsoft.Json.dll",
                "websocket-sharp.dll"
            )

            foreach ($dep in $deps) {
                $depPath = Join-Path $OutputDir $dep
                if (Test-Path $depPath) {
                    Copy-Item $depPath $PluginsDir -Force
                    Write-Host "  Copied $dep" -ForegroundColor Gray
                }
            }

            Write-Host ""
            Write-Host "Plugin installed to: $PluginsDir" -ForegroundColor Green
            Write-Host "Restart SimHub to load the plugin." -ForegroundColor Cyan
        } else {
            Write-Host "SimHub Plugins directory not found: $PluginsDir" -ForegroundColor Red
        }
    }

} catch {
    Write-Host ""
    Write-Host "Build failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
