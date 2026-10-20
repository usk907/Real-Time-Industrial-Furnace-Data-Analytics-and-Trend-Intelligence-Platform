@echo off
title IEIP - Cloudflare Live Public Tunnel
echo ======================================================================
echo    IEIP - Cloudflare Live Edge Tunnel (Remote 4G/5G Access)
echo ======================================================================
echo.

cd /d "%~dp0"

set "CF_CMD=cloudflared"
where cloudflared >nul 2>nul
if %ERRORLEVEL% neq 0 (
    if exist "C:\Program Files (x86)\cloudflared\cloudflared.exe" (
        set "CF_CMD=C:\Program Files (x86)\cloudflared\cloudflared.exe"
    ) else if exist "C:\Program Files\cloudflared\cloudflared.exe" (
        set "CF_CMD=C:\Program Files\cloudflared\cloudflared.exe"
    ) else (
        echo [ERROR] cloudflared is not installed or not in PATH.
        echo To install cloudflared on Windows, run:
        echo    winget install Cloudflare.cloudflared
        echo.
        pause
        exit /b 1
    )
)

echo Starting tunnel on http://localhost:5173...
echo Note: Both Frontend and Backend APIs (/api, /api/ws) will be routed through this public URL!
echo.
"%CF_CMD%" tunnel --url http://localhost:5173

pause
