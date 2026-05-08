$ErrorActionPreference = "Stop"
$Workspace = Split-Path -Parent $MyInvocation.MyCommand.Path
$RunScript = Join-Path $Workspace "run.ps1"

Write-Host "Starting ASKBot in the background..."

# Use WindowStyle Hidden to ensure NO terminal window appears on the desktop
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$RunScript`"" -WindowStyle Hidden

Write-Host "ASKBot is now running silently."
Write-Host "Dashboard: http://127.0.0.1:8788"
