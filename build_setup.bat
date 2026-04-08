@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo   Building FuelTracker Setup
echo ============================================================

REM [1] Зависимости сборки
echo [1/5] Installing build dependencies...
python -m pip install pyinstaller -q

REM [2] PyInstaller
echo [2/5] Building EXE with PyInstaller...
pyinstaller --noconfirm --clean ^
    --name "FuelTracker" ^
    --onedir ^
    --noconsole ^
    --icon "frontend\FOT.png" ^
    --add-data "frontend;frontend" ^
    --add-data "backend;backend" ^
    --hidden-import "webview.platforms.edgechromium" ^
    --hidden-import "flask" ^
    --hidden-import "flask_cors" ^
    --hidden-import "sqlalchemy" ^
    --hidden-import "sqlalchemy.dialects.sqlite" ^
    --hidden-import "backend.routes.profiles" ^
    --hidden-import "backend.routes.years" ^
    --hidden-import "backend.routes.months" ^
    --hidden-import "clr" ^
    main.py

if errorlevel 1 (
    echo [ERROR] PyInstaller failed!
    pause
    exit /b 1
)

REM [3] Скачать nginx для Windows
echo [3/5] Downloading nginx for Windows...
if not exist "nginx_win\nginx.exe" (
    mkdir nginx_win 2>nul
    powershell -Command "Invoke-WebRequest -Uri 'https://nginx.org/download/nginx-1.26.3.zip' -OutFile '%TEMP%\nginx.zip'"
    powershell -Command "Expand-Archive -Path '%TEMP%\nginx.zip' -DestinationPath '%TEMP%\nginx_extracted' -Force"
    xcopy /E /Y "%TEMP%\nginx_extracted\nginx-1.26.3\*" "nginx_win\" >nul
    copy /Y "nginx\nginx.conf" "nginx_win\conf\nginx.conf" >nul
    echo nginx downloaded.
) else (
    echo nginx already downloaded.
)

REM [4] Копируем nginx в dist
echo [4/5] Copying nginx to dist...
xcopy /E /Y "nginx_win\*" "dist\FuelTracker\nginx\" >nul
mkdir "dist\FuelTracker\nginx\logs" 2>nul

REM [5] Inno Setup
echo [5/5] Building installer with Inno Setup...
set INNO="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %INNO% set INNO="C:\Program Files\Inno Setup 6\ISCC.exe"

if not exist %INNO% (
    echo [WARNING] Inno Setup not found at %INNO%
    echo Download from: https://jrsoftware.org/isdl.php
    echo Then re-run this script.
    echo.
    echo EXE is ready at: dist\FuelTracker\FuelTracker.exe
    pause
    exit /b 0
)

mkdir "dist\installer" 2>nul
%INNO% setup.iss

if errorlevel 1 (
    echo [ERROR] Inno Setup failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Done!
echo   Installer: dist\installer\FuelTracker_Setup.exe
echo ============================================================
pause
