#!/usr/bin/env pwsh
# MinerU 파싱 테스트 스크립트 (UTF-8 인코딩 지원)

param(
    [Parameter(Mandatory=$false)]
    [string]$Filename = ""
)

# UTF-8 인코딩 설정
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MinerU Parsing Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if server is running
try {
    Write-Host "Step 1: Checking API server..." -ForegroundColor Yellow
    $status = Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get -ErrorAction Stop
    Write-Host "  OK - Server is running" -ForegroundColor Green
    Write-Host "  Version: $($status.version)" -ForegroundColor White
    Write-Host "  MinerU available: $($status.mineru)" -ForegroundColor White
} catch {
    Write-Host "  ERROR - Server is not running!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please start the server first:" -ForegroundColor Yellow
    Write-Host "  .\start_backend.ps1" -ForegroundColor White
    exit 1
}

# List available documents
Write-Host ""
Write-Host "Step 2: Checking available documents..." -ForegroundColor Yellow
try {
    $docs = Invoke-RestMethod -Uri "http://localhost:8000/documents" -Method Get
    Write-Host "  Found $($docs.Count) document(s) in /docu folder:" -ForegroundColor Green
    foreach ($doc in $docs) {
        Write-Host "    - $($doc.filename) ($($doc.size_mb) MB)" -ForegroundColor White
    }
} catch {
    Write-Host "  ERROR - Failed to list documents" -ForegroundColor Red
    exit 1
}

# Select file to parse
if ($Filename -eq "") {
    if ($docs.Count -eq 0) {
        Write-Host ""
        Write-Host "No documents found in /docu folder!" -ForegroundColor Red
        Write-Host "Please add a PDF file to the /docu folder and try again." -ForegroundColor Yellow
        exit 1
    }

    Write-Host ""
    Write-Host "Select a document to parse:" -ForegroundColor Yellow
    for ($i = 0; $i -lt $docs.Count; $i++) {
        Write-Host "  $($i + 1). $($docs[$i].filename)" -ForegroundColor White
    }

    $selection = Read-Host "Enter number (1-$($docs.Count))"
    $selectedIndex = [int]$selection - 1

    if ($selectedIndex -lt 0 -or $selectedIndex -ge $docs.Count) {
        Write-Host "Invalid selection!" -ForegroundColor Red
        exit 1
    }

    $Filename = $docs[$selectedIndex].filename
}

Write-Host ""
Write-Host "Step 3: Parsing document with MinerU..." -ForegroundColor Yellow
Write-Host "  File: $Filename" -ForegroundColor White
Write-Host "  This may take 10-60 seconds..." -ForegroundColor White
Write-Host ""

# Parse document
try {
    $body = @{
        filename = $Filename
        options = @{
            parsing_method = "mineru"
            save_to_output_folder = $true
            output_format = "markdown"
        }
    } | ConvertTo-Json

    $result = Invoke-RestMethod `
        -Uri "http://localhost:8000/parse" `
        -Method Post `
        -ContentType "application/json; charset=utf-8" `
        -Body $body `
        -TimeoutSec 300

    Write-Host "OK - Parsing completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Results:" -ForegroundColor Cyan
    Write-Host "  Method: $($result.parsing_method)" -ForegroundColor White
    Write-Host "  Tables: $($result.stats.tables)" -ForegroundColor White
    Write-Host "  Images: $($result.stats.images)" -ForegroundColor White
    Write-Host "  Formulas: $($result.stats.formulas)" -ForegroundColor White
    Write-Host "  Pages: $($result.stats.pages)" -ForegroundColor White

    if ($result.saved_file) {
        Write-Host ""
        Write-Host "Saved to: $($result.saved_file)" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "Content preview (first 500 chars):" -ForegroundColor Cyan
    $preview = $result.content.Substring(0, [Math]::Min(500, $result.content.Length))
    Write-Host $preview -ForegroundColor White
    Write-Host ""

} catch {
    Write-Host "ERROR - Parsing failed!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Test completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
