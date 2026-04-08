#define MyAppName "Fuel Tracker"
#define MyAppVersion "1.0"
#define MyAppPublisher "strdr1"
#define MyAppURL "https://github.com/strdr1/New-Report-NonExcel"
#define MyAppExeName "FuelTracker.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist\installer
OutputBaseFilename=FuelTracker_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Основное приложение (собранное PyInstaller)
Source: "dist\FuelTracker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; nginx
Source: "nginx_win\*"; DestDir: "{app}\nginx"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: NginxExists

; Скрипты запуска
Source: "start.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "start_server.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Десктоп приложение
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\{#MyAppName} - Сервер (для телефона)"; Filename: "{app}\start_server.bat"; WorkingDir: "{app}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Рабочий стол
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{autodesktop}\{#MyAppName} (Сервер)"; Filename: "{app}\start_server.bat"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function NginxExists: Boolean;
begin
  Result := FileExists(ExpandConstant('{src}\nginx_win\nginx.exe'));
end;
