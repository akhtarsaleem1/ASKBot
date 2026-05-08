# Change to Continue so that Uvicorn's stderr output doesn't stop the script
$ErrorActionPreference = "Continue"

$Python = "C:\Users\ASK\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$Workspace = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Workspace

if (-not (Test-Path "data")) {
    New-Item -Path "data" -ItemType Directory
}

$env:PYTHONPATH = "$Workspace\.python-packages;$Workspace"

# Run python and redirect logs
# Using *>&1 would merge streams, but let's just use simple redirection
& $Python -m askbot.main 1> "data\background.out.log" 2> "data\background.err.log"
