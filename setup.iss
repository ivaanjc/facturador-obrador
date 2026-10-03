[Setup]
AppName=Facturador Obrador Belis
AppVersion={#AppVersion}
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

[InstallDelete]
; Limpieza de accesos directos antiguos con nombres genéricos
Type: files; Name: "{autodesktop}\facturador2026.exe.lnk"
Type: files; Name: "{autodesktop}\facturador2026.lnk"
Type: files; Name: "{userdesktop}\facturador2026.exe.lnk"
Type: files; Name: "{userdesktop}\facturador2026.lnk"
Type: files; Name: "{app}\facturador2026_update.tmp"
Type: files; Name: "{app}\*.old"

[Files]
; Binario principal (ignora versión para sobrescribir siempre)
Source: "dist\facturador2026.exe"; DestDir: "{app}"; Flags: ignoreversion

; Fuentes y logo en su subcarpeta sin tocar archivos JSON
Source: "fuentes-letra\*"; DestDir: "{app}\fuentes-letra"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Facturador Obrador Belis"; Filename: "{app}\facturador2026.exe"
Name: "{autodesktop}\Facturador Obrador Belis"; Filename: "{app}\facturador2026.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\facturador2026.exe"; Description: "Iniciar Facturador"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  OldExe: String;
  Retries: Integer;
begin
  // Se ejecuta tras copiar el binario nuevo y antes de arrancar la aplicación
  if CurStep = ssPostInstall then
  begin
    OldExe := ExpandConstant('{param:OLDEXE}');
    
    // Si se especificó el parámetro /OLDEXE y el archivo existe
    if (OldExe <> '') and FileExists(OldExe) then
    begin
      // Solo borrar si el archivo antiguo tiene un nombre distinto al nuevo destino
      if CompareText(OldExe, ExpandConstant('{app}\facturador2026.exe')) <> 0 then
      begin
        Retries := 0;
        while FileExists(OldExe) and (Retries < 5) do
        begin
          if DeleteFile(OldExe) then
            Break;
          Sleep(300);
          Retries := Retries + 1;
        end;
        // Si el proceso previo aún retiene el archivo, programar el borrado al reiniciar o liberar
        if FileExists(OldExe) then
          RestartReplace(OldExe, '');
      end;
    end;
  end;
end;

procedure DeinitializeSetup();
var
  InstallerTmp: String;
begin
  // Marca el propio instalador descargado en %TEMP% para borrarse tras salir
  InstallerTmp := ExpandConstant('{tmp}\Instalador_Facturador_update.exe');
  if FileExists(InstallerTmp) then
    RestartReplace(InstallerTmp, '');
end;