$ErrorActionPreference = "Stop"

$Workspace = Split-Path -Parent $MyInvocation.MyCommand.Path
$EnvPath = Join-Path $Workspace ".env"
$RequiredKeys = @(
  "GROQ_API_KEY",
  "BUFFER_API_KEY",
  "BUFFER_API_KEY_2",
  "CLOUDINARY_CLOUD_NAME",
  "CLOUDINARY_API_KEY",
  "CLOUDINARY_API_SECRET"
)

Write-Host "ASKBot status"
Write-Host "============="

if (Test-Path $EnvPath) {
  Write-Host ".env: found"
  $Lines = Get-Content -Path $EnvPath
  foreach ($Key in $RequiredKeys) {
    $Match = $Lines | Where-Object { $_ -match "^\s*$Key\s*=\s*.+" } | Select-Object -First 1
    if ($Match) {
      Write-Host "${Key}: configured"
    } else {
      Write-Host "${Key}: missing or blank"
    }
  }
  $BufferMatches = $Lines | Where-Object { $_ -match "^\s*BUFFER_API_KEY(_\d+)?\s*=\s*.+" -or $_ -match "^\s*BUFFER_API_KEYS\s*=\s*.+" }
  Write-Host "Buffer accounts configured: $($BufferMatches.Count)"
} else {
  Write-Host ".env: missing"
}

$NetstatLine = netstat -ano | Select-String "127\.0\.0\.1:8788\s+.*LISTENING" | Select-Object -First 1
if ($NetstatLine) {
  $Parts = ($NetstatLine.ToString() -split "\s+") | Where-Object { $_ }
  $ProcessId = $Parts[-1]
  Write-Host "Server: running on http://127.0.0.1:8788"
  Write-Host "Process ID: $ProcessId"
} else {
  Write-Host "Server: not running"
}
