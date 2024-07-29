@echo off
fsutil dirty query %systemdrive% >nul || (
    echo Requesting administrative privileges...
    set "ELEVATE_CMDLINE=cd /d "%cd%" & call "%~f0" %*"
    findstr "^:::" "%~sf0">"%temp%\getadmin.vbs"
    cscript //nologo "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs" & exit /b
)

rem ------- getadmin.vbs ----------------------------------
::: Set objShell = CreateObject("Shell.Application")
::: Set objWshShell = WScript.CreateObject("WScript.Shell")
::: Set objWshProcessEnv = objWshShell.Environment("PROCESS")
::: strCommandLine = Trim(objWshProcessEnv("ELEVATE_CMDLINE"))
::: objShell.ShellExecute "cmd", "/c " & strCommandLine, "", "runas"
rem -------------------------------------------------------

echo Running as admin.
@REM echo Script file : %~f0
@REM echo Arguments   : %*
@REM echo Working dir : %cd%
@REM echo.
:: administrator commands here
:: e.g., run shell as admin

echo Installing dependencies...
choco install python 7zip windows-adk windows-adk-oscdimg -y
echo Done.
pause


