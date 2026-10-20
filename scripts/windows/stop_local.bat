@echo off
title IEIP - Stop All Services
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0stop_local.ps1"
pause
