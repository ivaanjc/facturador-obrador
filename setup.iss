[Setup]
AppName=Facturador Obrador Belis
AppVersion={#AppVersion}
SetupIconFile=fuentes-letra\icono.ico
DefaultDirName={localappdata}\ObradorBelis
DisableDirPage=yes
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
; Guarda el nuevo ejecutable sobrescribiendo el nombre exacto que tenía el anterior
Source: "dist\facturador2026.exe"; DestDir: "{app}"; DestName: "{code:GetTargetExeName}"; Flags: ignoreversion restartreplace

; Fuentes y logo
Source: "fuentes-letra\*"; DestDir: "{app}\fuentes-letra"; Flags: ignoreversion recursesubdirs createallsubdirs

[Run]
; Inicia el archivo con el nombre que se acaba de actualizar
Filename: "{app}\{code:GetTargetExeName}"; Description: "Iniciar Facturador"; Flags: nowait postinstall skipifsilent

[Icons]
Name: "{autodesktop}\Facturador Obrador Belis"; Filename: "{app}\{code:GetTargetExeName}"; IconFilename: "{app}\fuentes-letra\icono.ico"; Tasks: desktopicon
[Code]
// Función que obtiene el nombre del .exe recibido por parámetro o usa el predeterminado
function GetTargetExeName(Param: String): String;
var
  CustomName: String;
begin
  CustomName := ExpandConstant('{param:EXENAME}');
  if CustomName <> '' then
    Result := CustomName
  else
    Result := 'facturador2026.exe';
end;

procedure DeinitializeSetup();
var
  InstallerTmp: String;
begin
  // Limpia el instalador descargado de %TEMP%
  InstallerTmp := ExpandConstant('{tmp}\Instalador_Facturador_update.exe');
  if FileExists(InstallerTmp) then
    RestartReplace(InstallerTmp, '');
end;