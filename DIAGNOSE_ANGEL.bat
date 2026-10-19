@echo off
setlocal EnableExtensions
chcp 65001 >nul
set "REPO=%~dp0"
set "REPORT=%REPO%angel-diagnostics.txt"
set "COMPOSE=docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml"
title LocalAI Angel - Diagnose
cd /d "%REPO%" || goto path_error

>"%REPORT%" echo LocalAI Angel Diagnostic Report
>>"%REPORT%" echo Generated: %date% %time%
>>"%REPORT%" echo Repository: %REPO%
>>"%REPORT%" echo ============================================================

call :section "Required files"
for %%F in (docker-compose.yaml docker-compose.nexus.override.yaml nexus-service\Dockerfile nexus-service\server.py nexus-service\patch_engine.py) do (
  if exist "%%F" (>>"%REPORT%" echo [OK] %%F) else (>>"%REPORT%" echo [MISSING] %%F)
)

call :section "Docker version"
docker version >>"%REPORT%" 2>&1

call :section "Docker Compose version"
docker compose version >>"%REPORT%" 2>&1

call :section "Docker engine"
docker info >>"%REPORT%" 2>&1

call :section "Merged Compose validation"
%COMPOSE% config >>"%REPORT%" 2>&1

call :section "Container status"
%COMPOSE% ps -a >>"%REPORT%" 2>&1

call :section "LocalAI readiness"
curl.exe -i --max-time 10 http://localhost:8080/readyz >>"%REPORT%" 2>&1

call :section "Angel Nexus health"
curl.exe -i --max-time 10 http://localhost:8877/api/health >>"%REPORT%" 2>&1

call :section "Recent container logs"
%COMPOSE% logs --tail 200 >>"%REPORT%" 2>&1

echo.
echo Diagnostic report created:
echo %REPORT%
start "" notepad.exe "%REPORT%"
pause
exit /b 0

:section
>>"%REPORT%" echo.
>>"%REPORT%" echo ============================================================
>>"%REPORT%" echo %~1
>>"%REPORT%" echo ============================================================
exit /b 0

:path_error
echo ERROR: Could not enter the launcher folder.
pause
exit /b 1
