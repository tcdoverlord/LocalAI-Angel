@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".env" if exist ".env.example" copy ".env.example" ".env" >nul
set "ANGEL_USER_PROFILE=%USERPROFILE:\=/%"
if defined ANGEL_USER_PROFILE set "ANGEL_USER_DATA=%ANGEL_USER_PROFILE%/Angel_Platform"
if not defined ANGEL_USER_DATA set "ANGEL_USER_DATA=./Angel_Platform_Data"
set "ANGEL_LLM_PROVIDER=localai"
set "ANGEL_OLLAMA_FALLBACK=true"
docker compose --profile ollama -f docker-compose.yaml -f docker-compose.nexus.override.yaml -f docker-compose.angel-harness.yaml up -d --pull missing --build
if errorlevel 1 (echo Startup failed. Check Docker output.& pause & exit /b 1)
echo Angel started with LocalAI first and optional Ollama fallback enabled.
echo If LocalAI has no models, install one in LocalAI, or pull a model in Ollama.
start "" http://127.0.0.1:8765
endlocal
