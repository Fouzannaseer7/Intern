@echo off
title GitHub Auto-Push Monitor
color 0A

echo ================================================
echo   AUTO-PUSH MONITOR STARTED
echo   Checking every 2 minutes
echo   Working Directory: %CD%
echo   Press Ctrl+C to stop
echo ================================================
echo.

:loop
echo [%time%] Checking for changes...

git status --porcelain > temp_status.txt
set /p STATUS=<temp_status.txt
del temp_status.txt

if not "%STATUS%"=="" (
    echo [%time%] CHANGES FOUND - Pushing to GitHub...
    echo.
    
    git add .
    git commit -m "Auto-update: %date% %time%"
    git push origin main
    
    echo.
    echo [%time%] Push completed!
    echo ================================================
    echo.
) else (
    echo [%time%] No changes detected
)

echo Waiting 2 minutes...
echo.
timeout /t 120 /nobreak
goto loop
