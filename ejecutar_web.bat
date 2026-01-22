@echo off
title Sistema de Inventario PTAR - Servidor Web
color 0A

echo.
echo ========================================
echo   SISTEMA DE INVENTARIO PTAR - WEB
echo ========================================
echo.
echo Iniciando servidor web...
echo.
echo La aplicacion se abrira automaticamente en tu navegador
echo en unos segundos...
echo.
echo URL: http://localhost:5000
echo.
echo Para detener el servidor presiona Ctrl+C
echo.
echo ========================================
echo.

timeout /t 3 /nobreak >nul
start http://localhost:5000

python app.py

pause
