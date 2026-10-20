@echo off
title IEIP - Industrial Energy Intelligence Platform
echo ======================================================================
echo    IEIP - Industrial Energy Intelligence Platform Launcher
echo ======================================================================
echo.

cd /d "%~dp0"

:: 1. Check Python Venvs
if not exist "backend\venv\Scripts\python.exe" (
    echo [ERROR] backend\venv not found! Please create it or install requirements.
    pause
    exit /b 1
)

if not exist "simulator\venv\Scripts\python.exe" (
    echo [ERROR] simulator\venv not found! Please create it or install requirements.
    pause
    exit /b 1
)

:: 2. Check Node modules in frontend
if not exist "frontend\node_modules" (
    echo [INFO] frontend\node_modules missing. Running npm install...
    cd frontend && call npm install && cd ..
)

echo [1/5] Starting TAP Ingestion Server on http://localhost:8001...
start "IEIP TAP Server (Port 8001)" cmd /k "cd /d "%~dp0" && call backend\venv\Scripts\activate.bat && uvicorn tap_server.main:app --host 0.0.0.0 --port 8001"

echo [2/5] Starting Main FastAPI Backend on http://localhost:8000...
start "IEIP Main Backend (Port 8000)" cmd /k "cd /d "%~dp0" && call backend\venv\Scripts\activate.bat && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"

timeout /t 2 >nul

echo [3/5] Starting 1 Hz SCADA Telemetry Simulator...
start "IEIP SCADA Simulator (1 Hz)" cmd /k "cd /d "%~dp0" && call simulator\venv\Scripts\activate.bat && python simulator\scada_simulator.py"

echo [4/5] Starting React + Vite Frontend on http://localhost:5173...
start "IEIP Frontend (Vite)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

timeout /t 3 >nul

echo [5/5] Launching Web Browser...
start http://localhost:5173

echo.
echo ======================================================================
echo  IEIP Stack successfully initialized!
echo.
echo  - Frontend Web Dashboard: http://localhost:5173
echo  - Backend REST API:        http://localhost:8000
echo  - Interactive API Docs:    http://localhost:8000/docs
echo  - TAP Ingestion Server:    http://localhost:8001
echo  - TAP Server Docs:         http://localhost:8001/docs
echo  - Live WebSocket Stream:   ws://localhost:8000/api/ws
echo.
echo  * To expose to Mobile 4G/5G or Remote Web, run 'tunnel.bat'
echo  * To stop all services cleanly, run 'stop_local.bat'
echo ======================================================================
echo.
pause
