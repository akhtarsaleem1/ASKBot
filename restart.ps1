$ErrorActionPreference = "Stop"

$Workspace = Split-Path -Parent $MyInvocation.MyCommand.Path
$StopScript = Join-Path $Workspace "stop.ps1"
$StartScript = Join-Path $Workspace "start_background.ps1"
$StatusScript = Join-Path $Workspace "status.ps1"

Write-Host "Restarting ASKBot..."

# Stop the existing process
if (Test-Path $StopScript) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $StopScript
}
Start-Sleep -Seconds 2

# Start silently in background
if (Test-Path $StartScript) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $StartScript
}
Start-Sleep -Seconds 3

# Show status
if (Test-Path $StatusScript) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $StatusScript
}
