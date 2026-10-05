[Setup]
AppName=Facturador Obrador Belis
AppVersion={#AppVersion}
DefaultDirName={localappdata}\ObradorBelis
DisableDirPage=yes
; OBLIGATORIO: 'no' para que obedezca siempre al parámetro /DIR recibido por comando
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
; Solo 'ignoreversion': fuerza la sobrescritura directa en caliente
Source: "dist\facturador2026.exe"; DestDir: "{app}"; DestName: "{code:GetTargetExeName}"; Flags: ignoreversion
Source: "redist\vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

; Fuentes, logo e icono
Source: "fuentes-letra\*"; DestDir: "{app}\fuentes-letra"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autodesktop}\Facturador Obrador Belis"; Filename: "{app}\{code:GetTargetExeName}"; IconFilename: "{app}\fuentes-letra\icono.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{code:GetTargetExeName}"; WorkingDir: "{app}"; Flags: nowait
Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/install /passive /norestart"; StatusMsg: "Instalando componentes necesarios del sistema..."; Flags: waituntilterminated

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