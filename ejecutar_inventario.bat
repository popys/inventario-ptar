@echo off
title Sistema de Inventario PTAR
echo Iniciando Sistema de Inventario PTAR...
python inventario_ptar.py
if errorlevel 1 (
    echo.
    echo [ERROR] Ocurrio un error al ejecutar el programa
    echo.
    pause
)
