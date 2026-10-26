@echo off
title IEIP Cloudflare Tunnel (HTTPS/WSS Public Access)
cd /d "%~dp0.."

echo ======================================================================
echo       IEIP SECURE CLOUDFLARE TUNNEL (PUBLIC HTTPS / WSS GATEWAY)
echo ======================================================================
echo Exposing local FastAPI server (http://localhost:8000)...
echo No local ports (3307 or 8000) are directly exposed to the internet.
echo.

where cloudflared >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] 'cloudflared' CLI tool not found in PATH.
    echo Please install Cloudflare Tunnel from: https://github.com/cloudflare/cloudflared/releases
    pause
    exit /b 1
)

cloudflared tunnel --url http://localhost:8000

pause
