@echo off
title IEIP Client Website (Part 3)
cd /d "%~dp0..\..\client"

echo ======================================================================
echo       IEIP FRONTEND DASHBOARD (PART 3 - REACT / VITE)
echo ======================================================================
echo Starting Vite dev server on http://127.0.0.1:5174...
echo.

npm run dev -- --host 127.0.0.1 --port 5174

pause
