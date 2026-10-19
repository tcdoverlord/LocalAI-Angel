@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title LocalAI Angel Unified v1.0.0 - Installer
color 0B
echo ============================================================
echo       LOCALAI ANGEL UNIFIED - VERSION 1.0.0
echo                  FIRST-TIME INSTALL
echo ============================================================
echo This builds and starts the unified LocalAI + Angel Harness + Nexus stack.
echo Existing Compose volumes and persistent data are not deleted.
echo First install may take a long time and download the default model.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0INSTALL_ANGEL_V1.0.0.ps1"
if errorlevel 1 (
  echo.
  echo Installation failed. Review the error above and angel-v1-install.log.
  pause
  exit /b 1
)
echo.
echo Installation and endpoint checks completed.
echo Use RUN_ANGEL_V1.0.0.bat for future starts and STOP_ANGEL_V1.0.0.bat to stop.
pause
endlocal
