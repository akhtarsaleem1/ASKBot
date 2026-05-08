$ErrorActionPreference = "Stop"

$Python = "C:\Users\ASK\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if (-not (Test-Path $Python)) {
  Write-Error "Bundled Python runtime was not found at $Python"
}

& $Python -m pip install -r requirements.txt --target ".python-packages"
if ($LASTEXITCODE -ne 0) {
  throw "Dependency installation failed with exit code $LASTEXITCODE"
}

Write-Host "Dependencies installed into .python-packages"
