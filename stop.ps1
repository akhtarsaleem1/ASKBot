$ErrorActionPreference = "Stop"

$Lines = netstat -ano | Select-String "127\.0\.0\.1:8788\s+.*LISTENING"
if (-not $Lines) {
  Write-Host "ASKBot is not running on port 8788."
  exit 0
}

$ProcessIds = @()
foreach ($Line in $Lines) {
  $Parts = ($Line.ToString() -split "\s+") | Where-Object { $_ }
  $ProcessIds += $Parts[-1]
}
$ProcessIds = $ProcessIds | Select-Object -Unique
foreach ($ProcessId in $ProcessIds) {
  if ($ProcessId -and $ProcessId -ne 0) {
    Stop-Process -Id $ProcessId -Force
    Write-Host "Stopped ASKBot process $ProcessId."
  }
}
