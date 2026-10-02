@echo off
set /p VERSION="Introduce la nueva version (ej. 1.0.1): "

echo [1/4] Compilando con PyInstaller...
pyinstaller --noconsole --onefile --clean app.py
if errorlevel 1 (
    echo Error durante la compilacion.
    exit /b %errorlevel%
)

echo [2/4] Actualizando version.json...
(
echo {
echo   "version": "%VERSION%",
echo   "url": "https://github.com/ivaanjc/facturador-obrador/releases/download/v%VERSION%/facturador2026.exe"
echo }
) > version.json

echo [3/4] Sincronizando con Git...
git add version.json
git commit -m "Bump version a %VERSION%"
git push origin main

echo [4/4] Publicando Release en GitHub...
gh release create v%VERSION% dist/facturador2026.exe --title "Version %VERSION%" --notes "Actualizacion automatica a v%VERSION%"

echo Despliegue completado con exito.
pause