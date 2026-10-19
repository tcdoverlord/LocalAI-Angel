@echo off
setlocal EnableExtensions
chcp 65001 >nul
set "REPO=%~dp0"
set "COMPOSE=docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml"
title LocalAI Angel - Stop
cd /d "%REPO%" || goto error
where docker >nul 2>&1 || goto no_docker

echo Stopping LocalAI Angel without deleting containers, models, or Nexus data...
%COMPOSE% stop
if errorlevel 1 goto error

echo.
echo LocalAI Angel has stopped. Persistent data was preserved.
pause
exit /b 0

:no_docker
echo ERROR: Docker is not available in PATH.
pause
exit /b 1

:error
echo ERROR: The stack could not be stopped. Run DIAGNOSE_ANGEL.bat.
pause
exit /b 1
