# 🌐 SISTEMA DE INVENTARIO PTAR - VERSIÓN WEB

Sistema web completo de gestión de inventario para Plantas de Tratamiento de Aguas Residuales (PTAR).

## ✨ CARACTERÍSTICAS

- **Interfaz web moderna y responsive** - Funciona en cualquier navegador y dispositivo
- **Misma base de datos** - Utiliza la base de datos SQLite existente (inventario_ptar.db)
- **Diseño profesional** - Interfaz limpia y fácil de usar
- **Todas las funcionalidades**:
  - Gestión completa de inventario
  - Entrada y salida de materiales
  - Control de préstamos
  - Material en uso
  - Reportes en Excel
  - Estadísticas en tiempo real

## 📋 REQUISITOS

- Python 3.8 o superior
- Navegador web moderno (Chrome, Firefox, Edge, Safari)
- Conexión a red local (opcional, para acceso desde otros dispositivos)

## 🚀 INSTALACIÓN

### Opción 1: Instalación Automática (Recomendada)

1. Haz doble clic en `instalar_web.bat`
2. Espera a que termine la instalación
3. ¡Listo!

### Opción 2: Instalación Manual

```bash
pip install -r requirements_web.txt
```

## ▶️ EJECUTAR LA APLICACIÓN

### Opción 1: Script Automático

1. Haz doble clic en `ejecutar_web.bat`
2. El navegador se abrirá automáticamente
3. La aplicación estará disponible en http://localhost:5000

### Opción 2: Línea de Comandos

```bash
python app.py
```

Luego abre tu navegador en: http://localhost:5000

## 🌍 ACCESO DESDE OTROS DISPOSITIVOS EN LA RED

Para acceder desde otros dispositivos en tu red local:

1. Ejecuta el servidor con `ejecutar_web.bat`
2. Obtén la IP de tu computadora:
   ```bash
   ipconfig
   ```
   Busca la "Dirección IPv4" (ejemplo: 192.168.1.100)

3. Desde otro dispositivo en la misma red, abre:
   ```
   http://192.168.1.100:5000
   ```
   (Reemplaza 192.168.1.100 con tu IP real)

## 📱 USO DE LA APLICACIÓN

### 1. Inventario
- **Ver todos los materiales** con códigos de color según stock
- **Buscar y filtrar** por categoría, ubicación y estado
- **Agregar nuevos materiales** con el botón "Agregar Material"
- **Editar materiales** haciendo clic en el botón de editar
- **Eliminar materiales** con el botón de eliminar

**Códigos de color:**
- **Blanco**: Stock normal
- **Amarillo**: Stock bajo (alerta)
- **Rosa**: Sin stock

### 2. Entrada de Material
- Selecciona el material
- Ingresa cantidad recibida
- Indica el origen (proveedor, transferencia, etc.)
- Especifica el responsable
- Registra la entrada

La cantidad se suma automáticamente al inventario.

### 3. Salida de Material
- Selecciona el material
- El sistema muestra la cantidad disponible
- Ingresa cantidad a retirar
- Selecciona el destino
- Especifica el responsable
- Registra la salida

El sistema valida que haya stock suficiente.

### 4. Préstamos
- Registra material prestado a otras áreas
- Ve préstamos activos en tiempo real
- Registra devoluciones con un solo clic
- El inventario se actualiza automáticamente

### 5. Material en Uso
- Registra material instalado en equipos
- Especifica el equipo/instalación
- Lleva control del responsable
- Ve todo el material operativo

### 6. Reportes
- **Estadísticas en tiempo real**:
  - Total de materiales
  - Stock bajo y sin stock
  - Préstamos activos
  - Material en uso
  - Movimientos del mes
  - Valor total del inventario

- **Reportes en Excel**:
  - Inventario completo
  - Materiales con stock bajo
  - Movimientos del mes

  Los reportes se descargan automáticamente al hacer clic.

## 🗄️ BASE DE DATOS

La aplicación web utiliza la **misma base de datos** que la versión de escritorio:
- Archivo: `inventario_ptar.db`
- Ubicación: Carpeta del programa

**IMPORTANTE:**
- Puedes usar ambas versiones (escritorio y web) alternadamente
- Los datos se sincronizan automáticamente
- Haz respaldos periódicos del archivo `inventario_ptar.db`

### Hacer Respaldo
1. Detén el servidor web
2. Copia `inventario_ptar.db` a ubicación segura
3. Nombra el respaldo con la fecha: `inventario_ptar_2025-01-22.db`

