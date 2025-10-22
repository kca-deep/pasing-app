# Development Server Stop Script
# Stops all running Node.js and Python (uvicorn) development servers

Write-Host "Stopping development servers..." -ForegroundColor Cyan
Write-Host ""

# Stop all uvicorn processes (Backend)
Write-Host "Stopping Backend (uvicorn) processes..." -ForegroundColor Yellow
$UvicornProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*uvicorn*"
}

if ($UvicornProcesses) {
    $UvicornProcesses | ForEach-Object {
        Stop-Process -Id $_.Id -Force
        Write-Host "  Stopped process ID: $($_.Id)" -ForegroundColor Green
    }
} else {
    Write-Host "  No uvicorn processes found" -ForegroundColor Gray
}

# Stop all Node.js processes (Frontend)
Write-Host "Stopping Frontend (Node.js) processes..." -ForegroundColor Yellow
$NodeProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue

if ($NodeProcesses) {
    $NodeProcesses | ForEach-Object {
        Stop-Process -Id $_.Id -Force
        Write-Host "  Stopped process ID: $($_.Id)" -ForegroundColor Green
    }
} else {
    Write-Host "  No Node.js processes found" -ForegroundColor Gray
}

# Stop all PowerShell background jobs
Write-Host "Stopping PowerShell background jobs..." -ForegroundColor Yellow
$Jobs = Get-Job -ErrorAction SilentlyContinue

if ($Jobs) {
    $Jobs | ForEach-Object {
        Stop-Job -Id $_.Id
        Remove-Job -Id $_.Id
        Write-Host "  Stopped job ID: $($_.Id)" -ForegroundColor Green
    }
} else {
    Write-Host "  No background jobs found" -ForegroundColor Gray
}

Write-Host ""
Write-Host "All development servers stopped!" -ForegroundColor Cyan
