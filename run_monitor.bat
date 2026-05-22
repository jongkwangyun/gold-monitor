@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%CD%"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 goto done

"%PYTHON_EXE%" -m gold_monitor.monitor

:done
set "EXIT_CODE=%ERRORLEVEL%"
echo.
echo Process exited with code %EXIT_CODE%.
pause
