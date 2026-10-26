@echo off
title IEIP - Industrial Energy Intelligence Platform
cd /d "%~dp0.."

echo ======================================================================
echo    STARTING IEIP PLATFORM (GENERATOR, SERVER, AND CLIENT)
echo ======================================================================
echo.

echo [1/3] Starting Telemetry Generator (Part 1)...
start "IEIP Telemetry Generator" cmd /k "scripts\start_generator.bat"
timeout /t 2 /nobreak >nul

echo [2/3] Starting FastAPI Backend Server (Part 2)...
start "IEIP Backend Server" cmd /k "scripts\start_server.bat"
timeout /t 3 /nobreak >nul

echo [3/3] Starting Frontend Dashboard (Part 3)...
start "IEIP Frontend Dashboard" cmd /k "scripts\start_client.bat"

echo.
echo ======================================================================
echo  ALL 3 SERVICES LAUNCHED!
echo  - Generator: Emitting 60 tags/sec to MySQL (port 3307)
echo  - Server:    http://127.0.0.1:8000 (API & WebSocket)
echo  - Client:    http://127.0.0.1:5173 (Control Dashboard)
echo ======================================================================
echo To stop all services, run scripts\stop_all.bat
echo.
pause
