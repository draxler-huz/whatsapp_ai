@echo off
title Build WhatsApp Summarizer APK
cd /d "%~dp0"

echo ===================================================
echo     WhatsApp Group Summarizer - Free APK Builder
echo ===================================================
echo.
echo [Step 1/3] Installing lightweight dependencies...
call npm install --legacy-peer-deps
if %ERRORLEVEL% NEQ 0 (
    echo Error installing dependencies.
    pause
    exit /b
)

echo.
echo [Step 2/3] Authenticating with free Expo account...
echo (If you do not have an Expo account, it will prompt you to create one for free)
npx eas login

echo.
echo [Step 3/3] Submitting APK build to Expo Cloud...
echo (The cloud server compiles the APK in ~5-10 minutes)
npx eas build -p android --profile preview

echo.
echo ===================================================
echo Build submitted! When finished, scan the QR code
echo printed in the terminal to download your APK directly!
echo ===================================================
pause
