@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
title LocalAI-Angel - Start Full Stack
color 0B

cd /d "%~dp0" || (
    echo ERROR: Could not enter the LocalAI-Angel folder.
    pause
    exit /b 1
)
set "LOG=%~dp0angel-startup.log"
set "COMPOSE=docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml -f docker-compose.angel-harness.yaml"

echo ============================================================
echo             LOCALAI-ANGEL - START ALL
echo ============================================================
echo Project: %CD%
echo Log: %LOG%
echo.

for %%F in (docker-compose.yaml docker-compose.nexus.override.yaml docker-compose.angel-harness.yaml) do (
    if not exist "%%F" (
        echo ERROR: Missing required file: %%F
        echo Place this BAT file in the LocalAI-Angel repository folder.
        pause
        exit /b 1
    )
)
where docker >nul 2>&1 || (echo ERROR: Docker CLI not found.& pause & exit /b 1)
docker compose version >nul 2>&1 || (echo ERROR: Docker Compose unavailable.& pause & exit /b 1)

docker info >nul 2>&1
if not errorlevel 1 goto DOCKER_READY
echo Docker engine is not ready. Trying to start Docker Desktop...
set "DOCKER_DESKTOP="
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" set "DOCKER_DESKTOP=%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
if exist "%LocalAppData%\Docker\Docker Desktop.exe" set "DOCKER_DESKTOP=%LocalAppData%\Docker\Docker Desktop.exe"
if not defined DOCKER_DESKTOP (
    echo ERROR: Docker Desktop not found in the usual locations. Start it manually.
    pause
    exit /b 1
)
start "" "%DOCKER_DESKTOP%"
set /a WAIT_COUNT=0
:WAIT_DOCKER
timeout /t 5 /nobreak >nul
docker info >nul 2>&1
if not errorlevel 1 goto DOCKER_READY
set /a WAIT_COUNT+=1
echo Waiting for Docker Desktop... !WAIT_COUNT!/36
if !WAIT_COUNT! GEQ 36 (echo ERROR: Docker engine did not become ready within 3 minutes.& pause & exit /b 1)
goto WAIT_DOCKER

:DOCKER_READY
echo.
echo Validating the merged Compose configuration...
%COMPOSE% config --services
if errorlevel 1 (echo ERROR: Compose configuration validation failed.& pause & exit /b 1)
if not exist ".env" if exist ".env.example" (echo Creating .env from .env.example...& copy ".env.example" ".env" >nul)
if not defined ANGEL_DEFAULT_MODEL set "ANGEL_DEFAULT_MODEL=qwen2.5:3b"
if not defined ANGEL_OLLAMA_FALLBACK set "ANGEL_OLLAMA_FALLBACK=true"

echo.
echo Starting the complete stack: LocalAI, Nexus, Angel Harness, Ollama, and model initializer.
echo The model initializer should exit successfully when its one-time task completes.
echo First startup may take longer while images/models download or build.
echo.
%COMPOSE% up -d
if errorlevel 1 (
    echo ERROR: Compose failed to start the stack. Recent logs follow:
    %COMPOSE% logs --tail 80
    >>"%LOG%" echo [%date% %time%] ERROR: Compose up failed.
    pause
    exit /b 1
)

echo.
echo Waiting for Angel Home Base at http://127.0.0.1:8765/ ...
set /a HEALTH_TRIES=0
:WAIT_ANGEL
set "ANGEL_STATE="
for /f "usebackq delims=" %%S in (`docker inspect --format "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}" angel-ai-harness 2^>nul`) do set "ANGEL_STATE=%%S"
if /I "!ANGEL_STATE!"=="healthy" goto ANGEL_READY
curl.exe -fsS --max-time 2 http://127.0.0.1:8765/ >nul 2>&1
if not errorlevel 1 goto ANGEL_READY
set /a HEALTH_TRIES+=1
if !HEALTH_TRIES! GEQ 60 goto ANGEL_TIMEOUT
echo Angel status: !ANGEL_STATE!  (!HEALTH_TRIES!/60)
timeout /t 3 /nobreak >nul
goto WAIT_ANGEL

:ANGEL_READY
echo.
echo Angel Home Base is responding.
echo.
echo ================= CONTAINER STATUS =================
%COMPOSE% ps -a
echo.
echo ================= LOCAL ADDRESSES ==================
echo Angel Home Base:        http://127.0.0.1:8765/
echo LocalAI API/gallery:    http://127.0.0.1:8080/
echo Angel Nexus UI:         http://127.0.0.1:8080/app/angel-nexus
echo Nexus service:          http://127.0.0.1:8877/
echo Engineering/RAG API:    http://127.0.0.1:8780/
echo.
>>"%LOG%" echo [%date% %time%] SUCCESS: Angel Home Base responded.
start "" "http://127.0.0.1:8765/"
echo Startup complete. Review the service status above.
pause
exit /b 0

:ANGEL_TIMEOUT
echo.
echo WARNING: Angel Home Base did not respond within 3 minutes.
echo Container status:
%COMPOSE% ps -a
echo.
echo Recent logs:
%COMPOSE% logs --tail 100
>>"%LOG%" echo [%date% %time%] ERROR: Angel Home Base health wait timed out.
pause
exit /b 1
