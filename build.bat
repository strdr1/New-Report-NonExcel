@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo   Building Fuel Tracker EXE
echo ============================================================

echo [1/3] Installing build dependencies...
python -m pip install pyinstaller pywebview[base] -q

echo [2/3] Building EXE...
pyinstaller --noconfirm --clean ^
    --name "FuelTracker" ^
    --onedir ^
    --noconsole ^
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
    main.py

if errorlevel 1 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo [3/3] Copying database config...
if not exist "dist\FuelTracker\fuel_tracking.db" (
    if exist "fuel_tracking.db" copy "fuel_tracking.db" "dist\FuelTracker\" >nul
)

echo.
echo ============================================================
echo   Done! EXE is in: dist\FuelTracker\FuelTracker.exe
echo ============================================================
pause
