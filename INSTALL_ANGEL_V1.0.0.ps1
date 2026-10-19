[CmdletBinding()]
param([switch]$SkipOpenBrowser)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$log = Join-Path $PSScriptRoot 'angel-v1-install.log'
Start-Transcript -Path $log -Append | Out-Null
$composeFiles = @('docker-compose.yaml','docker-compose.nexus.override.yaml','docker-compose.angel-harness.yaml')
function Invoke-Compose {
  $composeArgs = @()
  foreach ($composeFile in $composeFiles) { $composeArgs += @('-f', $composeFile) }
  & docker compose @composeArgs @args
  if ($LASTEXITCODE -ne 0) { throw "docker compose $($args -join ' ') failed with exit code $LASTEXITCODE" }
}
try {
  Write-Host 'LOCALAI-ANGEL UNIFIED v1.0.0 - INSTALL / REPAIR' -ForegroundColor Cyan
  Write-Host 'Safe for first install and repeat runs. Existing .env and Docker volumes are preserved.'
  foreach ($file in $composeFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot $file))) { throw "Required Compose file missing: $file" }
  }
  if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'Angel_AI_Harness/Dockerfile.unified'))) { throw 'Angel AI Harness source/Dockerfile is missing.' }
  if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker CLI not found. Install Docker Desktop, then reopen this script.' }
  & docker info *> $null
  if ($LASTEXITCODE -ne 0) { throw 'Docker Engine is unavailable. Start Docker Desktop and retry.' }

  if (-not (Test-Path -LiteralPath '.env')) {
    if (Test-Path -LiteralPath 'env.release.example') { Copy-Item 'env.release.example' '.env' }
    elseif (Test-Path -LiteralPath '.env.example') { Copy-Item '.env.example' '.env' }
    else { throw 'No .env or release environment template was found.' }
    Write-Host 'Created .env from release defaults.' -ForegroundColor Yellow
  } else { Write-Host 'Existing .env found; preserving it.' -ForegroundColor Green }
  New-Item -ItemType Directory -Force -Path (Join-Path $PSScriptRoot 'Angel_Platform_Data') | Out-Null

  Write-Host "`n[1/6] Validating combined Compose configuration..." -ForegroundColor Cyan
  Invoke-Compose config --quiet

  Write-Host "`n[2/6] Checking required Angel storage package files..." -ForegroundColor Cyan
  $storageFiles = @('Angel_AI_Harness/angel_platform/storage/database.py','Angel_AI_Harness/angel_platform/storage/__init__.py')
  foreach ($file in $storageFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot $file))) { throw "Required storage source file missing: $file" }
    Write-Host "PASS  $file" -ForegroundColor Green
  }

  Write-Host "`n[3/6] Checking Dockerfile line endings (fixes shell heredoc parsing errors)..." -ForegroundColor Cyan
  # BuildKit shell heredocs can fail when the delimiter line in a Dockerfile has CRLF endings.
  # Normalize Dockerfiles to LF, backing up each affected file before changing it.
  $dockerfiles = Get-ChildItem -LiteralPath $PSScriptRoot -Recurse -File -Filter 'Dockerfile' -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '[\\/](\.git|node_modules|\.venv|venv)[\\/]' }
  $fixedLineEndings = 0
  foreach ($df in $dockerfiles) {
    $content = [System.IO.File]::ReadAllText($df.FullName)
    if ($content.Contains("`r`n")) {
      $backup = $df.FullName + '.pre-angel-install-line-ending-fix'
      if (-not (Test-Path -LiteralPath $backup)) { Copy-Item -LiteralPath $df.FullName -Destination $backup }
      $normalized = $content.Replace("`r`n", "`n")
      [System.IO.File]::WriteAllText($df.FullName, $normalized, [System.Text.UTF8Encoding]::new($false))
      $fixedLineEndings++
      Write-Host "Normalized Dockerfile line endings: $($df.FullName)" -ForegroundColor Yellow
    }
  }
  if ($fixedLineEndings -eq 0) { Write-Host 'PASS  Dockerfiles already use compatible line endings.' -ForegroundColor Green }
  else { Write-Host "PASS  Normalized $fixedLineEndings Dockerfile(s); original copies were preserved." -ForegroundColor Green }

  Write-Host "`n[4/6] Building LocalAI, Angel Harness, and Nexus images..." -ForegroundColor Cyan
  Invoke-Compose build

  Write-Host "`n[5/6] Testing Angel storage import inside the built image..." -ForegroundColor Cyan
  $composeArgs = @()
  foreach ($composeFile in $composeFiles) { $composeArgs += @('-f', $composeFile) }
  & docker compose @composeArgs run --rm --no-deps --entrypoint python angel-harness -c "import angel_platform.storage; print('Storage import PASS')"
  if ($LASTEXITCODE -ne 0) { throw "Angel storage import test failed with exit code $LASTEXITCODE" }

  Write-Host "`n[6/6] Starting services and checking endpoints..." -ForegroundColor Cyan
  Invoke-Compose up -d
  $targets = @(
    @{Name='Angel Home Base'; Url='http://127.0.0.1:8765/'},
    @{Name='LocalAI'; Url='http://127.0.0.1:8080/readyz'},
    @{Name='Angel Nexus'; Url='http://127.0.0.1:8877/api/health'}
  )
  $failed = @()
  foreach ($target in $targets) {
    $ready = $false
    for ($i=0; $i -lt 60; $i++) {
      try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $target.Url -TimeoutSec 4
        if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) { $ready = $true; break }
      } catch { Start-Sleep -Seconds 2 }
    }
    if ($ready) { Write-Host "PASS  $($target.Name): $($target.Url)" -ForegroundColor Green }
    else { Write-Host "FAIL  $($target.Name): $($target.Url)" -ForegroundColor Red; $failed += $target }
  }
  Write-Host "`nContainer status:" -ForegroundColor Cyan
  Invoke-Compose ps -a
  if ($failed.Count -gt 0) { throw 'One or more endpoints did not become ready. Review the diagnostics below.' }

  Write-Host "`nINSTALL / REPAIR COMPLETED SUCCESSFULLY." -ForegroundColor Green
  Write-Host 'Angel Home Base: http://127.0.0.1:8765/'
  Write-Host 'LocalAI:         http://127.0.0.1:8080/readyz'
  Write-Host 'Angel Nexus:     http://127.0.0.1:8877/'
  if (-not $SkipOpenBrowser) { Start-Process 'http://127.0.0.1:8765/' }
} catch {
  Write-Host ("`nINSTALL / REPAIR FAILED: " + $_.Exception.Message) -ForegroundColor Red
  Write-Host "`nCompose status (if containers exist):" -ForegroundColor Yellow
  try { Invoke-Compose ps -a } catch { Write-Host $_.Exception.Message -ForegroundColor DarkYellow }
  Write-Host "`nRecent Compose logs:" -ForegroundColor Yellow
  try { Invoke-Compose logs --tail 80 } catch { Write-Host $_.Exception.Message -ForegroundColor DarkYellow }
  Write-Host "`nReview $log for the full transcript." -ForegroundColor Yellow
  try { Stop-Transcript | Out-Null } catch {}
  exit 1
}
try { Stop-Transcript | Out-Null } catch {}
exit 0
