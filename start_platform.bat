@echo off
title SCADA Furnace Data Analytics and Trend Intelligence Platform Launcher
echo =========================================================================
echo  SCADA Furnace Analytics Platform Local Host Launcher (Dockerless)
echo =========================================================================
echo.

:: 1. Launch FastAPI Backend
echo [1/3] Spinning up FastAPI Backend in a separate window...
start "FastAPI Backend Server" cmd /k "cd backend && (if not exist venv (echo Creating virtualenv... && python -m venv venv)) && call venv\Scripts\activate && echo Installing dependencies... && pip install -r requirements.txt && echo Launching FastAPI on port 8000... && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

:: 2. Launch SCADA Simulator
echo [2/3] Spinning up SCADA Telemetry Simulator in a separate window...
start "SCADA Telemetry Simulator" cmd /k "cd simulator && (if not exist venv (echo Creating virtualenv... && python -m venv venv)) && call venv\Scripts\activate && echo Installing dependencies... && pip install -r requirements.txt && echo Launching SCADA telemetry loop (1 Hz)... && python scada_simulator.py"

:: 3. Launch React Frontend
echo [3/3] Spinning up Vite React Dev Server in a separate window...
start "React Dashboard Frontend" cmd /k "cd frontend && (if not exist node_modules (echo Installing Node packages... && npm install)) && echo Launching Vite local server on port 3000... && npm run dev -- --port 3000"

echo.
echo =========================================================================
echo  Startup triggers completed!
echo  - Backend: http://127.0.0.1:8000
echo  - Frontend Dashboard: http://localhost:3000
echo  Please ensure your local PostgreSQL database is running on port 5432.
echo =========================================================================
pause
