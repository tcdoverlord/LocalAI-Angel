@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title LocalAI-Angel v1.0.0 - Install / Repair
color 0B
echo ============================================================
echo       LOCALAI-ANGEL UNIFIED - INSTALL / REPAIR
echo ============================================================
echo Works for first-time installation and repeat repair/update runs.
echo Existing .env settings and Docker data/model volumes are preserved.
echo This script does not run docker compose down -v or delete volumes.
echo First build may take a while and download large images.
echo.
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0INSTALL_ANGEL_V1.0.0.ps1"
set "INSTALL_EXIT=%ERRORLEVEL%"
if not "%INSTALL_EXIT%"=="0" (
  echo.
  echo INSTALL / REPAIR FAILED. Review angel-v1-install.log and the errors above.
  pause
  exit /b %INSTALL_EXIT%
)
echo.
echo INSTALL / REPAIR SUCCEEDED.
echo Use START_ANGEL.bat for normal startup and STOP_ANGEL.bat to stop the stack.
pause
endlocal
exit /b 0
