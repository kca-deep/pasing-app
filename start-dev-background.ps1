# Development Server Startup Script (Background Jobs)
# Starts both Backend (FastAPI) and Frontend (Next.js) as background jobs in the current terminal

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Starting development servers as background jobs..." -ForegroundColor Cyan
Write-Host ""

# Start Backend as background job
Write-Host "Starting Backend (FastAPI) on port 8000..." -ForegroundColor Green
$BackendJob = Start-Job -ScriptBlock {
    param($Path)
    Set-Location $Path
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
} -ArgumentList "$ScriptDir\backend"

# Wait a moment before starting frontend
Start-Sleep -Seconds 2

# Start Frontend as background job
Write-Host "Starting Frontend (Next.js) on port 3000..." -ForegroundColor Green
$FrontendJob = Start-Job -ScriptBlock {
    param($Path)
    Set-Location $Path
    npm run dev
} -ArgumentList $ScriptDir

Write-Host ""
Write-Host "Development servers started!" -ForegroundColor Cyan
Write-Host "Backend Job ID:  $($BackendJob.Id)" -ForegroundColor Yellow
Write-Host "Frontend Job ID: $($FrontendJob.Id)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Gray
Write-Host "  Get-Job                    - List all background jobs" -ForegroundColor Gray
Write-Host "  Receive-Job -Id <id>       - View job output" -ForegroundColor Gray
Write-Host "  Stop-Job -Id <id>          - Stop a specific job" -ForegroundColor Gray
Write-Host "  Remove-Job -Id <id>        - Remove a stopped job" -ForegroundColor Gray
Write-Host ""
Write-Host "To stop all servers, run:" -ForegroundColor Gray
Write-Host "  Stop-Job -Id $($BackendJob.Id),$($FrontendJob.Id); Remove-Job -Id $($BackendJob.Id),$($FrontendJob.Id)" -ForegroundColor White
