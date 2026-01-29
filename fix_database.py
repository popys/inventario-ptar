#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar y arreglar problemas de la base de datos SQLite
"""
import sqlite3
import os
import sys

# Configurar encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = 'inventario_ptar.db'

def verificar_y_arreglar_db():
    """Verifica y arregla problemas comunes de la base de datos"""

    print("=" * 60)
    print("VERIFICANDO BASE DE DATOS")
    print("=" * 60)

    if not os.path.exists(DB_PATH):
        print(f"ERROR: La base de datos {DB_PATH} no existe")
        return False

    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        cursor = conn.cursor()

        # 1. Verificar integridad de la base de datos
        print("\n1. Verificando integridad de la base de datos...")
        cursor.execute('PRAGMA integrity_check')
        resultado = cursor.fetchone()
        if resultado[0] == 'ok':
            print("   [OK] Base de datos integra")
        else:
            print(f"   [ERROR] Problemas encontrados: {resultado[0]}")

        # 2. Verificar modo journal
        print("\n2. Verificando modo journal...")
        cursor.execute('PRAGMA journal_mode')
        modo_actual = cursor.fetchone()[0]
        print(f"   Modo actual: {modo_actual}")

        if modo_actual.upper() != 'WAL':
            print("   Cambiando a modo WAL para mejor concurrencia...")
            cursor.execute('PRAGMA journal_mode=WAL')
            nuevo_modo = cursor.fetchone()[0]
            print(f"   [OK] Modo cambiado a: {nuevo_modo}")
        else:
            print("   [OK] Ya esta en modo WAL")

        # 3. Verificar configuración de timeout
        print("\n3. Configuracion de timeout...")
        cursor.execute('PRAGMA busy_timeout')
        timeout = cursor.fetchone()[0]
        print(f"   Timeout actual: {timeout}ms")

        if timeout < 30000:
            print("   Aumentando timeout a 30 segundos...")
            cursor.execute('PRAGMA busy_timeout = 30000')
            print("   [OK] Timeout actualizado")
        else:
            print("   [OK] Timeout adecuado")

        # 4. Optimizar base de datos
        print("\n4. Optimizando base de datos...")
        cursor.execute('VACUUM')
        print("   [OK] Base de datos optimizada")

        # 5. Analizar tablas para mejorar rendimiento
        print("\n5. Analizando tablas...")
        cursor.execute('ANALYZE')
        print("   [OK] Analisis completado")

        # 6. Verificar que no hay transacciones abiertas
        print("\n6. Verificando transacciones...")
        try:
            conn.commit()
            print("   [OK] No hay transacciones pendientes")
        except Exception as e:
            print(f"   [ERROR] Error: {e}")

        # 7. Mostrar información de las tablas
        print("\n7. Información de tablas:")
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        tablas = cursor.fetchall()

        for tabla in tablas:
            nombre_tabla = tabla[0]
            cursor.execute(f'SELECT COUNT(*) FROM {nombre_tabla}')
            count = cursor.fetchone()[0]
            print(f"   - {nombre_tabla}: {count} registros")

        conn.close()

        print("\n" + "=" * 60)
        print("VERIFICACION COMPLETADA")
        print("=" * 60)
        print("\nLa base de datos ha sido verificada y optimizada.")
        print("Ahora puede intentar usar la aplicacion nuevamente.")

        return True

    except sqlite3.OperationalError as e:
        print(f"\n[ERROR]: {e}")
        print("\nPosibles soluciones:")
        print("1. Cierre la aplicacion de escritorio (inventario_ptar.py) si esta abierta")
        print("2. Cierre el servidor web Flask si esta corriendo")
        print("3. Verifique que ningun otro programa este usando la base de datos")
        return False
    except Exception as e:
        print(f"\n[ERROR INESPERADO]: {e}")
        return False

if __name__ == '__main__':
    verificar_y_arreglar_db()
