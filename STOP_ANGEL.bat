@echo off
setlocal EnableExtensions
chcp 65001 >nul
title LocalAI-Angel - Stop Full Stack
color 0E
cd /d "%~dp0" || (echo ERROR: Could not enter the LocalAI-Angel folder.& pause & exit /b 1)
set "COMPOSE=docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml -f docker-compose.angel-harness.yaml"

echo ============================================================
echo             LOCALAI-ANGEL - STOP ALL
echo ============================================================
echo This stops the configured services without deleting containers,
echo downloaded model volumes, or persistent Angel/Nexus data.
echo.
for %%F in (docker-compose.yaml docker-compose.nexus.override.yaml docker-compose.angel-harness.yaml) do (
    if not exist "%%F" (echo ERROR: Missing required file: %%F& pause& exit /b 1)
)
where docker >nul 2>&1 || (echo ERROR: Docker CLI not found.& pause & exit /b 1)
docker info >nul 2>&1 || (echo ERROR: Docker engine is not running. Start Docker Desktop and retry.& pause & exit /b 1)
%COMPOSE% stop
if errorlevel 1 (
    echo ERROR: One or more services could not be stopped.
    %COMPOSE% ps -a
    pause
    exit /b 1
)
echo.
echo Full LocalAI-Angel stack stopped. Persistent data and model volumes were preserved.
echo.
%COMPOSE% ps -a
echo.
pause
exit /b 0
