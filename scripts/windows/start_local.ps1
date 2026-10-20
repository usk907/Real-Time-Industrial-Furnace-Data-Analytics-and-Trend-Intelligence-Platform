# IEIP - Industrial Energy Intelligence Platform Local Stack Launcher
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   IEIP - Industrial Energy Intelligence Platform Launcher" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

$RootPath = (Resolve-Path "$PSScriptRoot\..\..").Path
Set-Location $RootPath

# 1. Check Python Venvs
if (-not (Test-Path "$RootPath\backend\venv\Scripts\python.exe")) {
    Write-Host "[ERROR] backend\venv not found! Please create it." -ForegroundColor Red
    pause
    exit 1
}

if (-not (Test-Path "$RootPath\simulator\venv\Scripts\python.exe")) {
    Write-Host "[ERROR] simulator\venv not found! Please create it." -ForegroundColor Red
    pause
    exit 1
}

Write-Host "[1/5] Starting TAP Ingestion Server on http://localhost:8001..." -ForegroundColor Yellow
Start-Process cmd -ArgumentList "/k", "cd /d `"$RootPath`" && call backend\venv\Scripts\activate.bat && uvicorn tap_server.main:app --host 0.0.0.0 --port 8001" -WindowStyle Normal

Write-Host "[2/5] Starting Main FastAPI Backend on http://localhost:8000..." -ForegroundColor Yellow
Start-Process cmd -ArgumentList "/k", "cd /d `"$RootPath`" && call backend\venv\Scripts\activate.bat && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000" -WindowStyle Normal

Start-Sleep -Seconds 2

Write-Host "[3/5] Starting 1 Hz SCADA Telemetry Simulator..." -ForegroundColor Yellow
Start-Process cmd -ArgumentList "/k", "cd /d `"$RootPath`" && call simulator\venv\Scripts\activate.bat && python simulator\scada_simulator.py" -WindowStyle Normal

Write-Host "[4/5] Starting React + Vite Frontend on http://localhost:5173..." -ForegroundColor Yellow
Start-Process cmd -ArgumentList "/k", "cd /d `"$RootPath\frontend`" && npm run dev" -WindowStyle Normal

Start-Sleep -Seconds 3

Write-Host "[5/5] Launching Web Browser..." -ForegroundColor Yellow
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host " IEIP Stack successfully initialized!" -ForegroundColor Green
Write-Host ""
Write-Host " - Frontend Web Dashboard: http://localhost:5173" -ForegroundColor White
Write-Host " - Backend REST API:        http://localhost:8000" -ForegroundColor White
Write-Host " - Interactive API Docs:    http://localhost:8000/docs" -ForegroundColor White
Write-Host " - TAP Ingestion Server:    http://localhost:8001" -ForegroundColor White
Write-Host " - Live WebSocket Stream:   ws://localhost:8000/api/ws" -ForegroundColor White
Write-Host ""
Write-Host " * To expose to Mobile 4G/5G or Remote Web, run 'scripts\windows\tunnel.bat'" -ForegroundColor Gray
Write-Host " * To stop all services cleanly, run 'scripts\windows\stop_local.bat'" -ForegroundColor Gray
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
