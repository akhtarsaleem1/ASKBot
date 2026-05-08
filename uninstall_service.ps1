# Uninstall ASKBot Windows Service
# Run as Administrator

$serviceName = "ASKBot"

Write-Host "Uninstalling ASKBot service..." -ForegroundColor Yellow

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "ERROR: Must run as Administrator to uninstall service" -ForegroundColor Red
    exit 1
}

# Stop and delete service
& "$env:SystemRoot\System32\sc.exe" stop $serviceName
& "$env:SystemRoot\System32\sc.exe" delete $serviceName

Write-Host "Service uninstalled!" -ForegroundColor Green
Write-Host "You can now safely delete the service directory if desired."
