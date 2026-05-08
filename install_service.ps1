# Windows Service Installer for ASKBot 24/7
# Run as Administrator: Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

param(
    [Parameter(Mandatory=$false)]
    [string]$InstallDir = "D:\Software\ASKBot"
)

$serviceName = "ASKBot"
$displayName = "ASKBot Daily Promotion Bot"
$description = "Automated Play Store app promotion with image/video generation"
$executable = "python.exe"
$arguments = "-m askbot.main"
$workingDir = $InstallDir

Write-Host "Installing ASKBot as Windows Service..." -ForegroundColor Green

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "ERROR: Must run as Administrator to install service" -ForegroundColor Red
    exit 1
}

# Create service directory
$serviceDir = "$env:ProgramFiles\ASKBot"
if (-NOT (Test-Path $serviceDir)) {
    New-Item -ItemType Directory -Path $serviceDir -Force
}

# Copy Python files
Write-Host "Copying files to $serviceDir..."
Copy-Item -Path "$InstallDir\*" -Destination $serviceDir -Recurse -Force

# Create service batch file
$batchPath = "$serviceDir\service.bat"
@"
@echo off
cd /d "$serviceDir"
set PYTHONPATH=$serviceDir\.python-packages
%executable% %arguments%
"@ | Out-File -FilePath $batchPath -Encoding ASCII

Write-Host "Creating service..."

# Install service using sc.exe
$scPath = "$env:SystemRoot\System32\sc.exe"
& $scPath create $serviceName binPath= $batchPath start= auto DisplayName= $displayName
& $scPath description $serviceName $description

# Set service to restart on failure
& $scPath failure $serviceName reset= 86400 actions= restart/5000/restart/5000/restart/5000

# Start the service
Write-Host "Starting service..."
& $scPath start $serviceName

Write-Host ""
Write-Host "Service installed and started!" -ForegroundColor Green
Write-Host "Service name: $serviceName"
Write-Host "Log directory: $serviceDir\logs"
Write-Host ""
Write-Host "To manage service:"
Write-Host "  Stop:    sc stop $serviceName"
Write-Host "  Start:   sc start $serviceName"
Write-Host "  Delete:  sc delete $serviceName"
Write-Host ""
Write-Host "View logs: Get-Content $serviceDir\logs\askbot.log -Tail 20"
