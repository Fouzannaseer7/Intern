@echo off
title Auto-Push (Every 30 seconds)
color 0A
echo Auto-Push Running... Press Ctrl+C to stop
echo.

:loop
git add . 2>nul
git commit -m "Auto: %time%" 2>nul
git push origin main 2>nul

if errorlevel 0 (
    echo [%time%] Pushed changes
) else (
    echo [%time%] No changes or push failed
)

timeout /t 30 /nobreak >nul
goto loop
