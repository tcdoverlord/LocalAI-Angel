@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title LocalAI Angel Unified v1.0.0 - Run
color 0B
echo ============================================================
echo       LOCALAI ANGEL UNIFIED v1.0.0 - START
echo ============================================================
where docker >nul 2>nul || (echo ERROR: Docker CLI not found.& pause & exit /b 1)
docker info >nul 2>nul || (echo ERROR: Start Docker Desktop first.& pause & exit /b 1)
for %%F in (docker-compose.yaml docker-compose.nexus.override.yaml docker-compose.angel-harness.yaml) do if not exist "%%F" (echo ERROR: Required file %%F is missing.& pause & exit /b 1)
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml -f docker-compose.angel-harness.yaml config --quiet
if errorlevel 1 (echo ERROR: Compose configuration is invalid. Run INSTALL_ANGEL_V1.0.0.bat.& pause & exit /b 1)
echo Starting services without rebuilding images...
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml -f docker-compose.angel-harness.yaml up -d --no-build
if errorlevel 1 goto failed
echo Waiting for Angel, LocalAI, and Nexus...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$targets=@(@{n='Angel AI';u='http://127.0.0.1:8765/api/status'},@{n='LocalAI';u='http://127.0.0.1:8080/readyz'},@{n='Angel Nexus';u='http://127.0.0.1:8877/api/health});$bad=@();foreach($t in $targets){$ok=$false;for($i=0;$i -lt 60;$i++){try{$r=Invoke-WebRequest -UseBasicParsing -Uri $t.u -TimeoutSec 3;if($r.StatusCode -ge 200 -and $r.StatusCode -lt 400){$ok=$true;break}}catch{Start-Sleep -Seconds 2}};if($ok){Write-Host ('PASS '+$t.n+' '+$t.u)}else{Write-Host ('FAIL '+$t.n+' '+$t.u);$bad+=$t}};if($bad.Count){exit 1}"
if errorlevel 1 goto failed
echo.
echo All endpoint checks passed.
echo Angel AI:   http://127.0.0.1:8765/
echo LocalAI UI: http://127.0.0.1:8080/app
echo Nexus UI:   http://127.0.0.1:8080/app/angel-nexus
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml -f docker-compose.angel-harness.yaml ps
start "" "http://127.0.0.1:8765/"
start "" "http://127.0.0.1:8080/app"
start "" "http://127.0.0.1:8080/app/angel-nexus"
pause
exit /b 0
:failed
echo.
echo WARNING: Startup or health checks failed. Container status and logs:
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml -f docker-compose.angel-harness.yaml ps -a
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml -f docker-compose.angel-harness.yaml logs --tail 80
pause
exit /b 1
