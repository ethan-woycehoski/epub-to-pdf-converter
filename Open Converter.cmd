@echo off
where pythonw.exe >nul 2>&1
if errorlevel 1 (
    echo Python for Windows is required to open this converter.
    pause
    exit /b 1
)
start "" pythonw.exe "%~dp0converter.pyw"
