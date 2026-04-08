@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo   Building FuelTracker Setup (2 EXEs)
echo ============================================================

REM [1] Зависимости
echo [1/6] Installing build dependencies...
python -m pip install pyinstaller -q

REM [2] EXE: десктоп (webview)
echo [2/6] Building FuelTracker.exe (desktop)...
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

if errorlevel 1 ( echo [ERROR] FuelTracker build failed! & pause & exit /b 1 )

REM [3] EXE: сервер (для телефона, с консолью чтобы видеть IP)
echo [3/6] Building FuelTrackerServer.exe (server mode)...
pyinstaller --noconfirm --clean ^
    --name "FuelTrackerServer" ^
    --onedir ^
    --console ^
    --add-data "frontend;frontend" ^
    --add-data "backend;backend" ^
    --hidden-import "flask" ^
    --hidden-import "flask_cors" ^
    --hidden-import "sqlalchemy" ^
    --hidden-import "sqlalchemy.dialects.sqlite" ^
    --hidden-import "backend.routes.profiles" ^
    --hidden-import "backend.routes.years" ^
    --hidden-import "backend.routes.months" ^
    server.py

if errorlevel 1 ( echo [ERROR] FuelTrackerServer build failed! & pause & exit /b 1 )

REM Оба EXE кладём в одну папку dist\FuelTracker
xcopy /E /Y "dist\FuelTrackerServer\*" "dist\FuelTracker\" >nul

REM [4] nginx
echo [4/6] Downloading nginx for Windows...
if not exist "nginx_win\nginx.exe" (
    mkdir nginx_win 2>nul
    powershell -Command "Invoke-WebRequest -Uri 'https://nginx.org/download/nginx-1.26.3.zip' -OutFile '%TEMP%\nginx.zip'"
    powershell -Command "Expand-Archive -Path '%TEMP%\nginx.zip' -DestinationPath '%TEMP%\nginx_extracted' -Force"
    xcopy /E /Y "%TEMP%\nginx_extracted\nginx-1.26.3\*" "nginx_win\" >nul
    copy /Y "nginx\nginx.conf" "nginx_win\conf\nginx.conf" >nul
    echo nginx downloaded.
) else (
    echo nginx already present.
)

REM [5] Копируем nginx в dist
echo [5/6] Copying nginx...
xcopy /E /Y "nginx_win\*" "dist\FuelTracker\nginx\" >nul
mkdir "dist\FuelTracker\nginx\logs" 2>nul

REM [6] Собираем setup.exe (установщик на Python/tkinter)
echo [6/6] Building setup.exe...
pyinstaller --noconfirm --clean ^
    --name "setup" ^
    --onefile ^
    --noconsole ^
    --add-data "dist\FuelTracker;app" ^
    installer.py

if errorlevel 1 ( echo [ERROR] setup.exe build failed! & pause & exit /b 1 )

echo.
echo ============================================================
echo   Done!
echo   Installer: dist\setup.exe
echo   (просто дай пользователю этот файл)
echo ============================================================
pause
