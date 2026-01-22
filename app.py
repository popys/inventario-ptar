from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
from datetime import datetime
import pandas as pd
from io import BytesIO
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ptar-inventario-2025'

# Ruta a la base de datos existente
DB_PATH = 'inventario_ptar.db'

def get_db_connection():
    """Obtiene conexión a la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Inicializa la base de datos si no existe"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabla de materiales
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materiales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            categoria TEXT,
            unidad TEXT,
            cantidad_actual REAL DEFAULT 0,
            stock_minimo REAL DEFAULT 0,
            ubicacion TEXT,
            costo_unitario REAL DEFAULT 0,
            notas TEXT,
            fecha_registro TEXT,
            imagen_ruta TEXT
        )
    ''')

    # Tabla de movimientos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id INTEGER,
            tipo_movimiento TEXT,
            cantidad REAL,
            fecha TEXT,
            responsable TEXT,
            destino_origen TEXT,
            observaciones TEXT,
            FOREIGN KEY (material_id) REFERENCES materiales (id)
        )
    ''')

    # Tabla de préstamos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prestamos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id INTEGER,
            cantidad REAL,
            fecha_prestamo TEXT,
            fecha_devolucion TEXT,
            prestado_a TEXT,
            area_destino TEXT,
            estado TEXT,
            observaciones TEXT,
            FOREIGN KEY (material_id) REFERENCES materiales (id)
        )
    ''')

    # Tabla de material en uso
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS material_en_uso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id INTEGER,
            cantidad REAL,
            equipo_instalacion TEXT,
            fecha_instalacion TEXT,
            responsable TEXT,
            observaciones TEXT,
            FOREIGN KEY (material_id) REFERENCES materiales (id)
        )
    ''')

    conn.commit()
    conn.close()

# Inicializar DB al arrancar
init_database()

# ===============================
# RUTAS PRINCIPALES
# ===============================

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

# ===============================
# API - MATERIALES
# ===============================

@app.route('/api/materiales', methods=['GET'])
def get_materiales():
    """Obtiene todos los materiales con filtros opcionales"""
    categoria = request.args.get('categoria', '')
    ubicacion = request.args.get('ubicacion', '')
    estado = request.args.get('estado', '')
    busqueda = request.args.get('busqueda', '')

    conn = get_db_connection()
    query = 'SELECT * FROM materiales WHERE 1=1'
    params = []

    if categoria and categoria != 'Todas':
        query += ' AND categoria = ?'
        params.append(categoria)

    if ubicacion and ubicacion != 'Todas':
        query += ' AND ubicacion = ?'
        params.append(ubicacion)

    if busqueda:
        query += ' AND (codigo LIKE ? OR nombre LIKE ? OR descripcion LIKE ?)'
        busqueda_param = f'%{busqueda}%'
        params.extend([busqueda_param, busqueda_param, busqueda_param])

    query += ' ORDER BY nombre'

    materiales = conn.execute(query, params).fetchall()
    conn.close()

    # Convertir a lista de diccionarios y aplicar filtro de estado
    result = []
    for m in materiales:
        material = dict(m)

        # Aplicar filtro de estado
        if estado:
            if estado == 'sin_stock' and material['cantidad_actual'] > 0:
                continue
            elif estado == 'stock_bajo' and (material['cantidad_actual'] > material['stock_minimo'] or material['cantidad_actual'] == 0):
                continue
            elif estado == 'stock_normal' and material['cantidad_actual'] <= material['stock_minimo']:
                continue

        # Agregar clase de estado para el frontend
        if material['cantidad_actual'] == 0:
            material['estado_clase'] = 'sin-stock'
        elif material['cantidad_actual'] <= material['stock_minimo']:
            material['estado_clase'] = 'stock-bajo'
        else:
            material['estado_clase'] = 'stock-normal'

        result.append(material)

    return jsonify(result)

@app.route('/api/materiales/<int:id>', methods=['GET'])
def get_material(id):
    """Obtiene un material específico"""
    conn = get_db_connection()
    material = conn.execute('SELECT * FROM materiales WHERE id = ?', (id,)).fetchone()
    conn.close()

    if material:
        return jsonify(dict(material))
    return jsonify({'error': 'Material no encontrado'}), 404

@app.route('/api/materiales', methods=['POST'])
def create_material():
    """Crea un nuevo material"""
    data = request.json

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO materiales (codigo, nombre, descripcion, categoria, unidad,
                                   cantidad_actual, stock_minimo, ubicacion, costo_unitario,
                                   notas, fecha_registro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['codigo'],
            data['nombre'],
            data.get('descripcion', ''),
            data.get('categoria', ''),
            data.get('unidad', ''),
            data.get('cantidad_actual', 0),
            data.get('stock_minimo', 0),
            data.get('ubicacion', ''),
            data.get('costo_unitario', 0),
            data.get('notas', ''),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))

        conn.commit()
        material_id = cursor.lastrowid
        conn.close()

        return jsonify({'success': True, 'id': material_id, 'message': 'Material creado exitosamente'}), 201

    except sqlite3.IntegrityError:
        return jsonify({'error': 'El código de material ya existe'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/materiales/<int:id>', methods=['PUT'])
def update_material(id):
    """Actualiza un material existente"""
    data = request.json

    try:
        conn = get_db_connection()
        conn.execute('''
            UPDATE materiales
            SET codigo = ?, nombre = ?, descripcion = ?, categoria = ?, unidad = ?,
                stock_minimo = ?, ubicacion = ?, costo_unitario = ?, notas = ?
            WHERE id = ?
        ''', (
            data['codigo'],
            data['nombre'],
            data.get('descripcion', ''),
            data.get('categoria', ''),
            data.get('unidad', ''),
            data.get('stock_minimo', 0),
            data.get('ubicacion', ''),
            data.get('costo_unitario', 0),
            data.get('notas', ''),
            id
        ))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Material actualizado exitosamente'})

    except sqlite3.IntegrityError:
        return jsonify({'error': 'El código de material ya existe'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/materiales/<int:id>', methods=['DELETE'])
def delete_material(id):
    """Elimina un material"""
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM materiales WHERE id = ?', (id,))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Material eliminado exitosamente'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===============================
# API - MOVIMIENTOS
# ===============================

@app.route('/api/movimientos', methods=['GET'])
def get_movimientos():
    """Obtiene historial de movimientos"""
    tipo = request.args.get('tipo', '')

    conn = get_db_connection()
    query = '''
        SELECT m.*, mat.nombre as material_nombre, mat.codigo as material_codigo
        FROM movimientos m
        JOIN materiales mat ON m.material_id = mat.id
        WHERE 1=1
    '''
    params = []

    if tipo:
        query += ' AND m.tipo_movimiento = ?'
        params.append(tipo)

    query += ' ORDER BY m.fecha DESC LIMIT 100'

    movimientos = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify([dict(m) for m in movimientos])

@app.route('/api/movimientos/entrada', methods=['POST'])
def registrar_entrada():
    """Registra entrada de material"""
    data = request.json

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Registrar movimiento
        cursor.execute('''
            INSERT INTO movimientos (material_id, tipo_movimiento, cantidad, fecha,
                                    responsable, destino_origen, observaciones)
            VALUES (?, 'ENTRADA', ?, ?, ?, ?, ?)
        ''', (
            data['material_id'],
            data['cantidad'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            data['responsable'],
            data['origen'],
            data.get('observaciones', '')
        ))

        # Actualizar cantidad en inventario
        cursor.execute('''
            UPDATE materiales
            SET cantidad_actual = cantidad_actual + ?
            WHERE id = ?
        ''', (data['cantidad'], data['material_id']))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Entrada registrada exitosamente'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/movimientos/salida', methods=['POST'])
def registrar_salida():
    """Registra salida de material"""
    data = request.json

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Verificar stock disponible
        material = cursor.execute('SELECT cantidad_actual FROM materiales WHERE id = ?',
                                 (data['material_id'],)).fetchone()

        if not material:
            return jsonify({'error': 'Material no encontrado'}), 404

        if material['cantidad_actual'] < data['cantidad']:
            return jsonify({'error': 'Stock insuficiente'}), 400

        # Registrar movimiento
        cursor.execute('''
            INSERT INTO movimientos (material_id, tipo_movimiento, cantidad, fecha,
                                    responsable, destino_origen, observaciones)
            VALUES (?, 'SALIDA', ?, ?, ?, ?, ?)
        ''', (
            data['material_id'],
            data['cantidad'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            data['responsable'],
            data['destino'],
            data.get('observaciones', '')
        ))

        # Actualizar cantidad en inventario
        cursor.execute('''
            UPDATE materiales
            SET cantidad_actual = cantidad_actual - ?
            WHERE id = ?
        ''', (data['cantidad'], data['material_id']))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Salida registrada exitosamente'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===============================
# API - PRÉSTAMOS
# ===============================

@app.route('/api/prestamos', methods=['GET'])
def get_prestamos():
    """Obtiene préstamos activos"""
    conn = get_db_connection()
    prestamos = conn.execute('''
        SELECT p.*, m.nombre as material_nombre, m.codigo as material_codigo
        FROM prestamos p
        JOIN materiales m ON p.material_id = m.id
        WHERE p.estado = 'ACTIVO'
        ORDER BY p.fecha_prestamo DESC
    ''').fetchall()
    conn.close()

    return jsonify([dict(p) for p in prestamos])

@app.route('/api/prestamos', methods=['POST'])
def registrar_prestamo():
    """Registra un préstamo de material"""
    data = request.json

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Verificar stock disponible
        material = cursor.execute('SELECT cantidad_actual FROM materiales WHERE id = ?',
                                 (data['material_id'],)).fetchone()

        if not material:
            return jsonify({'error': 'Material no encontrado'}), 404

        if material['cantidad_actual'] < data['cantidad']:
            return jsonify({'error': 'Stock insuficiente'}), 400

        # Registrar préstamo
        cursor.execute('''
            INSERT INTO prestamos (material_id, cantidad, fecha_prestamo, prestado_a,
                                  area_destino, estado, observaciones)
            VALUES (?, ?, ?, ?, ?, 'ACTIVO', ?)
        ''', (
            data['material_id'],
            data['cantidad'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            data['prestado_a'],
            data['area_destino'],
            data.get('observaciones', '')
        ))

        # Actualizar cantidad en inventario
        cursor.execute('''
            UPDATE materiales
            SET cantidad_actual = cantidad_actual - ?
            WHERE id = ?
        ''', (data['cantidad'], data['material_id']))

        # Registrar movimiento
        cursor.execute('''
            INSERT INTO movimientos (material_id, tipo_movimiento, cantidad, fecha,
                                    responsable, destino_origen, observaciones)
            VALUES (?, 'PRÉSTAMO', ?, ?, ?, ?, ?)
        ''', (
            data['material_id'],
            data['cantidad'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            data['prestado_a'],
            data['area_destino'],
            data.get('observaciones', '')
        ))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Préstamo registrado exitosamente'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/prestamos/<int:id>/devolver', methods=['POST'])
def devolver_prestamo(id):
    """Registra la devolución de un préstamo"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Obtener información del préstamo
        prestamo = cursor.execute('SELECT * FROM prestamos WHERE id = ?', (id,)).fetchone()

        if not prestamo:
            return jsonify({'error': 'Préstamo no encontrado'}), 404

        if prestamo['estado'] != 'ACTIVO':
            return jsonify({'error': 'El préstamo ya fue devuelto'}), 400

        # Actualizar préstamo
        cursor.execute('''
            UPDATE prestamos
            SET estado = 'DEVUELTO', fecha_devolucion = ?
            WHERE id = ?
        ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), id))

        # Devolver cantidad al inventario
        cursor.execute('''
            UPDATE materiales
            SET cantidad_actual = cantidad_actual + ?
            WHERE id = ?
        ''', (prestamo['cantidad'], prestamo['material_id']))

        # Registrar movimiento
        cursor.execute('''
            INSERT INTO movimientos (material_id, tipo_movimiento, cantidad, fecha,
                                    responsable, destino_origen, observaciones)
            VALUES (?, 'DEVOLUCIÓN', ?, ?, ?, ?, ?)
        ''', (
            prestamo['material_id'],
            prestamo['cantidad'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            prestamo['prestado_a'],
            prestamo['area_destino'],
            'Devolución de préstamo'
        ))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Préstamo devuelto exitosamente'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===============================
# API - MATERIAL EN USO
# ===============================

@app.route('/api/material-en-uso', methods=['GET'])
def get_material_en_uso():
    """Obtiene material en uso"""
    conn = get_db_connection()
    material_uso = conn.execute('''
        SELECT mu.*, m.nombre as material_nombre, m.codigo as material_codigo
        FROM material_en_uso mu
        JOIN materiales m ON mu.material_id = m.id
        ORDER BY mu.fecha_instalacion DESC
    ''').fetchall()
    conn.close()

    return jsonify([dict(m) for m in material_uso])

@app.route('/api/material-en-uso', methods=['POST'])
def registrar_material_uso():
    """Registra material en uso"""
    data = request.json

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Verificar stock disponible
        material = cursor.execute('SELECT cantidad_actual FROM materiales WHERE id = ?',
                                 (data['material_id'],)).fetchone()

        if not material:
            return jsonify({'error': 'Material no encontrado'}), 404

        if material['cantidad_actual'] < data['cantidad']:
            return jsonify({'error': 'Stock insuficiente'}), 400

        # Registrar material en uso
        cursor.execute('''
            INSERT INTO material_en_uso (material_id, cantidad, equipo_instalacion,
                                        fecha_instalacion, responsable, observaciones)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['material_id'],
            data['cantidad'],
            data['equipo_instalacion'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            data['responsable'],
            data.get('observaciones', '')
        ))

        # Actualizar cantidad en inventario
        cursor.execute('''
            UPDATE materiales
            SET cantidad_actual = cantidad_actual - ?
            WHERE id = ?
        ''', (data['cantidad'], data['material_id']))

        # Registrar movimiento
        cursor.execute('''
            INSERT INTO movimientos (material_id, tipo_movimiento, cantidad, fecha,
                                    responsable, destino_origen, observaciones)
            VALUES (?, 'EN USO', ?, ?, ?, ?, ?)
        ''', (
            data['material_id'],
            data['cantidad'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            data['responsable'],
            data['equipo_instalacion'],
            data.get('observaciones', '')
        ))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Material en uso registrado exitosamente'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===============================
# API - ESTADÍSTICAS
# ===============================

@app.route('/api/estadisticas', methods=['GET'])
def get_estadisticas():
    """Obtiene estadísticas del inventario"""
    conn = get_db_connection()

    # Total de materiales
    total_materiales = conn.execute('SELECT COUNT(*) as total FROM materiales').fetchone()['total']

    # Materiales con stock bajo
    stock_bajo = conn.execute('''
        SELECT COUNT(*) as total FROM materiales
        WHERE cantidad_actual <= stock_minimo AND cantidad_actual > 0
    ''').fetchone()['total']

    # Materiales sin stock
    sin_stock = conn.execute('''
        SELECT COUNT(*) as total FROM materiales WHERE cantidad_actual = 0
    ''').fetchone()['total']

    # Préstamos activos
    prestamos_activos = conn.execute('''
        SELECT COUNT(*) as total FROM prestamos WHERE estado = 'ACTIVO'
    ''').fetchone()['total']

    # Material en uso
    material_en_uso_total = conn.execute('''
        SELECT COUNT(*) as total FROM material_en_uso
    ''').fetchone()['total']

    # Movimientos del mes
    mes_actual = datetime.now().strftime('%Y-%m')
    movimientos_mes = conn.execute('''
        SELECT COUNT(*) as total FROM movimientos
        WHERE fecha LIKE ?
    ''', (f'{mes_actual}%',)).fetchone()['total']

    # Valor total del inventario
    valor_total = conn.execute('''
        SELECT SUM(cantidad_actual * costo_unitario) as total FROM materiales
    ''').fetchone()['total'] or 0

    conn.close()

    return jsonify({
        'total_materiales': total_materiales,
        'stock_bajo': stock_bajo,
        'sin_stock': sin_stock,
        'prestamos_activos': prestamos_activos,
        'material_en_uso': material_en_uso_total,
        'movimientos_mes': movimientos_mes,
        'valor_total': round(valor_total, 2)
    })

# ===============================
# API - REPORTES
# ===============================

@app.route('/api/reportes/inventario', methods=['GET'])
def reporte_inventario():
    """Genera reporte de inventario completo en Excel"""
    try:
        conn = get_db_connection()
        df = pd.read_sql_query('SELECT * FROM materiales ORDER BY nombre', conn)
        conn.close()

        # Crear archivo Excel en memoria
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Inventario')

        output.seek(0)

        filename = f'inventario_completo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reportes/stock-bajo', methods=['GET'])
