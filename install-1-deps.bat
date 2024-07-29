@echo off

:: Check if the script is running with admin permissions
net session >nul 2>&1
if %errorlevel% NEQ 0 (
    echo This script requires administrative privileges. Please run it as an administrator.
    pause
    exit /b
)

echo Installing dependencies...
choco install python 7zip windows-adk windows-adk-oscdimg -y
echo Done.
pause


