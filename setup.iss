[Setup]
AppName=Facturador Obrador Belis
AppVersion=1.1.0
DefaultDirName={autopf}\ObradorBelis
DefaultGroupName=Obrador Belis
OutputDir=dist_installer
OutputBaseFilename=Instalador_Facturador
Compression=lzma2
SolidCompression=yes
; Evita que se instale si la app está abierta, pidiendo cerrarla
CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el Escritorio"; GroupDescription: "Iconos adicionales:"

[Files]
; Binario principal compilado por PyInstaller
Source: "dist\facturador2026.exe"; DestDir: "{app}"; Flags: ignoreversion
; Logo (si lo usas externo)
Source: "logo.png"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Facturador Obrador Belis"; Filename: "{app}\facturador2026.exe"
Name: "{autodesktop}\Facturador Obrador Belis"; Filename: "{app}\facturador2026.exe"; Tasks: desktopicon

[Run]
; Opción para arrancar la app al finalizar la instalación
Filename: "{app}\facturador2026.exe"; Description: "Iniciar Facturador"; Flags: nowait postinstall skipifsilent