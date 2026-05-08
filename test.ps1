$ErrorActionPreference = "Stop"

$Workspace = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = "C:\Users\ASK\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if (-not (Test-Path $Python)) {
  Write-Error "Bundled Python runtime was not found at $Python"
}

Set-Location $Workspace
$env:PYTHONPATH = "$Workspace\.python-packages;$Workspace"
& $Python -m pytest -q
if ($LASTEXITCODE -ne 0) {
  throw "Tests failed with exit code $LASTEXITCODE"
}

