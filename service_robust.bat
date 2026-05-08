@echo off
setlocal enabledelayedexpansion

:: ASKBot Windows Service - Robust Startup Script
:: Logs everything to help debug startup issues

set LOGFILE=C:\Program Files\ASKBot\logs\service_startup.log
set SERVICE_DIR=C:\Program Files\ASKBot

:: Ensure log directory exists
if not exist "%SERVICE_DIR%\logs" mkdir "%SERVICE_DIR%\logs"

:: Log startup
echo [%DATE% %TIME%] Starting ASKBot service... >> "%LOGFILE%"

:: Set working directory
cd /d "%SERVICE_DIR%"
echo [%DATE% %TIME%] Working directory: %CD% >> "%LOGFILE%"

:: Set Python path
set PYTHONPATH=%SERVICE_DIR%\.python-packages
echo [%DATE% %TIME%] PYTHONPATH set to: %PYTHONPATH% >> "%LOGFILE%"

:: Find Python executable
set PYTHON_EXE=
if exist "%SERVICE_DIR%\.python-packages\python.exe" (
    set PYTHON_EXE=%SERVICE_DIR%\.python-packages\python.exe
) else (
    :: Try system Python
    where python.exe > "%TEMP%\pythonpath.txt" 2>nul
    set /p PYTHON_EXE=<"%TEMP%\pythonpath.txt"
)
echo [%DATE% %TIME%] Python executable: %PYTHON_EXE% >> "%LOGFILE%"

:: Check if Python found
if "%PYTHON_EXE%"=="" (
    echo [%DATE% %TIME%] ERROR: Python not found >> "%LOGFILE%"
    exit /b 1
)

:: Check if main module exists
if not exist "%SERVICE_DIR%\askbot\main.py" (
    echo [%DATE% %TIME%] ERROR: askbot\main.py not found >> "%LOGFILE%"
    exit /b 1
)

:: Start the application
echo [%DATE% %TIME%] Starting: %PYTHON_EXE% -m askbot.main >> "%LOGFILE%"
"%PYTHON_EXE%" -m askbot.main >> "%LOGFILE%" 2>&1

:: Log result
if %ERRORLEVEL% EQU 0 (
    echo [%DATE% %TIME%] Application started successfully >> "%LOGFILE%"
) else (
    echo [%DATE% %TIME%] ERROR: Application failed with code %ERRORLEVEL% >> "%LOGFILE%"
)

exit /b %ERRORLEVEL%
