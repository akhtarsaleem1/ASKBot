$ErrorActionPreference = "Stop"

$Workspace = Split-Path -Parent $MyInvocation.MyCommand.Path
$StartScript = Join-Path $Workspace "start_background.ps1"
$RunKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$Name = "ASKBot Daily Play Store Promotion Bot"
$Value = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$StartScript`""

if (-not (Test-Path $StartScript)) {
  Write-Error "start_background.ps1 was not found at $StartScript"
}

New-ItemProperty -Path $RunKey -Name $Name -Value $Value -PropertyType String -Force | Out-Null
Write-Host "Installed per-user Windows login startup entry: $Name"

