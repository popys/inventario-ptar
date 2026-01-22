@echo off
echo ================================================
echo   INSTALACION SISTEMA DE INVENTARIO PTAR
echo ================================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no está instalado en el sistema
    echo Por favor instala Python desde: https://www.python.org/downloads/
    echo Asegurate de marcar la casilla "Add Python to PATH" durante la instalacion
    pause
    exit /b 1
)

echo [OK] Python detectado
echo.

REM Actualizar pip
echo Actualizando pip...
python -m pip install --upgrade pip

echo.
echo Instalando dependencias...
python -m pip install -r requirements.txt

echo.
echo ================================================
echo   INSTALACION COMPLETADA
echo ================================================
echo.
echo Para ejecutar el programa, ejecuta:
echo     python inventario_ptar.py
echo.
echo O haz doble clic en: ejecutar_inventario.bat
echo.
pause
