# IEIP - Industrial Energy Intelligence Platform Local Stack Launcher
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   IEIP - Industrial Energy Intelligence Platform (All-In-One Launcher)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

$RootPath = (Resolve-Path "$PSScriptRoot\..\..").Path
Set-Location $RootPath

# 1. Verify Virtual Environments
if (-not (Test-Path "$RootPath\generator\venv\Scripts\python.exe")) {
    Write-Host "[ERROR] generator\venv not found! Run: python -m venv generator\venv" -ForegroundColor Red
    pause
    exit 1
}

if (-not (Test-Path "$RootPath\server\venv\Scripts\python.exe")) {
    Write-Host "[ERROR] server\venv not found! Run: python -m venv server\venv" -ForegroundColor Red
    pause
    exit 1
}

# 2. Check and Start MySQL Database on port 3307
Write-Host "[1/4] Checking MySQL Database on port 3307..." -ForegroundColor Yellow
$conn = Get-NetTCPConnection -LocalPort 3307 -ErrorAction SilentlyContinue
if (-not $conn) {
    Write-Host "Starting MySQL on port 3307 using PowerPlus local_db..." -ForegroundColor Cyan
    $MysqldPath = "C:\Program Files\MySQL\MySQL Server 5.7\bin\mysqld.exe"
    $DataDir = "C:\Users\kusha\New folder (2)\PowerPlus\local_db"
    if (Test-Path $MysqldPath) {
        Start-Process $MysqldPath -ArgumentList "--datadir=`"$DataDir`" --port=3307" -WindowStyle Hidden
        Start-Sleep -Seconds 3
    }
}

$CheckDbScript = "import pymysql; pymysql.connect(host='127.0.0.1', port=3307, user='generator_user', password='GenPassword123!', database='furnace_db')"
$DbOk = & "$RootPath\generator\venv\Scripts\python.exe" -c "$CheckDbScript" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] Could not connect to MySQL as generator_user on port 3307." -ForegroundColor Yellow
} else {
    Write-Host "[OK] MySQL connection on port 3307 to furnace_db verified." -ForegroundColor Green
}

# 3. Start Telemetry Generator (Part 1)
Write-Host "[2/4] Starting 60-Tag Telemetry Generator (Part 1)..." -ForegroundColor Yellow
Start-Process cmd -ArgumentList "/k", "title IEIP Telemetry Generator (Part 1) && cd /d `"$RootPath\generator`" && venv\Scripts\python.exe generator.py" -WindowStyle Normal

Start-Sleep -Seconds 2

# 4. Start FastAPI Backend Server (Part 2)
Write-Host "[3/4] Starting FastAPI Server on http://localhost:8001 (Part 2)..." -ForegroundColor Yellow
Start-Process cmd -ArgumentList "/k", "title IEIP FastAPI Server (Part 2) && cd /d `"$RootPath`" && server\venv\Scripts\python.exe -m uvicorn server.app.main:app --host 127.0.0.1 --port 8001 --reload" -WindowStyle Normal

Start-Sleep -Seconds 2

# 5. Start React + Vite Client (Part 3)
Write-Host "[4/4] Starting React + Vite Client on http://localhost:5174 (Part 3)..." -ForegroundColor Yellow
Start-Process cmd -ArgumentList "/k", "title IEIP Client Website (Part 3) && cd /d `"$RootPath\client`" && npm run dev -- --host 127.0.0.1 --port 5174" -WindowStyle Normal

Start-Sleep -Seconds 3

# 6. Launch Web Browser
Write-Host ""
Write-Host "Launching Web Browser..." -ForegroundColor Cyan
Start-Process "http://localhost:5174"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host " IEIP All-in-One Stack successfully initialized!" -ForegroundColor Green
Write-Host ""
Write-Host " - Frontend Web Dashboard: http://localhost:5174" -ForegroundColor White
Write-Host " - Backend REST API:        http://127.0.0.1:8001" -ForegroundColor White
Write-Host " - Interactive API Docs:    http://127.0.0.1:8001/docs" -ForegroundColor White
Write-Host " - WebSocket Live Stream:   ws://127.0.0.1:8001/api/ws" -ForegroundColor White
Write-Host ""
Write-Host " * To expose to Mobile 4G/5G or Remote Web, run 'scripts\windows\start_tunnel.bat'" -ForegroundColor Gray
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
