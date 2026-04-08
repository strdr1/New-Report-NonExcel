@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo   Fuel Tracker
echo ============================================================

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.9+ from python.org
    pause
    exit /b 1
)

REM Автообновление через git
git --version >nul 2>&1
if not errorlevel 1 (
    echo Checking for updates...
    git fetch origin >nul 2>&1
    git status -uno | find "behind" >nul 2>&1
    if not errorlevel 1 (
        echo Update found, applying...
        git pull origin main >nul 2>&1
        echo Updated to latest version.
    ) else (
        echo No updates.
    )
) else (
    echo git not found, skipping update check.
)

echo Installing dependencies...
python -m pip install -r requirements.txt -q 2>>error.log

echo Checking WebView2...
reg query "HKLM\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}" >nul 2>&1
if not errorlevel 1 goto webview2_ok
reg query "HKCU\SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}" >nul 2>&1
if not errorlevel 1 goto webview2_ok

echo WebView2 not found. Downloading...
powershell -Command "Invoke-WebRequest -Uri 'https://go.microsoft.com/fwlink/p/?LinkId=2124703' -OutFile '%TEMP%\MicrosoftEdgeWebview2Setup.exe'" >nul 2>&1
"%TEMP%\MicrosoftEdgeWebview2Setup.exe" /silent /install
echo WebView2 installed.

:webview2_ok
echo Starting...
python main.py > app.log 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: App crashed. See app.log:
    type app.log
    pause
)
