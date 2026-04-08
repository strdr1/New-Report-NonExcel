#define MyAppName "Учёт топлива"
#define MyAppVersion "1.0"
#define MyAppPublisher "strdr1"
#define MyAppURL "https://github.com/strdr1/New-Report-NonExcel"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
; Пользователь выбирает папку сам — по умолчанию C:\Учёт топлива
DefaultDirName=C:\{#MyAppName}
DefaultGroupName={#MyAppName}
DirExistsWarning=no
AllowNoIcons=yes
OutputDir=dist\installer
OutputBaseFilename=FuelTracker_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Не требуем admin — пишем куда пользователь выбрал
PrivilegesRequiredOverridesAllowed=dialog
PrivilegesRequired=lowest

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлыки на рабочем столе"; GroupDescription: "Дополнительно:"; Flags: checked

[Dirs]
; Полные права на папку установки (для записи БД)
Name: "{app}"; Permissions: everyone-full

[Files]
Source: "dist\FuelTracker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Учёт топлива";                Filename: "{app}\FuelTracker.exe";       WorkingDir: "{app}"; Comment: "Запуск в окне приложения"
Name: "{group}\Учёт топлива (Сервер)";       Filename: "{app}\FuelTrackerServer.exe"; WorkingDir: "{app}"; Comment: "Запуск сервера — доступ с телефона"
Name: "{group}\Удалить {#MyAppName}";        Filename: "{uninstallexe}"

Name: "{autodesktop}\Учёт топлива";          Filename: "{app}\FuelTracker.exe";       WorkingDir: "{app}"; Comment: "Запуск в окне приложения";           Tasks: desktopicon
Name: "{autodesktop}\Учёт топлива (Сервер)"; Filename: "{app}\FuelTrackerServer.exe"; WorkingDir: "{app}"; Comment: "Запуск сервера — доступ с телефона"; Tasks: desktopicon

[Run]
Filename: "{app}\FuelTracker.exe"; Description: "Запустить {#MyAppName}"; Flags: nowait postinstall skipifsilent
