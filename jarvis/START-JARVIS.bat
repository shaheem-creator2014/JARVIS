@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 jarvis.py
) else (
    python jarvis.py
)
if errorlevel 1 (
    echo.
    echo JARVIS could not start. Read the error above.
    echo Python 3.12 or newer is required. No extra packages are needed.
    pause
)
endlocal
