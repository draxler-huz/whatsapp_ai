@echo off
title WhatsApp AI Announcement Bot
cd /d "%~dp0"
echo ========================================================
echo        WhatsApp AI Announcement Bot Launcher
echo ========================================================
echo.
echo [1/2] Opening dashboard in your browser...
start http://127.0.0.1:8050
echo.
echo [2/2] Starting server on http://127.0.0.1:8050 ...
echo (Keep this window open while using the bot)
echo.
python backend\main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [Notice] Python exited with error code %ERRORLEVEL%.
    echo Trying py launcher...
    py backend\main.py
)
pause
