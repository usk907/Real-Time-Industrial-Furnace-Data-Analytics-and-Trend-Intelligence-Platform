@echo off
title IEIP Database & Users Setup
cd /d "%~dp0..\.."

echo ======================================================================
echo          IEIP MySQL DATABASE ^& USERS SETUP
echo ======================================================================
echo.

if exist "server\venv\Scripts\python.exe" (
    "server\venv\Scripts\python.exe" scripts\setup_mysql.py
) else if exist "generator\venv\Scripts\python.exe" (
    "generator\venv\Scripts\python.exe" scripts\setup_mysql.py
) else (
    python scripts\setup_mysql.py
)

echo.
pause
