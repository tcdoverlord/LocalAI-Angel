$ErrorActionPreference = 'Stop'
$path = Join-Path $PSScriptRoot 'docker-compose.angel-harness.yaml'
if (-not (Test-Path -LiteralPath $path)) { throw "Missing Compose file: $path" }
$text = [IO.File]::ReadAllText($path)
$original = $text
$start = $text.IndexOf("  ollama:")
$end = $text.IndexOf("  ollama-model-init:")
if ($start -lt 0 -or $end -le $start) { throw 'Could not locate Ollama service boundaries. Compose file was not changed.' }
$before = $text.Substring(0, $start)
$service = $text.Substring($start, $end - $start)
$after = $text.Substring($end)
# Remove only Ollama's host port mapping. Containers still reach it via http://ollama:11434.
$service = [regex]::Replace($service, '(?m)^\s{4}ports:\r?\n(?:\s{6}-[^\r\n]*\r?\n)+', '')
$text = $before + $service + $after
# Use YAML-safe literal strings; do not embed Docker ${VAR:-default} syntax in PowerShell.
$replaceEnv = {
  param($match, $value)
  if ($match.Success) { return ($match.Groups[1].Value + ' "' + $value + '"') }
  return $null
}
$text = [regex]::Replace($text, '(?m)^(\s{6}ANGEL_OLLAMA_FALLBACK:)\s*.*$', { param($m) & $replaceEnv $m 'true' })
$text = [regex]::Replace($text, '(?m)^(\s{6}ANGEL_DEFAULT_MODEL:)\s*.*$', { param($m) & $replaceEnv $m 'llama3.2:3b' })
# Ensure Angel can discover Ollama through the Docker network; add the setting if missing.
if ($text -notmatch '(?m)^\s{6}ANGEL_OLLAMA_BASE_URL:') {
  $text = [regex]::Replace($text, '(?m)^(\s{6}environment:\s*\r?\n)', '$1      ANGEL_OLLAMA_BASE_URL: "http://ollama:11434"' + "`r`n", 1)
} else {
  $text = [regex]::Replace($text, '(?m)^(\s{6}ANGEL_OLLAMA_BASE_URL:)\s*.*$', '$1 "http://ollama:11434"')
}
if ($text -eq $original) { Write-Host 'Compose settings already match expected values.' }
[IO.File]::WriteAllText($path, $text, [Text.UTF8Encoding]::new($false))
# Verify edited service boundaries and settings.
$start = $text.IndexOf("  ollama:")
$end = $text.IndexOf("  ollama-model-init:")
$service = $text.Substring($start, $end - $start)
if ($service -match '(?m)^\s{4}ports:') { throw 'Ollama host port mapping remains in the service block.' }
if ($text -notmatch '(?m)^\s{6}ANGEL_OLLAMA_BASE_URL:\s*"http://ollama:11434"') { throw 'Angel Ollama URL could not be verified.' }
Write-Host 'Compose repair complete: Ollama uses the internal Docker URL, fallback is enabled, and default model is llama3.2:3b.'
