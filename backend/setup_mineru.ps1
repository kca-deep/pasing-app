#!/usr/bin/env pwsh
<#
.SYNOPSIS
    MinerU Model Setup Script for Windows PowerShell

.DESCRIPTION
    Downloads and verifies MinerU (magic-pdf) model weights.
    Run this script once before using MinerU parsing features.

.EXAMPLE
    .\setup_mineru.ps1
#>

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MinerU Model Setup for Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if venv is activated
$venvPath = Join-Path $PSScriptRoot "venv\Scripts\Activate.ps1"
if (-not (Test-Path $venvPath)) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "  Expected: $venvPath" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please create the virtual environment first:" -ForegroundColor Yellow
    Write-Host "  cd backend" -ForegroundColor White
    Write-Host "  python -m venv venv" -ForegroundColor White
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  pip install -r requirements.txt" -ForegroundColor White
    exit 1
}

# Activate virtual environment
Write-Host "Step 1: Activating virtual environment..." -ForegroundColor Yellow
& $venvPath

# Check magic-pdf installation
Write-Host ""
Write-Host "Step 2: Checking magic-pdf installation..." -ForegroundColor Yellow
try {
    $version = python -c "import magic_pdf; print('OK')" 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "magic-pdf not installed"
    }
    Write-Host "  ✓ magic-pdf is installed" -ForegroundColor Green
} catch {
    Write-Host "  ✗ magic-pdf not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Installing magic-pdf..." -ForegroundColor Yellow
    pip install "magic-pdf[full]"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Failed to install magic-pdf" -ForegroundColor Red
        exit 1
    }
}

# Check current model status
Write-Host ""
Write-Host "Step 3: Checking model status..." -ForegroundColor Yellow
python download_mineru_models.py

# Prompt user to download models
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Ready to Download Models" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will download ~2-3GB of AI models." -ForegroundColor Yellow
Write-Host "Models are required for MinerU to work." -ForegroundColor Yellow
Write-Host ""
$response = Read-Host "Download models now? (Y/n)"

if ($response -eq "" -or $response -eq "Y" -or $response -eq "y") {
    Write-Host ""
    Write-Host "Step 4: Downloading models (this may take 5-10 minutes)..." -ForegroundColor Yellow
    Write-Host ""

    # Try to download models using mineru-models-download
    Write-Host "Downloading pipeline models from HuggingFace..." -ForegroundColor Cyan
    mineru-models-download -m pipeline -s huggingface

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✓ Models downloaded successfully!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "✗ Auto-download failed!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Manual download instructions:" -ForegroundColor Yellow
        Write-Host "  1. Visit: https://huggingface.co/wanderkid/PDF-Extract-Kit" -ForegroundColor White
        Write-Host "  2. Or visit: https://www.modelscope.cn/models/wanderkid/PDF-Extract-Kit" -ForegroundColor White
        Write-Host "  3. Download and extract to: $PSScriptRoot\models\" -ForegroundColor White
        Write-Host ""
        Write-Host "See MINERU_SETUP.md for detailed instructions." -ForegroundColor Cyan
        exit 1
    }

    # Verify installation
    Write-Host ""
    Write-Host "Step 5: Verifying installation..." -ForegroundColor Yellow
    python download_mineru_models.py

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  ✓ Setup Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "MinerU is now ready to use." -ForegroundColor Green
    Write-Host "You can now parse documents with advanced features:" -ForegroundColor White
    Write-Host "  - Layout detection" -ForegroundColor White
    Write-Host "  - Formula recognition" -ForegroundColor White
    Write-Host "  - Table extraction" -ForegroundColor White
    Write-Host "  - Multi-language OCR" -ForegroundColor White
    Write-Host ""

} else {
    Write-Host ""
    Write-Host "Setup cancelled." -ForegroundColor Yellow
    Write-Host "Run this script again when you're ready to download models." -ForegroundColor Yellow
    Write-Host ""
    exit 0
}
