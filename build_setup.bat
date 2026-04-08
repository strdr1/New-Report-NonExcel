@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Building FuelTracker Setup...

echo [1/6] Installing pyinstaller...
python -m pip install pyinstaller -q

echo [2/6] Building FuelTracker.exe (desktop)...
python -m PyInstaller --noconfirm --clean --name FuelTracker --onedir --noconsole --add-data "frontend;frontend" --add-data "backend;backend" --add-data "version.txt;." --hidden-import webview.platforms.edgechromium --hidden-import flask --hidden-import flask_cors --hidden-import sqlalchemy --hidden-import sqlalchemy.dialects.sqlite --hidden-import backend.routes.profiles --hidden-import backend.routes.years --hidden-import backend.routes.months --hidden-import backend.routes.update main.py
if errorlevel 1 ( echo ERROR: FuelTracker build failed! & pause & exit /b 1 )

echo [3/6] Building FuelTrackerServer.exe (server)...
python -m PyInstaller --noconfirm --clean --name FuelTrackerServer --onedir --console --add-data "frontend;frontend" --add-data "backend;backend" --add-data "version.txt;." --hidden-import flask --hidden-import flask_cors --hidden-import sqlalchemy --hidden-import sqlalchemy.dialects.sqlite --hidden-import backend.routes.profiles --hidden-import backend.routes.years --hidden-import backend.routes.months --hidden-import backend.routes.update server.py
if errorlevel 1 ( echo ERROR: FuelTrackerServer build failed! & pause & exit /b 1 )

echo [4/6] Merging into one folder...
xcopy /E /Y "dist\FuelTrackerServer\*" "dist\FuelTracker\" >nul

echo [5/6] Downloading nginx...
if not exist "nginx_win\nginx.exe" (
    mkdir nginx_win 2>nul
    powershell -Command "Invoke-WebRequest -Uri 'https://nginx.org/download/nginx-1.26.3.zip' -OutFile '%TEMP%\nginx.zip'"
    powershell -Command "Expand-Archive -Path '%TEMP%\nginx.zip' -DestinationPath '%TEMP%\nginx_ex' -Force"
    xcopy /E /Y "%TEMP%\nginx_ex\nginx-1.26.3\*" "nginx_win\" >nul
    copy /Y "nginx\nginx.conf" "nginx_win\conf\nginx.conf" >nul
)
xcopy /E /Y "nginx_win\*" "dist\FuelTracker\nginx\" >nul
mkdir "dist\FuelTracker\nginx\logs" 2>nul

echo [6/6] Building setup.exe...
python -m PyInstaller --noconfirm --clean --name setup --onefile --noconsole --add-data "dist\FuelTracker;app" installer.py
if errorlevel 1 ( echo ERROR: setup.exe build failed! & pause & exit /b 1 )

echo.
echo Done! Installer: dist\setup.exe
pause
