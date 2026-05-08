# ASKBot Windows Service Setup

## Overview
Run ASKBot 24/7 as a Windows Service that starts automatically when your laptop boots.

## Features
- **Automatic startup** with Windows
- **File logging** with timestamps in `logs/` directory
- **Log rotation** (30 days retention)
- **Service management** via PowerShell scripts

## Quick Install

1. **Open PowerShell as Administrator**
   ```powershell
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Install the service**
   ```powershell
   .\install_service.ps1
   ```

3. **Verify it's running**
   ```powershell
   Get-Service ASKBot
   ```

## What Gets Installed

- Service name: `ASKBot`
- Display name: `ASKBot Daily Promotion Bot`
- Startup type: Automatic
- Restart on failure: Yes (after 5 seconds, up to 3 times)
- Working directory: `C:\Program Files\ASKBot`
- Log directory: `C:\Program Files\ASKBot\logs`

## Log Files

All operations are logged with timestamps:

| File | Contents | Location |
|------|----------|----------|
| `askbot.log` | All application events | `logs/askbot.log` |
| `promotion.log` | Promotion runs only | `logs/promotion.log` |
| `errors.log` | Errors with stack traces | `logs/errors.log` |

### View Recent Logs
```powershell
# Last 20 lines of main log
Get-Content "C:\Program Files\ASKBot\logs\askbot.log" -Tail 20

# Last 10 promotion runs
Get-Content "C:\Program Files\ASKBot\logs\promotion.log" -Tail 10

# Recent errors
Get-Content "C:\Program Files\ASKBot\logs\errors.log" -Tail 5
```

## Service Management

### Stop Service
```powershell
sc stop ASKBot
```

### Start Service
```powershell
sc start ASKBot
```

### Delete Service
```powershell
.\uninstall_service.ps1
```

## Development Mode

To run ASKBot normally (not as service) for development:
```powershell
cd D:\Software\ASKBot
python -m askbot.main
```

The service automatically uses the same `.env` file and database as the development version.

## Troubleshooting

### Service Won't Start
1. Check Event Viewer → Windows Logs → Application
2. Verify Python and dependencies are installed
3. Ensure `.env` file exists in service directory

### No Logs Appearing
1. Check permissions on `logs/` directory
2. Verify service has write access
3. Restart service: `sc stop ASKBot && sc start ASKBot`

### Updating Bot
1. Stop service: `sc stop ASKBot`
2. Update files in `C:\Program Files\ASKBot\`
3. Start service: `sc start ASKBot`

The service preserves your database and logs across updates.
