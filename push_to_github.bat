@echo off
setlocal enabledelayedexpansion
title Push Invisibility Cloak to GitHub
cd /d "%~dp0"

echo ========================================================
echo        PUSH TO GITHUB: INVISIBILITY CLOAK
echo ========================================================
echo.

git status
echo.

git remote -v >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo No remote found.
    set /p REPO_URL="Enter your GitHub repository URL (e.g. https://github.com/CHARANSAI11328/invisibility-cloak.git): "
    if "!REPO_URL!"=="" (
        echo [!] URL cannot be empty. Exiting.
        pause
        exit /b 1
    )
    git remote add origin !REPO_URL!
)

echo.
echo Pushing branch 'main' to origin...
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Code pushed successfully to GitHub!
) else (
    echo.
    echo [!] Push failed. Please check your repository URL and GitHub credentials.
)

pause
