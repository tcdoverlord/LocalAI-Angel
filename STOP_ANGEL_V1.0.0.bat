@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title LocalAI Angel Unified v1.0.0 - Stop
color 0B
echo ============================================================
echo       LOCALAI ANGEL UNIFIED v1.0.0 - STOP
echo ============================================================
where docker >nul 2>nul || (echo ERROR: Docker CLI not found.& pause & exit /b 1)
echo This stops the unified stack only. It does NOT delete containers, volumes, models, history, knowledge, or Nexus data.
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml -f docker-compose.angel-harness.yaml stop
if errorlevel 1 (echo ERROR: One or more services could not be stopped.& pause & exit /b 1)
echo.
echo Angel Unified is stopped. Persistent data has been preserved.
pause
endlocal
