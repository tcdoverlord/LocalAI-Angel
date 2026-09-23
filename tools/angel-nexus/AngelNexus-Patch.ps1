[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("validate", "apply", "history")]
    [string]$Action,

    [Parameter(Mandatory = $false)]
    [string]$Patch = "",

    [Parameter(Mandatory = $false)]
    [string]$TargetRoot = (Get-Location).Path,

    [Parameter(Mandatory = $false)]
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$engine = Join-Path $PSScriptRoot "..\nexus-service\patch_engine.py"

if (-not (Test-Path $engine)) {
    throw "Patch engine not found: $engine"
}

$env:NEXUS_TARGET_ROOT = (Resolve-Path $TargetRoot).Path
$env:NEXUS_DATA_ROOT = Join-Path $env:NEXUS_TARGET_ROOT ".angel-nexus"

switch ($Action) {
    "history" {
        & $Python -c "from patch_engine import read_ledger; import json; print(json.dumps(read_ledger(), indent=2))"
        exit $LASTEXITCODE
    }
    "validate" {
        if (-not $Patch) { throw "-Patch is required for validate." }
        & $Python -c "import json,sys; from patch_engine import validate_manifest; print(json.dumps(validate_manifest(json.load(open(sys.argv[1], encoding='utf-8'))), indent=2))" $Patch
        exit $LASTEXITCODE
    }
    "apply" {
        if (-not $Patch) { throw "-Patch is required for apply." }
        & $Python -c "import json,sys; from patch_engine import apply_manifest; result=apply_manifest(json.load(open(sys.argv[1], encoding='utf-8'))); print(json.dumps(result, indent=2)); raise SystemExit(0 if result.get('status') == 'VALIDATED' else 2)" $Patch
        exit $LASTEXITCODE
    }
}

# SIG # Begin signature block
# MIIFggYJKoZIhvcNAQcCoIIFczCCBW8CAQExCzAJBgUrDgMCGgUAMGkGCisGAQQB
# gjcCAQSgWzBZMDQGCisGAQQBgjcCAR4wJgIDAQAABBAfzDtgWUsITrck0sYpfvNR
# AgEAAgEAAgEAAgEAAgEAMCEwCQYFKw4DAhoFAAQUtUY4V5/GfwhVELdU6vE1jR5z
# 6tegggMWMIIDEjCCAfqgAwIBAgIQHMcFXO2KFp1HcmXs+nRW/DANBgkqhkiG9w0B
# AQsFADAhMR8wHQYDVQQDDBZIVi1Db2RlU2lnbi0yMDI2LUdFTjAxMB4XDTI2MDYx
# NzIxNTE1OVoXDTI4MDYxNzIyMDIwMFowITEfMB0GA1UEAwwWSFYtQ29kZVNpZ24t
# MjAyNi1HRU4wMTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALV12gWV
# R1hHoSdHbVR5dyp99H5SL+b0VGPyxoZqPLz4GGGSzn3qdxgSEwduofW56UGcHFMF
# N3zI/YNh7tuyEIsLSQXKc1TiwqtD1b0D+XwGKY9Ns0Hc9eSSmCL2Yk7TTNVyMyyH
# P3fbK5aMokWFrSTbZnTmU0+ufcQkQaNygjrR2j3O+JOZyey6XlqV8WKxl5RN76WX
# v2baG0OP6ypswPFabSwrYblCfyfPgIQRtD1VFEG0B0WO3u+Agr9TMdrgDUW+JFPI
# eM06JfOHh2emr8lw/ijNFBojDxLDBnzcKUjbCn24QlC+qsLc3dRKv1JIDWP5DAuF
# PKa7E0h4zucm/LkCAwEAAaNGMEQwDgYDVR0PAQH/BAQDAgeAMBMGA1UdJQQMMAoG
# CCsGAQUFBwMDMB0GA1UdDgQWBBTv7z2lwMtf0vCCeuDDIyD3JiQKkzANBgkqhkiG
# 9w0BAQsFAAOCAQEAAtYpBx4018O+twFqLjZxMjRFPLI9rdN4+9msTd3e0bAmzPFU
# jRQO/8H/PsWNbKcPihugAc66YV8rWtQvDGO1XBy414jdgRzCOXLvrJWrt2N2nmBV
# opWK40pPzIhCC+EX1oX/mEEZVjoyzALXL5S55pygDCqY9n6ccG1qdDZ4Uy30Mz2A
# cAL1e8Try2gejKLJCUFoZErzmK289b2B8F7Howe9h8bekD1xWuUUR3+MGKYqP4Go
# HQ+dn8hpP2v2SslGouppBVs+T3MknKt1pP1f8VGpW53rzKZkxcNxQ/LzJO9gKzON
# mmlY+EWUXaYp9a0+7qCRvosdkf1bcx/y236y7zGCAdYwggHSAgEBMDUwITEfMB0G
# A1UEAwwWSFYtQ29kZVNpZ24tMjAyNi1HRU4wMQIQHMcFXO2KFp1HcmXs+nRW/DAJ
# BgUrDgMCGgUAoHgwGAYKKwYBBAGCNwIBDDEKMAigAoAAoQKAADAZBgkqhkiG9w0B
# CQMxDAYKKwYBBAGCNwIBBDAcBgorBgEEAYI3AgELMQ4wDAYKKwYBBAGCNwIBFTAj
# BgkqhkiG9w0BCQQxFgQUTNPTHZ4u5bSYPBI/YY7AC9DVdl4wDQYJKoZIhvcNAQEB
# BQAEggEANeHQ6Iv7pQlTJjarprKy3pOpJHOAe5qWt/h9+IW14TgkrWopLi0XuRj7
# ghX25D2hoaVrM1tToEWIbMyx5m4kOLdp7DBufuQhpGiFl6xcb6OtnvqBH5mdweiS
# nr4M5r/xoSmERKd8CjWvwRh03TILfFQOOdKs17CBRMQjXMzLjr21oJ7xlTyU688q
# mBwq1MV2MmCbVMiPp+fXGVFZTkcD4gIQVR/tTGbYW6WQva96YwriL/k/Fdf6lS6W
# 6L63qMc3ijdX7vXQIrA+pI9P/EQRufEhbZwtOdMbQuefGs/EkKYLPWNnakA5o6PT
# q7sjqUire4d9wGJUmFd7FewU9cVIWA==
# SIG # End signature block
