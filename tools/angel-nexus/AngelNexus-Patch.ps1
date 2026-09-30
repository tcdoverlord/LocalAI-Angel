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

