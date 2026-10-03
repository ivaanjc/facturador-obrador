@echo off
setlocal enabledelayedexpansion

set /p VERSION="Introduce la nueva version (ej. 1.0.2): "
if "%VERSION%"=="" (
    echo [ERROR] La version no puede estar vacia.
    pause
    exit /b 1
)

set /p MSG="Mensaje de cambios (Enter para omitir): "
if "%MSG%"=="" set MSG=Actualizacion a version %VERSION%

echo.
echo [1/5] Compilando con PyInstaller...
pyinstaller --noconsole --onefile --clean ^
    --icon "fuentes-letra\icono.ico" ^
    --add-data "fuentes-letra;fuentes-letra" ^
    --collect-all customtkinter ^
    facturador2026.py

if errorlevel 1 (
    echo [ERROR] Fallo la compilacion de PyInstaller.
    pause
    exit /b 1
)

echo.
echo [2/5] Buscando Inno Setup y compilando instalador...
set "ISCC_PATH="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"

if "%ISCC_PATH%"=="" (
    echo [ERROR] No se encontro ISCC.exe.
    pause
    exit /b 1
)

"%ISCC_PATH%" /DAppVersion=%VERSION% setup.iss
if errorlevel 1 (
    echo [ERROR] Fallo al compilar el instalador con Inno Setup.
    pause
    exit /b 1
)

echo.
echo [3/5] Actualizando version.json...
(
echo {
echo     "version": "%VERSION%",
echo     "url": "https://github.com/ivaanjc/facturador-obrador/releases/download/v%VERSION%/Instalador_Facturador.exe"
echo }
) > version.json

echo.
echo [4/5] Guardando en Git...
git add -A
git commit -m "%MSG% - v%VERSION%"
git push origin main
if errorlevel 1 (
    echo [ERROR] Fallo el git push.
    pause
    exit /b 1
)

echo.
echo [5/5] Publicando Release en GitHub...
gh release create v%VERSION% dist_installer\Instalador_Facturador.exe --title "Version %VERSION%" --notes "%MSG%"
if errorlevel 1 (
    echo [ERROR] Fallo al crear la release con GitHub CLI.
    pause
    exit /b 1
)

echo.
echo ======================================================
echo  DESPLIEGUE FINALIZADO CON EXITO (v%VERSION%)
echo ======================================================
pause