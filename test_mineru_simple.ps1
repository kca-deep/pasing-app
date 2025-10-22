# UTF-8 BOM
# MinerU Quick Test

# Set UTF-8 encoding
chcp 65001 > $null
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  MinerU Test" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check server
Write-Host "Checking server..." -ForegroundColor Yellow
try {
    $status = Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get -ErrorAction Stop
    Write-Host "OK - Server running (v$($status.version))" -ForegroundColor Green
} catch {
    Write-Host "ERROR - Server not running!" -ForegroundColor Red
    Write-Host "Start server with: .\start_backend.ps1" -ForegroundColor Yellow
    exit 1
}

# List documents
Write-Host ""
Write-Host "Available documents:" -ForegroundColor Yellow
$docs = Invoke-RestMethod -Uri "http://localhost:8000/documents" -Method Get
for ($i = 0; $i -lt $docs.Count; $i++) {
    Write-Host "  $($i + 1). $($docs[$i].filename)" -ForegroundColor White
}

# Select document
Write-Host ""
$selection = Read-Host "Select number (1-$($docs.Count))"
$file = $docs[[int]$selection - 1].filename

# Parse
Write-Host ""
Write-Host "Parsing: $file" -ForegroundColor Yellow
Write-Host "Please wait (10-60 seconds)..." -ForegroundColor Gray

$body = @{
    filename = $file
    options = @{
        parsing_method = "mineru"
        save_to_output_folder = $true
    }
} | ConvertTo-Json

$result = Invoke-RestMethod `
    -Uri "http://localhost:8000/parse" `
    -Method Post `
    -ContentType "application/json; charset=utf-8" `
    -Body $body `
    -TimeoutSec 300

# Show results
Write-Host ""
Write-Host "=== Results ===" -ForegroundColor Green
Write-Host "Tables: $($result.stats.tables)" -ForegroundColor White
Write-Host "Images: $($result.stats.images)" -ForegroundColor White
Write-Host "Formulas: $($result.stats.formulas)" -ForegroundColor White
Write-Host "Pages: $($result.stats.pages)" -ForegroundColor White
Write-Host ""
Write-Host "Saved: $($result.saved_file)" -ForegroundColor Cyan
Write-Host ""
