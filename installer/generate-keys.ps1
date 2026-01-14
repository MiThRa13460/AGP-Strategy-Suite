# AGP Strategy Suite - Updater Key Generator
# ==========================================
#
# This script generates the signing keys for the Tauri updater.
# Run this ONCE before your first release.
#
# The private key should be kept SECRET and stored securely.
# The public key goes in tauri.conf.json

$ErrorActionPreference = "Stop"

$KeysDir = Join-Path $PSScriptRoot "keys"

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   AGP Strategy Suite - Updater Key Generator" -ForegroundColor White
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Create keys directory
if (-not (Test-Path $KeysDir)) {
    New-Item -ItemType Directory -Force -Path $KeysDir | Out-Null
}

# Check if keys already exist
$PrivateKeyPath = Join-Path $KeysDir "agp-strategy-suite.key"
$PublicKeyPath = Join-Path $KeysDir "agp-strategy-suite.pub"

if ((Test-Path $PrivateKeyPath) -or (Test-Path $PublicKeyPath)) {
    Write-Host "WARNING: Keys already exist!" -ForegroundColor Yellow
    Write-Host ""
    $response = Read-Host "Do you want to regenerate them? This will invalidate existing signatures! (y/N)"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Host "Aborted." -ForegroundColor Gray
        exit 0
    }
}

Write-Host "Generating new signing keys..." -ForegroundColor Yellow
Write-Host ""

# Generate keys using Tauri CLI
try {
    # Check for Tauri CLI
    $tauriCli = Get-Command "cargo-tauri" -ErrorAction SilentlyContinue
    if (-not $tauriCli) {
        Write-Host "Installing Tauri CLI..." -ForegroundColor Gray
        cargo install tauri-cli
    }

    # Generate keys (Tauri 2.0 syntax)
    Push-Location $KeysDir
    $env:TAURI_SIGNING_PRIVATE_KEY_PASSWORD = ""
    cargo tauri signer generate -w agp-strategy-suite.key

    Write-Host ""
    Write-Host "Keys generated successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Files created:" -ForegroundColor Cyan
    Write-Host "  Private key: $PrivateKeyPath" -ForegroundColor Gray
    Write-Host "  Public key:  $PublicKeyPath" -ForegroundColor Gray
    Write-Host ""

    # Read and display public key
    if (Test-Path $PublicKeyPath) {
        $publicKey = Get-Content $PublicKeyPath -Raw
        Write-Host "Public key (add to tauri.conf.json):" -ForegroundColor Cyan
        Write-Host $publicKey -ForegroundColor White
    }

    Write-Host ""
    Write-Host "IMPORTANT:" -ForegroundColor Yellow
    Write-Host "  1. Keep the private key (.key) SECRET" -ForegroundColor Gray
    Write-Host "  2. Add the public key to tauri.conf.json > plugins > updater > pubkey" -ForegroundColor Gray
    Write-Host "  3. Set TAURI_SIGNING_PRIVATE_KEY environment variable when building releases" -ForegroundColor Gray
    Write-Host ""
}
catch {
    Write-Host "Error generating keys: $_" -ForegroundColor Red
    exit 1
}
finally {
    Pop-Location
}
