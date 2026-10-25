@echo off
title IEIP FastAPI Server (Part 2)
cd /d "%~dp0..\.."

echo ======================================================================
echo       IEIP INDUSTRIAL ENERGY SERVER (PART 2 - FASTAPI)
echo ======================================================================
echo Starting server on http://127.0.0.1:8001...
echo.

if exist "server\venv\Scripts\python.exe" (
    "server\venv\Scripts\python.exe" -m uvicorn server.app.main:app --host 127.0.0.1 --port 8001 --reload
) else (
    python -m uvicorn server.app.main:app --host 127.0.0.1 --port 8001 --reload
)

pause
