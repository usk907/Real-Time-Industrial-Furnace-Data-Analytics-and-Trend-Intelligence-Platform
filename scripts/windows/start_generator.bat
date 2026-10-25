@echo off
title IEIP Telemetry Generator (Part 1)
cd /d "%~dp0..\..\generator"

echo ======================================================================
echo       IEIP TELEMETRY GENERATOR (PART 1 - MySQL STREAM)
echo ======================================================================
echo Starting 60-tag industrial furnace data generator...
echo Writing to MySQL tables: furnace_readings and furnace_latest
echo.

if exist "..\server\venv\Scripts\python.exe" (
    "..\server\venv\Scripts\python.exe" generator.py
) else (
    python generator.py
)

pause
