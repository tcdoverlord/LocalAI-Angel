$ErrorActionPreference = 'Stop'
$source = Join-Path $env:USERPROFILE 'Angel_Platform'
if (-not (Test-Path -LiteralPath $source -PathType Container)) {
    Write-Host "No existing Angel_Platform data folder was found at $source" -ForegroundColor Yellow
    exit 0
}
$backupRoot = Join-Path $env:USERPROFILE 'Angel_Platform_Backups'
New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$destination = Join-Path $backupRoot "Angel_Platform-before-unified-$stamp.zip"
Compress-Archive -Path (Join-Path $source '*') -DestinationPath $destination -CompressionLevel Optimal
Write-Host "Backup created: $destination" -ForegroundColor Green
