@echo off
title Cloth Color Calibrator
cd /d "%~dp0"

echo ========================================================
echo         CLOTH COLOR CALIBRATOR (OpenCV)
echo ========================================================
echo.
echo Launching calibrator...
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" calibrate_color.py %*
) else (
    python calibrate_color.py %*
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Program exited with code %ERRORLEVEL%.
    pause
)
