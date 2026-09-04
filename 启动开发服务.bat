@echo off
title Inkstone Dev Launcher
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-dev.ps1" %*
echo.
pause
