@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m gold_monitor.monitor --once --force-report
) else (
    python -m gold_monitor.monitor --once --force-report
)

