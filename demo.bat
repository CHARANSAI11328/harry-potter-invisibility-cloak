@echo off
title Harry Potter Invisibility Cloak - Hogwarts Demo Mode
cd /d "%~dp0"

echo ========================================================
echo   HARRY POTTER INVISIBILITY CLOAK - DEMO MODE
echo ========================================================
echo.
echo Launching Hogwarts Demo Video Mode...
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" invisibility_cloak.py --demo %*
) else (
    python invisibility_cloak.py --demo %*
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Program exited with code %ERRORLEVEL%.
    pause
)
