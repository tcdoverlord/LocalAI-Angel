@echo off
setlocal
cd /d "%~dp0"
set "ANGEL_USER_PROFILE=%USERPROFILE:\=/%"
if defined ANGEL_USER_PROFILE set "ANGEL_USER_DATA=%ANGEL_USER_PROFILE%/Angel_Platform"
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml -f docker-compose.angel-harness.yaml down
endlocal
