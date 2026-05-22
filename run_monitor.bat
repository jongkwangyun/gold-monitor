@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m gold_monitor.monitor
) else (
    python -m gold_monitor.monitor
)

set "EXIT_CODE=%ERRORLEVEL%"
echo.
echo Process exited with code %EXIT_CODE%.
pause
