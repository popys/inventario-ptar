@echo off
title Reparar Base de Datos - Sistema de Inventario PTAR
color 0A

echo.
echo ============================================================
echo      REPARAR BASE DE DATOS - SISTEMA DE INVENTARIO PTAR
echo ============================================================
echo.
echo Este script verifica y repara problemas comunes de la base
echo de datos, incluyendo el error "database locked".
echo.
echo IMPORTANTE: Cierra todas las aplicaciones que usen la base
echo de datos antes de continuar (version web y escritorio).
echo.
pause

python fix_database.py

echo.
echo ============================================================
echo Presiona cualquier tecla para cerrar esta ventana...
pause >nul
