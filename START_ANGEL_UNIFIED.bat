@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
echo ========================================
echo   LocalAI-Angel Unified 0.3.0 Launcher
echo ========================================
echo.
where docker >nul 2>nul
if errorlevel 1 (
  echo Docker CLI was not found. Install Docker Desktop, start it, and retry.
  pause
  exit /b 1
)
if not exist ".env" if exist ".env.example" copy ".env.example" ".env" >nul
set "ANGEL_USER_PROFILE=%USERPROFILE:\=/%"
if defined ANGEL_USER_PROFILE set "ANGEL_USER_DATA=%ANGEL_USER_PROFILE%/Angel_Platform"
if not defined ANGEL_USER_DATA set "ANGEL_USER_DATA=./Angel_Platform_Data"
echo Persistent chat, memory, and knowledge data: %ANGEL_USER_DATA%
echo.
echo IMPORTANT: Close any standalone Angel Harness window using the same data folder before continuing.
if exist "%USERPROFILE%\Angel_Platform\angel_intelligence.sqlite3" (
  set /p "CONTINUE=Existing Angel SQLite history detected. Continue using it in place (Y/N)? "
  if /I not "!CONTINUE!"=="Y" (
    echo Startup cancelled. Back up your existing Angel_Platform folder, then retry.
    pause
    exit /b 1
  )
)
echo Building LocalAI-Angel, Nexus, and the Angel Harness runtime.
echo Angel's default model is provisioned automatically on first launch.
echo The model download is several gigabytes and can take time; later launches reuse it.
echo The first LocalAI source build can also take a while and needs substantial free disk space.
echo.
docker version >nul 2>nul
if errorlevel 1 (
  echo Docker engine is unavailable. Open Docker Desktop and wait for it to finish starting.
  pause
  exit /b 1
)
set "ANGEL_OLLAMA_FALLBACK=true"
if not defined ANGEL_DEFAULT_MODEL set "ANGEL_DEFAULT_MODEL=qwen2.5:3b"
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml -f docker-compose.angel-harness.yaml up -d --pull missing --build
if errorlevel 1 (
  echo.
  echo Startup failed. Keep this log and send the last error lines for troubleshooting.
  pause
  exit /b 1
)
echo.
echo Angel Home Base: http://127.0.0.1:8765
echo Default model: qwen2.5:3b (automatically provisioned on first launch)
echo LocalAI model gallery and API: http://127.0.0.1:8080
echo Angel Nexus module/repository runner: http://127.0.0.1:8080/app/angel-nexus
echo Engineering/RAG API: http://127.0.0.1:8780
echo.
start "" http://127.0.0.1:8765
endlocal
