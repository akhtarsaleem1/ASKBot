$ErrorActionPreference = "Stop"

$TaskName = "ASKBot Daily Play Store Promotion Bot"
$Workspace = Split-Path -Parent $MyInvocation.MyCommand.Path
$RunScript = Join-Path $Workspace "run.ps1"

if (-not (Test-Path $RunScript)) {
  Write-Error "run.ps1 was not found at $RunScript"
}

$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$RunScript`"" -WorkingDirectory $Workspace
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5)

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Runs ASKBot local dashboard and daily promotion scheduler at login." -Force | Out-Null

Write-Host "Installed scheduled task: $TaskName"

