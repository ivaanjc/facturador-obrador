[Setup]
AppName=Facturador Obrador Belis
AppVersion={#AppVersion}
DefaultDirName={localappdata}\ObradorBelis
DisableDirPage=yes
; Permite ver la pantalla final de finalización con la casilla de abrir
DisableFinishedPage=no
UsePreviousAppDir=no
AllowRootDirectory=yes
AppendDefaultDirName=no
OutputDir=dist_installer
OutputBaseFilename=Instalador_Facturador
Compression=lzma2
SolidCompression=yes
CloseApplications=yes
PrivilegesRequired=lowest
SetupIconFile=fuentes-letra\icono.ico

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el Escritorio"; GroupDescription: "Iconos adicionales:"

[Files]
Source: "dist\facturador2026.exe"; DestDir: "{app}"; DestName: "{code:GetTargetExeName}"; Flags: ignoreversion
Source: "fuentes-letra\*"; DestDir: "{app}\fuentes-letra"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autodesktop}\Facturador Obrador Belis"; Filename: "{app}\{code:GetTargetExeName}"; IconFilename: "{app}\fuentes-letra\icono.ico"; Tasks: desktopicon

[Run]
; 'postinstall' crea la casilla en la última pantalla para que el usuario elija si abrirlo o no
Filename: "{app}\{code:GetTargetExeName}"; Description: "Ejecutar Facturador Obrador Belis"; Flags: postinstall nowait

[Code]
function GetTargetExeName(Param: String): String;
var
  CustomName: String;
begin
  CustomName := RemoveQuotes(ExpandConstant('{param:EXENAME}'));
  if CustomName <> '' then
    Result := CustomName
  else
    Result := 'facturador2026.exe';
end;

procedure DeinitializeSetup();
var
  InstallerTmp: String;
begin
  InstallerTmp := ExpandConstant('{tmp}\Instalador_Facturador_update.exe');
  if FileExists(InstallerTmp) then
    RestartReplace(InstallerTmp, '');
end;