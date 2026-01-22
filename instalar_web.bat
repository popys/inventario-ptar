@echo off
title Instalacion Sistema de Inventario PTAR - Web
color 0B

echo.
echo ========================================
echo   INSTALACION - INVENTARIO PTAR WEB
echo ========================================
echo.
echo Instalando dependencias necesarias...
echo.
echo Este proceso puede tardar unos minutos.
echo Por favor espere...
echo.
echo ========================================
echo.

pip install -r requirements_web.txt

echo.
echo ========================================
echo.
echo Instalacion completada exitosamente!
echo.
echo Para iniciar el servidor web ejecute:
echo    ejecutar_web.bat
echo.
echo O desde la linea de comandos:
echo    python app.py
echo.
echo ========================================
echo.

pause
