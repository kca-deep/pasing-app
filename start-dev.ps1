# Development Server Startup Script
# Starts both Backend (FastAPI) and Frontend (Next.js) in separate windows

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Backend command
$BackendCommand = "Set-Location '$ScriptDir\backend'; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

# Frontend command
$FrontendCommand = "Set-Location '$ScriptDir'; npm run dev"

# Start Backend in new PowerShell window
Write-Host "Starting Backend (FastAPI) on port 8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", $BackendCommand

# Wait a moment before starting frontend
Start-Sleep -Seconds 2

# Start Frontend in new PowerShell window
Write-Host "Starting Frontend (Next.js) on port 3000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", $FrontendCommand

Write-Host ""
Write-Host "Development servers started!" -ForegroundColor Cyan
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Close the opened terminal windows to stop the servers." -ForegroundColor Gray
