[Setup]
AppName=Facturador Obrador Belis
AppVersion={#AppVersion}
DefaultDirName={localappdata}\ObradorBelis
; Oculta la ventana de elegir directorio para que no pregunte nada
DisableDirPage=yes
; Si no se pasa /DIR por comando, intenta recordar la previa
UsePreviousAppDir=yes
OutputDir=dist_installer
OutputBaseFilename=Instalador_Facturador
Compression=lzma2
SolidCompression=yes
CloseApplications=yes
PrivilegesRequired=lowest

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el Escritorio"; GroupDescription: "Iconos adicionales:"

[Files]
Source: "dist\facturador2026.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "fuentes-letra\*"; DestDir: "{app}\fuentes-letra"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Facturador Obrador Belis"; Filename: "{app}\facturador2026.exe"
Name: "{autodesktop}\Facturador Obrador Belis"; Filename: "{app}\facturador2026.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\facturador2026.exe"; Description: "Iniciar Facturador"; Flags: nowait postinstall skipifsilent