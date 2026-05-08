@echo off
echo Installing ASKBot to Windows Startup...

set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "VBS_FILE=d:\Software\ASKBot\start_background.vbs"

if not exist "%VBS_FILE%" (
    echo Error: %VBS_FILE% not found!
    pause
    exit /b 1
)

copy /Y "%VBS_FILE%" "%STARTUP_DIR%"

echo.
echo Success! ASKBot will now start automatically in the background every time you turn on your laptop.
echo It will run 24/7 and log all activity to the 'logs' folder.
echo To stop the bot, use Task Manager or run stop.ps1.
echo.
pause
