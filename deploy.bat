@echo off
setlocal enabledelayedexpansion

set /p VERSION="Introduce la nueva version (ej. 1.2.1): "
if "%VERSION%"=="" (
    echo [ERROR] La version no puede estar vacia.
    pause
    exit /b 1
)

set /p MSG="Mensaje de cambios (Enter para omitir): "
if "%MSG%"=="" set MSG=Actualizacion a version %VERSION%

echo.
echo [1/4] Compilando con PyInstaller...
pyinstaller --noconsole --onefile --clean ^
    --icon "fuentes-letra\icono.ico" ^
    --add-data "fuentes-letra;fuentes-letra" ^
    --add-binary "%LOCALAPPDATA%\Programs\Python\Python312\vcruntime140.dll;." ^
    --add-binary "%LOCALAPPDATA%\Programs\Python\Python312\vcruntime140_1.dll;." ^
    --collect-all customtkinter ^
    facturador2026.py

if errorlevel 1 (
    echo [ERROR] Fallo la compilacion de PyInstaller.
    pause
    exit /b 1
)

if not exist "dist\facturador2026.exe" (
    echo [ERROR] No se encontro el archivo dist\facturador2026.exe generado.
    pause
    exit /b 1
)

echo.
echo [2/4] Actualizando version.json...
(
echo {
echo     "version": "%VERSION%",
echo     "url": "https://github.com/ivaanjc/facturador-obrador/releases/download/v%VERSION%/facturador2026.exe"
echo }
) > version.json

echo.
echo [3/4] Guardando en Git...
git add -A
git commit -m "%MSG% - v%VERSION%"
git push origin main
if errorlevel 1 (
    echo [ERROR] Fallo el git push.
    pause
    exit /b 1
)

echo.
echo [4/4] Publicando Release en GitHub con el ejecutable directo...
gh release create v%VERSION% dist\facturador2026.exe --title "Version %VERSION%" --notes "%MSG%"
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