@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo   Fuel Tracker - Server Mode (Phone Access)
echo ============================================================

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.9+ from python.org
    pause
    exit /b 1
)

REM Автообновление
git --version >nul 2>&1
if not errorlevel 1 (
    git fetch origin >nul 2>&1
    git status -uno | find "behind" >nul 2>&1
    if not errorlevel 1 (
        echo Update found, applying...
        git pull origin main --rebase >nul 2>&1
    )
)

python -m pip install -r requirements.txt -q

python server.py

pause
