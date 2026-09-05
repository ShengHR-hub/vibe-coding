@echo off
title Inkstone Dev Stopper
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop-dev.ps1" -Force
echo.
pause
