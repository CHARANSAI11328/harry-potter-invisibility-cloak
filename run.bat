@echo off
title Harry Potter Invisibility Cloak
cd /d "%~dp0"

echo ========================================================
echo        HARRY POTTER INVISIBILITY CLOAK (OpenCV)
echo ========================================================
echo.
echo Launching application...
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" invisibility_cloak.py %*
) else (
    python invisibility_cloak.py %*
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Program exited with code %ERRORLEVEL%.
    pause
)
