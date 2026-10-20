@echo off
title IEIP - Stop All Services
echo ======================================================================
echo    IEIP - Stopping All Local Services
echo ======================================================================
echo.

echo Terminating processes on Port 8000 (Backend)...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host 'Stopped PID:' $_.OwningProcess }"

echo Terminating processes on Port 8001 (TAP Server)...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host 'Stopped PID:' $_.OwningProcess }"

echo Terminating processes on Port 5173 (Vite Frontend)...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host 'Stopped PID:' $_.OwningProcess }"

echo Stopping SCADA Simulator python instances...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*scada_simulator.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; Write-Host 'Stopped Simulator PID:' $_.ProcessId }"

echo.
echo ======================================================================
echo  All IEIP services have been stopped.
echo ======================================================================
echo.
pause
