@echo off
title GitHub Auto-Push Monitor
color 0A

echo ================================================
echo   AUTO-PUSH MONITOR STARTED
echo   Checking every 2 minutes
echo   Press Ctrl+C to stop
echo ================================================
echo.

:loop
echo [%time%] Checking for changes...

REM Check if there are uncommitted changes
git diff-index --quiet HEAD --
if errorlevel 1 (
    echo [%time%] CHANGES FOUND - Pushing to GitHub...
    echo.
    
    git add .
    git commit -m "Auto-update: %date% %time%"
    git push origin main
    
    echo.
    echo [%time%] ? Push completed!
    echo ================================================
    echo.
) else (
    echo [%time%] No changes detected
)

echo Waiting 2 minutes...
echo.
timeout /t 120 /nobreak >nul
goto loop
