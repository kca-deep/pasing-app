#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Creates magic-pdf.json configuration file for MinerU

.DESCRIPTION
    This script creates the required configuration file in the user's home directory.
    MinerU needs this file to know where models are stored and which device to use.

.EXAMPLE
    .\create_mineru_config.ps1
#>

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  MinerU Configuration Generator" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get home directory
$homeDir = [Environment]::GetFolderPath("UserProfile")
$configPath = Join-Path $homeDir "magic-pdf.json"

# Default model directory
$modelsDir = Join-Path $homeDir ".magic-pdf\models"

# Check if config already exists
if (Test-Path $configPath) {
    Write-Host "⚠️  Configuration file already exists:" -ForegroundColor Yellow
    Write-Host "   $configPath" -ForegroundColor White
    Write-Host ""
    $response = Read-Host "Overwrite existing config? (y/N)"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Host ""
        Write-Host "❌ Cancelled. Existing configuration preserved." -ForegroundColor Red
        exit 0
    }
}

# Ask about device
Write-Host ""
Write-Host "Select device mode:" -ForegroundColor Yellow
Write-Host "  1. CPU (slower, works on all machines)" -ForegroundColor White
Write-Host "  2. CUDA (faster, requires NVIDIA GPU with CUDA)" -ForegroundColor White
Write-Host ""
$deviceChoice = Read-Host "Enter choice (1/2) [default: 1]"

$deviceMode = "cpu"
if ($deviceChoice -eq "2") {
    $deviceMode = "cuda"
    Write-Host "   Selected: CUDA (GPU)" -ForegroundColor Green
} else {
    $deviceMode = "cpu"
    Write-Host "   Selected: CPU" -ForegroundColor Green
}

# Ask about custom model directory
Write-Host ""
Write-Host "Default model directory:" -ForegroundColor Yellow
Write-Host "  $modelsDir" -ForegroundColor White
Write-Host ""
$customDir = Read-Host "Use custom directory? (press Enter to use default)"

if ($customDir) {
    $modelsDir = $customDir
    Write-Host "   Using custom: $modelsDir" -ForegroundColor Green
} else {
    Write-Host "   Using default: $modelsDir" -ForegroundColor Green
}

# Create configuration object
$config = @{
    "models-dir" = $modelsDir.Replace("\", "/")
    "device-mode" = $deviceMode
}

# Write config file
try {
    $config | ConvertTo-Json | Out-File -FilePath $configPath -Encoding UTF8 -Force

    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "✅ Configuration created successfully!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Location: $configPath" -ForegroundColor White
    Write-Host ""
    Write-Host "Configuration:" -ForegroundColor Yellow
    Get-Content $configPath | Write-Host -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Download models: mineru-models-download -m pipeline -s huggingface" -ForegroundColor White
    Write-Host "  2. Or run: .\backend\setup_mineru.ps1" -ForegroundColor White
    Write-Host ""

} catch {
    Write-Host ""
    Write-Host "❌ Error creating configuration: $_" -ForegroundColor Red
    exit 1
}
