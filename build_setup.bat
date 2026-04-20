@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Building FuelTracker Setup...

echo [1/4] Installing pyinstaller...
python -m pip install pyinstaller -q

echo [2/4] Building FuelTracker.exe...
python -m PyInstaller --noconfirm --clean --name FuelTracker --onedir --noconsole --add-data "frontend;frontend" --add-data "backend;backend" --add-data "version.txt;." --hidden-import webview.platforms.edgechromium --hidden-import flask --hidden-import flask_cors --hidden-import sqlalchemy --hidden-import sqlalchemy.dialects.sqlite --hidden-import backend.routes.profiles --hidden-import backend.routes.years --hidden-import backend.routes.months --hidden-import backend.routes.update main.py
if errorlevel 1 ( echo ERROR: build failed! & pause & exit /b 1 )

echo [3/4] Building setup.exe (installer)...
python -m PyInstaller --noconfirm --clean --name setup --onefile --noconsole --add-data "dist\FuelTracker;app" installer.py
if errorlevel 1 ( echo ERROR: setup.exe build failed! & pause & exit /b 1 )

echo.
echo ============================================================
echo   Done!
echo   Installer:      dist\setup.exe
echo   Portable EXE:   dist\FuelTracker\FuelTracker.exe
echo.
echo   To release an update:
echo     1. Bump version in version.txt
echo     2. Run this bat to build
echo     3. Create GitHub Release with tag v1.x.x
echo     4. Upload dist\FuelTracker\FuelTracker.exe to the release
echo ============================================================
pause
