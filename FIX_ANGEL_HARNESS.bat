@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title LocalAI-Angel - Repair Angel Backend and History
color 0B
echo ============================================================
echo    Angel Harness Backend + Persistent History Repair
echo ============================================================
where docker >nul 2>nul || (echo ERROR: Docker CLI not found.& pause & exit /b 1)
docker info >nul 2>nul || (echo ERROR: Start Docker Desktop first.& pause & exit /b 1)
if not exist "Angel_Platform_Data" mkdir "Angel_Platform_Data"
set "COMPOSE=docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml -f docker-compose.angel-harness.yaml"
echo.
echo [1/5] Saving existing Angel container history before replacement...
REM Copy legacy container data first; never overwrite files already in the host data folder.
docker inspect angel-ai-harness >nul 2>nul
if not errorlevel 1 (
  docker stop angel-ai-harness >nul 2>nul
  if not exist "_angel-history-migration" mkdir "_angel-history-migration"
  docker cp angel-ai-harness:/root/Angel_Platform/. "_angel-history-migration" >nul 2>nul
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$src=Join-Path (Get-Location) '_angel-history-migration'; $dst=Join-Path (Get-Location) 'Angel_Platform_Data'; if(Test-Path $src){Get-ChildItem -LiteralPath $src -Force -File -Recurse | ForEach-Object {$rel=$_.FullName.Substring($src.Length).TrimStart('\'); $target=Join-Path $dst $rel; if(-not (Test-Path -LiteralPath $target)){New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null; Copy-Item -LiteralPath $_.FullName -Destination $target}}}"
)
echo.
echo [2/5] Ensuring persistent data directory exists...
if not exist "Angel_Platform_Data" mkdir "Angel_Platform_Data"
echo.
echo [3/5] Rebuilding ONLY the Angel Harness (not LocalAI/Nexus)...
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml -f docker-compose.angel-harness.yaml build angel-harness
if errorlevel 1 goto :failed
echo.
echo [4/5] Starting Ollama and confirming llama3.2:3b is present...
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml -f docker-compose.angel-harness.yaml up -d --no-build ollama
if errorlevel 1 goto :failed
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml -f docker-compose.angel-harness.yaml run --rm ollama-model-init
if errorlevel 1 goto :failed
echo.
echo [5/5] Recreating only the Angel Harness with the fixed backend and data mount...
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml -f docker-compose.angel-harness.yaml up -d --no-build --force-recreate angel-harness
if errorlevel 1 goto :failed
echo.
echo Repair complete. Run RUN_ANGEL.bat for everyday startup.
echo User history is stored in .\Angel_Platform_Data and is not deleted.
echo.
pause
exit /b 0
:failed
echo.
echo Repair did not complete. Diagnostics follow:
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml -f docker-compose.angel-harness.yaml ps -a
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml -f docker-compose.angel-harness.yaml logs --tail 80 angel-harness ollama ollama-model-init
pause
exit /b 1
