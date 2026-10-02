@echo off
set /p VERSION="Introduce la nueva version (ej. 1.0.1): "
set /p MSG="Mensaje de cambios (deja en blanco para mensaje por defecto): "

if "%MSG%"=="" (
    set MSG=Actualizacion a version %VERSION%
)

echo.
echo [1/4] Compilando ejecutable con PyInstaller...
pyinstaller --noconsole --onefile --clean ^
    --add-data "logo.png;." ^
    --collect-all customtkinter ^
    facturador2026.py

if errorlevel 1 (
    echo.
    echo [ERROR] Fallo durante la compilacion. Despliegue cancelado.
    pause
    exit /b %errorlevel%
)

echo.
echo [2/4] Generando version.json actualizado...
(
echo {
echo    "version": "%VERSION%",
echo    "url": "https://github.com/ivaanjc/facturador-obrador/releases/download/v%VERSION%/facturador2026.exe"
echo }
) > version.json

echo.
echo [3/4] Sincronizando codigo fuente y version.json con Git...
git add -A
git commit -m "%MSG% (v%VERSION%)"
git push origin main
if errorlevel 1 (
    echo.
    echo [ERROR] No se pudo hacer push a main. Revisa tu conexion o conflictos de Git.
    pause
    exit /b %errorlevel%
)

echo.
echo [4/4] Creando Release en GitHub y subiendo binario...
gh release create v%VERSION% dist/facturador2026.exe --title "Version %VERSION%" --notes "%MSG%"

if errorlevel 1 (
    echo.
    echo [ERROR] Fallo al publicar la release en GitHub CLI.
    pause
    exit /b %errorlevel%
)

echo.
echo ======================================================
echo  Despliegue completado con exito para la v%VERSION%
echo ======================================================
pause