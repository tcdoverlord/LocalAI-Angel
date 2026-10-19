[CmdletBinding()]
param([switch]$SkipOpenBrowser)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$log = Join-Path $PSScriptRoot 'angel-v1-install.log'
Start-Transcript -Path $log -Append | Out-Null
$composeFiles = @('docker-compose.yaml','docker-compose.nexus.override.yaml','docker-compose.angel-harness.yaml')
function Invoke-Compose { $composeArgs = @(); foreach ($composeFile in $composeFiles) { $composeArgs += @('-f', $composeFile) }; & docker compose @composeArgs @args; if ($LASTEXITCODE -ne 0) { throw "docker compose $($args -join ' ') failed with exit code $LASTEXITCODE" } }
try {
  Write-Host 'LocalAI Angel Unified v1.0.0 installer' -ForegroundColor Cyan
  foreach ($file in $composeFiles) { if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot $file))) { throw "Required Compose file missing: $file" } }
  if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'Angel_AI_Harness/Dockerfile.unified'))) { throw 'Angel AI Harness source/Dockerfile is missing.' }
  if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker CLI not found. Install Docker Desktop, then reopen this script.' }
  & docker info *> $null
  if ($LASTEXITCODE -ne 0) { throw 'Docker Engine is unavailable. Start Docker Desktop and retry.' }
  if (-not (Test-Path -LiteralPath '.env')) {
    if (Test-Path -LiteralPath 'env.release.example') { Copy-Item 'env.release.example' '.env' }
    elseif (Test-Path -LiteralPath '.env.example') { Copy-Item '.env.example' '.env' }
    else { throw 'No .env or release environment template was found.' }
    Write-Host 'Created .env from the release defaults.'
  } else { Write-Host 'Existing .env found; preserving it and its configured data path.' -ForegroundColor Yellow }
  if (-not (Test-Path -LiteralPath '.env')) { throw 'Could not create .env.' }
  New-Item -ItemType Directory -Force -Path (Join-Path $PSScriptRoot 'Angel_Platform_Data') | Out-Null
  Write-Host "`n[1/4] Validating combined Compose configuration..." -ForegroundColor Cyan
  Invoke-Compose config --quiet
  Write-Host "`n[2/4] Building LocalAI, Angel Harness, and Nexus... First build can take several minutes." -ForegroundColor Cyan
  Invoke-Compose build
  Write-Host "`n[3/4] Starting unified services..." -ForegroundColor Cyan
  Invoke-Compose up -d
  Write-Host "`n[4/4] Waiting for service endpoints..." -ForegroundColor Cyan
  $targets = @(
    @{Name='Angel AI'; Url='http://127.0.0.1:8765/api/status'},
    @{Name='LocalAI'; Url='http://127.0.0.1:8080/readyz'},
    @{Name='Angel Nexus'; Url='http://127.0.0.1:8877/api/health'}
  )
  $failed = @()
  foreach ($target in $targets) {
    $ready = $false
    for ($i=0; $i -lt 90; $i++) {
      try { $response = Invoke-WebRequest -UseBasicParsing -Uri $target.Url -TimeoutSec 4; if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) { $ready=$true; break } } catch { Start-Sleep -Seconds 2 }
    }
    if ($ready) { Write-Host ("PASS  {0}: {1}" -f $target.Name,$target.Url) -ForegroundColor Green }
    else { Write-Host ("FAIL  {0}: {1}" -f $target.Name,$target.Url) -ForegroundColor Red; $failed += $target }
  }
  Write-Host "`nContainer status:" -ForegroundColor Cyan
  Invoke-Compose ps -a
  if ($failed.Count) {
    Write-Host "`nOne or more endpoint checks failed. Recent logs follow:" -ForegroundColor Yellow
    Invoke-Compose logs --tail 80
    throw 'Stack started but not all endpoint checks passed. Inspect angel-v1-install.log and container logs.'
  }
  Write-Host "`nINSTALLATION CHECKS PASSED." -ForegroundColor Green
  Write-Host 'Angel AI:   http://127.0.0.1:8765/'
  Write-Host 'LocalAI UI: http://127.0.0.1:8080/app'
  Write-Host 'Nexus UI:   http://127.0.0.1:8080/app/angel-nexus'
  if (-not $SkipOpenBrowser) { Start-Process 'http://127.0.0.1:8765/'; Start-Process 'http://127.0.0.1:8080/app'; Start-Process 'http://127.0.0.1:8080/app/angel-nexus' }
} catch {
  Write-Host ("`nERROR: " + $_.Exception.Message) -ForegroundColor Red
  try { & docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml -f docker-compose.angel-harness.yaml ps -a } catch {}
  Stop-Transcript | Out-Null
  exit 1
}
Stop-Transcript | Out-Null
exit 0
