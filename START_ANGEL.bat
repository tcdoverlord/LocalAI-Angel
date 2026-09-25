@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

set "REPO=%~dp0"
set "LOG=%REPO%angel-startup.log"
set "LOCALAI_URL=http://localhost:8080"
set "LOCALAI_HEALTH=http://localhost:8080/readyz"
set "NEXUS_HEALTH=http://localhost:8877/api/health"
set "COMPOSE=docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml"

title LocalAI Angel - Start
color 0B

call :log "START requested"
echo ============================================================
echo                 LocalAI Angel Launcher
echo ============================================================
echo Repository: %REPO%
echo.

if not exist "%REPO%docker-compose.yaml" (
    call :fatal "docker-compose.yaml is missing. Put this launcher in the LocalAI-Angel repository root."
    goto :eof
)
if not exist "%REPO%docker-compose.nexus.override.yaml" (
    call :fatal "docker-compose.nexus.override.yaml is missing."
    goto :eof
)
if not exist "%REPO%nexus-service\Dockerfile" (
    call :fatal "nexus-service\Dockerfile is missing."
    goto :eof
)

cd /d "%REPO%" || (
    call :fatal "Could not enter the repository folder."
    goto :eof
)

where docker >nul 2>&1 || (
    call :fatal "Docker is not installed or is not available in PATH. Install Docker Desktop, then try again."
    goto :eof
)

docker compose version >nul 2>&1 || (
    call :fatal "Docker Compose is unavailable. Update or repair Docker Desktop."
    goto :eof
)

docker info >nul 2>&1
if not errorlevel 1 goto docker_ready

call :log "Docker engine is not running; attempting to start Docker Desktop"
set "DOCKER_DESKTOP="
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" set "DOCKER_DESKTOP=%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
if exist "%LocalAppData%\Docker\Docker Desktop.exe" set "DOCKER_DESKTOP=%LocalAppData%\Docker\Docker Desktop.exe"
if not defined DOCKER_DESKTOP (
    call :fatal "Docker Desktop was not found in its standard install locations."
    goto :eof
)

start "" "%DOCKER_DESKTOP%"
echo Waiting for Docker Desktop...
set /a tries=0

:wait_docker
timeout /t 5 /nobreak >nul
docker info >nul 2>&1
if not errorlevel 1 goto docker_ready
set /a tries+=1
echo Still waiting for Docker... !tries!/36
if !tries! GEQ 36 (
    call :fatal "Docker did not become ready within 3 minutes."
    goto :eof
)
goto wait_docker

:docker_ready
call :log "Docker engine ready"
echo Validating Compose configuration...
%COMPOSE% config >nul 2>>"%LOG%"
if errorlevel 1 (
    call :fatal "Compose validation failed. See angel-startup.log."
    goto :eof
)

call :log "Starting LocalAI and Angel Nexus"
echo.
echo Checking existing Angel Nexus container...
set "NEXUS_EXISTS="
set "NEXUS_PROJECT="
set "NEXUS_SERVICE="

docker inspect angel-nexus-service >nul 2>&1
if errorlevel 1 (
    echo No existing angel-nexus-service container found.
) else (
    for /f "delims=" %%A in ('docker inspect -f "{{index .Config.Labels \"com.docker.compose.project\"}}" angel-nexus-service 2^>nul') do set "NEXUS_PROJECT=%%A"
    for /f "delims=" %%A in ('docker inspect -f "{{index .Config.Labels \"com.docker.compose.service\"}}" angel-nexus-service 2^>nul') do set "NEXUS_SERVICE=%%A"

    echo Existing container project: !NEXUS_PROJECT!
    echo Existing container service: !NEXUS_SERVICE!

    if /i "!NEXUS_PROJECT!"=="localai-angel" if /i "!NEXUS_SERVICE!"=="nexus" (
        echo Existing Angel Nexus container belongs to this Compose project. Keeping it.
    ) else (
        echo Existing angel-nexus-service is stale or belongs to another Compose project.
        echo Removing only the conflicting container...
        docker rm -f angel-nexus-service
        if errorlevel 1 (
            call :fatal "Could not remove the conflicting angel-nexus-service container."
            goto :eof
        )
        echo Conflicting container removed.
    )
)

echo.
echo Starting LocalAI and Angel Nexus...
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml up -d
if errorlevel 1 (
    call :fatal "Docker Compose startup failed. The Docker output above contains the actual error."
    goto :eof
)

echo.
echo Container status:
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml ps


echo.
echo Waiting for LocalAI...
set /a localai_tries=0
:wait_localai
curl.exe -fsS "%LOCALAI_HEALTH%" >nul 2>&1
if not errorlevel 1 goto localai_ready
set /a localai_tries+=1
if !localai_tries! GEQ 60 goto health_failed
timeout /t 3 /nobreak >nul
goto wait_localai

:localai_ready
call :log "LocalAI ready"
echo LocalAI is ready.
echo Waiting for Angel Nexus...
set /a nexus_tries=0

:wait_nexus
curl.exe -fsS "%NEXUS_HEALTH%" >nul 2>&1
if not errorlevel 1 goto all_ready
set /a nexus_tries+=1
if !nexus_tries! GEQ 60 goto health_failed
timeout /t 3 /nobreak >nul
goto wait_nexus

:all_ready
call :log "Angel Nexus healthy"
echo Angel Nexus is healthy.
start "" "%LOCALAI_URL%"
echo.
echo ============================================================
echo LocalAI Angel is running.
echo LocalAI: %LOCALAI_URL%
echo Nexus health: %NEXUS_HEALTH%
echo Log: %LOG%
echo ============================================================
echo.
pause
exit /b 0

:health_failed
call :log "Health check timed out"
echo.
echo Containers started, but a health check timed out.
echo Run DIAGNOSE_ANGEL.bat for a complete report.
echo.
%COMPOSE% ps
pause
exit /b 1

:fatal
echo.
echo ERROR: %~1
call :log "ERROR: %~1"
echo Log: %LOG%
echo.
pause
exit /b 1

:log
>>"%LOG%" echo [%date% %time%] %~1
exit /b 0
