; ================================================================
; setup_pos.iss - Instalador Sistema POS Venialgo Sistemas
; ================================================================
;
; PASOS ANTES DE COMPILAR:
;   1. Ejecutar: python build_exe.py       (genera dist/POS/)
;   2. Abrir este archivo con Inno Setup 6
;   3. Presionar F9 para compilar
;   4. El instalador queda en: installer/Output/VenialgoPOS_Setup_v1.1.exe
;
; ================================================================

#define AppName        "Venialgo POS"
#define AppVersion     "1.1"
#define AppPublisher   "Venialgo Sistemas"
#define AppContact     "davenialgo@proton.me"
#define AppWhatsApp    "+595 994-686 493"
#define AppURL         "www.venialgosistemas.com"
#define AppExeName     "POS.exe"
#define AppYear        "2025"

; ================================================================
[Setup]
AppId={{A1B2C3D4-5555-6666-7777-VENIALGOV11POS}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} v{#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=https://{#AppURL}
AppSupportURL=https://{#AppURL}
AppContact={#AppContact}
AppCopyright=Copyright (C) {#AppYear} {#AppPublisher}

DefaultDirName={autopf}\VenialgoPOS
DefaultGroupName={#AppPublisher}

AllowNoIcons=yes
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=120
DisableProgramGroupPage=yes
CloseApplications=yes
PrivilegesRequired=admin
MinVersion=10.0

OutputDir=Output
OutputBaseFilename=VenialgoPOS_Setup_v{#AppVersion}

; Ícono del instalador
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\assets\icon.ico
UninstallDisplayName={#AppName} v{#AppVersion}

LicenseFile=..\contrato_uso.txt

; ================================================================
[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

; ================================================================
[Tasks]
Name: "desktopicon";   Description: "Crear icono en el Escritorio";       GroupDescription: "Iconos adicionales:"; Flags: checked
Name: "startmenuicon"; Description: "Crear acceso en Menu Inicio";        GroupDescription: "Iconos adicionales:"; Flags: checked
Name: "startuprun";    Description: "Iniciar automaticamente con Windows"; GroupDescription: "Inicio automatico:";  Flags: unchecked

; ================================================================
[Files]
Source: "..\dist\POS\{#AppExeName}";  DestDir: "{app}";           Flags: ignoreversion
Source: "..\dist\POS\_internal\*";   DestDir: "{app}\_internal";  Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\assets\*";               DestDir: "{app}\assets";     Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "..\contrato_uso.txt";       DestDir: "{app}";            Flags: ignoreversion skipifsourcedoesntexist

; ================================================================
[Dirs]
Name: "{app}\backups"
Name: "{app}\logs"
Name: "{app}\assets\logos"

; ================================================================
[Icons]
; Menú Inicio
Name: "{group}\{#AppName}";             Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\assets\icon.ico"; Comment: "Sistema de Punto de Venta"; Tasks: startmenuicon
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"; Tasks: startmenuicon

; Escritorio - UN SOLO acceso directo
Name: "{commondesktop}\{#AppName}";     Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\assets\icon.ico"; Comment: "Sistema de Punto de Venta"; Tasks: desktopicon

; ================================================================
[Registry]
Root: HKLM; Subkey: "SOFTWARE\VenialgoPOS"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}";            Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\VenialgoPOS"; ValueType: string; ValueName: "Version";     ValueData: "{#AppVersion}"
Root: HKLM; Subkey: "SOFTWARE\VenialgoPOS"; ValueType: string; ValueName: "Publisher";   ValueData: "{#AppPublisher}"
Root: HKLM; Subkey: "SOFTWARE\VenialgoPOS"; ValueType: string; ValueName: "Contact";     ValueData: "{#AppContact}"
Root: HKCU; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#AppName}"; ValueData: """{app}\{#AppExeName}"""; Tasks: startuprun; Flags: uninsdeletevalue

; ================================================================
[Run]
Filename: "{app}\{#AppExeName}"; Description: "Iniciar {#AppName} ahora"; Flags: nowait postinstall skipifsilent

; ================================================================
[UninstallRun]
Filename: "taskkill"; Parameters: "/F /IM {#AppExeName}"; Flags: runhidden; RunOnceId: "CerrarPOS"

; ================================================================
[UninstallDelete]
Type: files;          Name: "{app}\.integrity"
Type: files;          Name: "{app}\contrato_uso.accepted"
Type: files;          Name: "{app}\.first_run_done"
Type: filesandordirs; Name: "{app}\logs"

; ================================================================
[Code]

function InitializeSetup(): Boolean;
begin
  Result := True;
  if not (GetWindowsVersion >= $0A000000) then
  begin
    MsgBox(
      'Este software requiere Windows 10 o superior.' + #13#10 +
      'Por favor actualice su sistema operativo antes de instalar.',
      mbError, MB_OK
    );
    Result := False;
  end;
end;

procedure InitializeWizard;
begin
  WizardForm.WelcomeLabel2.Caption :=
    'Este asistente instalara ' + ExpandConstant('{#AppName}') +
    ' v' + ExpandConstant('{#AppVersion}') + ' en su equipo.' +
    #13#10 + #13#10 +
    'Desarrollado por: ' + ExpandConstant('{#AppPublisher}') +
    #13#10 +
    'Email:     ' + ExpandConstant('{#AppContact}') +
    #13#10 +
    'WhatsApp:  ' + ExpandConstant('{#AppWhatsApp}') +
    #13#10 + #13#10 +
    'Cierre todas las demas aplicaciones antes de continuar.';
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  OldShortcut: string;
begin
  if CurStep = ssInstall then
  begin
    // Limpiar accesos directos de versiones anteriores con nombres distintos
    OldShortcut := ExpandConstant('{commondesktop}\Sistema POS.lnk');
    if FileExists(OldShortcut) then DeleteFile(OldShortcut);
    OldShortcut := ExpandConstant('{commondesktop}\POS.lnk');
    if FileExists(OldShortcut) then DeleteFile(OldShortcut);
    OldShortcut := ExpandConstant('{commondesktop}\Sistema POS v1.1.lnk');
    if FileExists(OldShortcut) then DeleteFile(OldShortcut);
    OldShortcut := ExpandConstant('{commondesktop}\Venialgo POS v1.1.lnk');
    if FileExists(OldShortcut) then DeleteFile(OldShortcut);
  end;

  if CurStep = ssPostInstall then
  begin
    SaveStringToFile(
      ExpandConstant('{app}\first_install.flag'),
      'instalado_' + GetDateTimeString('yyyymmdd', '-', ':'),
      False
    );
  end;
end;
