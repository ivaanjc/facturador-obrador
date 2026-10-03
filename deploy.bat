@echo off
set /p VERSION="Introduce la nueva version (ej. 1.1.0): "

echo.
echo [1/5] Compilando facturador2026.py con PyInstaller...
pyinstaller --noconsole --onefile --clean ^
    --add-data "logo.png;." ^
    --collect-all customtkinter ^
    facturador2026.py

if errorlevel 1 (
    echo Error durante la compilacion.
    pause
    exit /b %errorlevel%
)

echo.
echo [2/5] Creando instalador independiente con Inno Setup...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DAppVersion=%VERSION% setup.iss

if errorlevel 1 (
    echo Error al generar el instalador.
    pause
    exit /b %errorlevel%
)

echo.
echo [3/5] Actualizando version.json...
(
echo {
echo    "version": "%VERSION%",
echo    "url": "https://github.com/ivaanjc/facturador-obrador/releases/download/v%VERSION%/Instalador_Facturador.exe"
echo }
) > version.json

echo.
echo [4/5] Sincronizando con Git...
git add -A
git commit -m "Lanzamiento v%VERSION%"
git push origin main

echo.
echo [5/5] Creando Release en GitHub y subiendo Instalador_Facturador.exe...
gh release create v%VERSION% dist_installer/Instalador_Facturador.exe --title "Version %VERSION%" --notes "Actualizacion automatica v%VERSION%"

echo.
echo ===============================================
echo  Despliegue completado con exito.
echo ===============================================
pause