def reporte_stock_bajo():
    """Genera reporte de materiales con stock bajo"""
    try:
        conn = get_db_connection()
        df = pd.read_sql_query('''
            SELECT * FROM materiales
            WHERE cantidad_actual <= stock_minimo
            ORDER BY cantidad_actual
        ''', conn)
        conn.close()

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Stock Bajo')

        output.seek(0)

        filename = f'stock_bajo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reportes/movimientos', methods=['GET'])
def reporte_movimientos():
    """Genera reporte de movimientos del mes"""
    try:
        mes_actual = datetime.now().strftime('%Y-%m')

        conn = get_db_connection()
        df = pd.read_sql_query('''
            SELECT m.*, mat.nombre as material_nombre, mat.codigo as material_codigo
            FROM movimientos m
            JOIN materiales mat ON m.material_id = mat.id
            WHERE m.fecha LIKE ?
            ORDER BY m.fecha DESC
        ''', conn, params=(f'{mes_actual}%',))
        conn.close()

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Movimientos')

        output.seek(0)

        filename = f'movimientos_{mes_actual}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("SISTEMA DE INVENTARIO PTAR - VERSIÓN WEB")
    print("=" * 60)
    print(f"\nServidor iniciado exitosamente")
    print(f" URL: http://localhost:5000")
    print(f"Base de datos: {DB_PATH}")
    print(f"\n Presiona Ctrl+C para detener el servidor\n")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5000)
