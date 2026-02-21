; setup_pos.iss - Instalador Sistema POS Venialgo Sistemas
; Abrir con Inno Setup 6 y presionar F9 para compilar

[Setup]
AppId={{A1B2C3D4-1111-2222-3333-VENIALGOSISTEMAS}}
AppName=Sistema POS
AppVersion=1.1
AppVerName=Sistema POS v1.1
AppPublisher=Venialgo Sistemas
AppPublisherURL=https://www.venialgosistemas.com
AppSupportURL=https://www.venialgosistemas.com
AppContact=davenialgo@proton.me
AppCopyright=Copyright (C) 2024 Venialgo Sistemas
DefaultDirName={autopf}\VenialgoPOS
DefaultGroupName=Venialgo Sistemas
AllowNoIcons=yes
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
CloseApplications=yes
PrivilegesRequired=admin
MinVersion=10.0
OutputDir=Output
OutputBaseFilename=POS_Setup_v1.1
SetupIconFile=..\assets\app_icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create desktop icon"

[Files]
Source: "..\dist\POS\POS.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\POS\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\assets\VenialgoSistemasLogo.png"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "..\assets\app_icon.ico"; DestDir: "{app}\assets"; Flags: ignoreversion


[Dirs]
Name: "{app}\backups"
Name: "{app}\logs"
Name: "{app}\assets\logos"

[Icons]
Name: "{group}\Sistema POS"; Filename: "{app}\POS.exe"
Name: "{group}\Uninstall Sistema POS"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Sistema POS"; Filename: "{app}\POS.exe"; Tasks: desktopicon
Name: "{autoprograms}\Venialgo POS"; Filename: "{app}\POS.exe"; IconFilename: "{app}\assets\app_icon.ico"
Name: "{autodesktop}\Venialgo POS"; Filename: "{app}\POS.exe"; IconFilename: "{app}\assets\app_icon.ico"; Tasks: desktopicon

[Registry]
Root: HKLM; Subkey: "SOFTWARE\VenialgoPOS"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\VenialgoPOS"; ValueType: string; ValueName: "Version"; ValueData: "1.1"
Root: HKLM; Subkey: "SOFTWARE\VenialgoPOS"; ValueType: string; ValueName: "Publisher"; ValueData: "Venialgo Sistemas"

[Run]
Filename: "{app}\POS.exe"; Description: "Launch Sistema POS"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "taskkill"; Parameters: "/F /IM POS.exe"; Flags: runhidden; RunOnceId: "CerrarPOS"

[UninstallDelete]
Type: files; Name: "{app}\.integrity"
Type: filesandordirs; Name: "{app}\logs"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  if not (GetWindowsVersion >= $0A000000) then
  begin
    MsgBox('This software requires Windows 10 or higher.', mbError, MB_OK);
    Result := False;
  end;
end;

procedure InitializeWizard;
begin
  WizardForm.WelcomeLabel2.Caption :=
    'This wizard will install Sistema POS v1.1.' + #13#10 + #13#10 +
    'Developer: Venialgo Sistemas' + #13#10 +
    'Email:     davenialgo@proton.me' + #13#10 +
    'WhatsApp:  +595 994-686 493' + #13#10 + #13#10 +
    'Please close all other applications before continuing.';
end;