### Restaurar Respaldo
1. Detén el servidor web
2. Reemplaza `inventario_ptar.db` con tu archivo de respaldo
3. Reinicia el servidor

## 🔧 SOLUCIÓN DE PROBLEMAS

### El servidor no inicia

**Problema**: Error "Address already in use"
**Solución**: El puerto 5000 está ocupado. Detén otros procesos o cambia el puerto en `app.py` línea final:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Cambiar 5000 a 5001
```

### Página en blanco o errores

**Problema**: La página no carga correctamente
**Solución**:
1. Verifica que todas las carpetas existan:
   - templates/
   - static/css/
   - static/js/
2. Presiona Ctrl+F5 para recargar sin caché
3. Verifica la consola del navegador (F12) para errores

### No puedo acceder desde otro dispositivo

**Solución**:
1. Verifica que ambos dispositivos estén en la misma red
2. Desactiva temporalmente el firewall de Windows
3. Asegúrate de usar la IP correcta

### Error al instalar dependencias

**Solución**:
```bash
python -m pip install --upgrade pip
pip install -r requirements_web.txt --force-reinstall
```

## 🎨 PERSONALIZACIÓN

### Cambiar colores del tema

Edita `static/css/styles.css` líneas 1-15 para cambiar la paleta de colores:

```css
:root {
    --primary: #2563eb;      /* Color principal */
    --success: #10b981;      /* Color de éxito */
    --warning: #f59e0b;      /* Color de advertencia */
    --danger: #ef4444;       /* Color de peligro */
}
```

### Cambiar puerto del servidor

Edita `app.py` última línea:
```python
app.run(debug=True, host='0.0.0.0', port=8080)  # Cambiar puerto
```

### Agregar más categorías o ubicaciones

Edita tanto `templates/index.html` como las opciones en los select de categorías y ubicaciones.

## 🔒 SEGURIDAD

**IMPORTANTE**: Este servidor está diseñado para uso en red local. Para producción:

1. Desactiva el modo debug en `app.py`:
   ```python
   app.run(debug=False, host='0.0.0.0', port=5000)
   ```

2. Usa un servidor WSGI de producción (Gunicorn, uWSGI)

3. Implementa autenticación de usuarios

4. Usa HTTPS

## 📞 VENTAJAS DE LA VERSIÓN WEB

✅ **Acceso desde cualquier dispositivo** (PC, tablet, móvil)
✅ **Sin instalación en cada equipo** - Solo necesitas el navegador
✅ **Interfaz moderna y responsive**
✅ **Múltiples usuarios simultáneos**
✅ **Acceso desde cualquier lugar de la red**
✅ **Misma base de datos** - Compatible con versión de escritorio
✅ **Actualizaciones centralizadas**

## 🆚 COMPARACIÓN DE VERSIONES

| Característica | Versión Escritorio | Versión Web |
|---------------|-------------------|-------------|
| Interfaz | CustomTkinter | HTML/CSS/JS |
| Acceso | Solo PC local | Cualquier dispositivo en red |
| Instalación | En cada PC | Solo en servidor |
| Base de datos | SQLite | SQLite (misma) |
| Reportes Excel | ✅ | ✅ |
| Todas las funciones | ✅ | ✅ |
| Uso simultáneo | ❌ | ✅ |

## 📄 ARCHIVOS INCLUIDOS

```
inventario_ptar.db          # Base de datos SQLite
app.py                      # Servidor Flask (backend)
templates/
  └── index.html            # Interfaz web (frontend)
static/
  ├── css/
  │   └── styles.css        # Estilos profesionales
  └── js/
      └── app.js            # Lógica JavaScript
requirements_web.txt        # Dependencias Python
ejecutar_web.bat           # Script de ejecución
instalar_web.bat           # Script de instalación
README_WEB.md              # Este archivo
```

## 🎯 PRÓXIMAS MEJORAS SUGERIDAS

- [ ] Sistema de usuarios y permisos
- [ ] Autenticación con login/password
- [ ] Gráficas de consumo
- [ ] Notificaciones automáticas
- [ ] Código de barras / QR
- [ ] API REST para integración
- [ ] App móvil nativa
- [ ] Sincronización en la nube

---

**¡Disfruta de tu sistema de inventario web! 🚀**

Para soporte o sugerencias, contacta al equipo de TI.
