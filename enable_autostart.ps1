$ErrorActionPreference = "Stop"

$Workspace = Split-Path -Parent $MyInvocation.MyCommand.Path
$TargetFile = Join-Path $Workspace "run_background.cmd"
$StartupFolder = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
$ShortcutPath = Join-Path $StartupFolder "ASKBot.url"

# We use a .url file as a simple way to create a shortcut that launches a file
$Content = @(
    "[InternetShortcut]"
    "URL=file:///$($TargetFile.Replace('\', '/'))"
)

$Content | Out-File -FilePath $ShortcutPath -Encoding ascii

Write-Host "Auto-startup enabled!"
Write-Host "The bot will now start silently every time you log into your laptop."
Write-Host "Shortcut created at: $ShortcutPath"
