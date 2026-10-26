@echo off
title IEIP - Stop All Services
cd /d "%~dp0.."

echo ======================================================================
echo       STOPPING ALL RUNNING IEIP SERVICES
echo ======================================================================
echo.

echo Terminating IEIP processes...
taskkill /FI "WINDOWTITLE eq IEIP*" /T /F >nul 2>&1

echo.
echo [OK] All IEIP platform service windows terminated.
echo.
pause
