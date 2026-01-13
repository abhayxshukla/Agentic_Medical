# Medical Assistant - Startup Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Medical Assistant - Full Stack" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Start Backend
Write-Host "Starting Backend Server (Port 5005)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath'; python main.py" -WindowStyle Normal

Start-Sleep -Seconds 3

# Start Frontend
Write-Host "Starting Frontend Server (Port 8000)..." -ForegroundColor Green
$frontendPath = Join-Path $scriptPath "frontend-geo"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; python -m http.server 8000" -WindowStyle Normal

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Servers Starting..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Backend:  http://localhost:5005" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Opening frontend in browser..." -ForegroundColor Green
Start-Process "http://localhost:8000"

Write-Host ""
Write-Host "Servers are running in separate windows." -ForegroundColor Green
Write-Host "Close those windows to stop the servers." -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
