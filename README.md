# 📦 SISTEMA DE INVENTARIO PTAR

Sistema completo de gestión de inventario para Plantas de Tratamiento de Aguas Residuales (PTAR) desarrollado para operación en Windows.

## 🎯 CARACTERÍSTICAS PRINCIPALES

### 📊 Gestión de Inventario
- **Registro completo de materiales**: código, nombre, descripción, categoría, ubicación
- **Control de stock**: alertas de stock mínimo y material sin existencia
- **Búsqueda avanzada**: filtros por categoría, ubicación y estado
- **Múltiples categorías**: Eléctrico, Mecánico, Químico, Herramientas, Instrumentación, Consumibles, Repuestos, Otros
- **Múltiples ubicaciones**: PTAR I, PTAR II, Almacén General, Estaciones de Bombeo, Taller

### 📥 Entrada de Material
- Registro de entradas con origen y responsable
- Actualización automática de cantidades
- Historial completo de entradas

### 📤 Salida de Material
- Control de salidas con validación de stock disponible
- Registro de destino y responsable
- Verificación de cantidad disponible en tiempo real
- Historial completo de salidas

### 🔄 Control de Préstamos
- Registro de material prestado a otras áreas
- Seguimiento de préstamos activos
- Control de devoluciones
- Actualización automática de inventario

### 🔧 Material en Uso
- Registro de material instalado en equipos
- Seguimiento de material operativo
- Identificación de equipos e instalaciones
- Control de responsables

### 📈 Reportes y Estadísticas
- **Reportes en Excel**:
  - Inventario completo
  - Materiales con stock bajo
  - Movimientos del mes
  - Préstamos activos
  - Material en uso
- **Estadísticas en tiempo real**:
  - Total de materiales
  - Stock bajo y sin stock
  - Préstamos activos
  - Movimientos del mes
  - Valor total del inventario

## 💻 REQUISITOS DEL SISTEMA

- **Sistema Operativo**: Windows 7 o superior
- **Python**: 3.8 o superior
- **Espacio en disco**: 50 MB mínimo
- **RAM**: 2 GB mínimo

## 📥 INSTALACIÓN

### Opción 1: Instalación Automática (Recomendada)

1. Descarga todos los archivos del sistema
2. Haz doble clic en `instalar.bat`
3. Espera a que termine la instalación
4. Listo para usar

### Opción 2: Instalación Manual

1. Abre el símbolo del sistema (CMD)
2. Navega a la carpeta del programa:
   ```
   cd ruta\a\la\carpeta
   ```
3. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

## 🚀 USO DEL SISTEMA

### Iniciar el Programa

**Opción 1**: Haz doble clic en `ejecutar_inventario.bat`

**Opción 2**: Desde el símbolo del sistema:
```
python inventario_ptar.py
```

## 📖 GUÍA DE USO

### 1. Agregar Material Nuevo

1. Ve a la pestaña **"Inventario"**
2. Haz clic en **"Agregar Material"**
3. Completa los campos:
   - Código (único, obligatorio)
   - Nombre (obligatorio)
   - Descripción
   - Categoría
   - Unidad de medida
   - Cantidad inicial
   - Stock mínimo (para alertas)
   - Ubicación
   - Costo unitario
   - Notas adicionales
4. Haz clic en **"Guardar"**

### 2. Registrar Entrada de Material

1. Ve a la pestaña **"Entrada Material"**
2. Selecciona el material del combo
3. Ingresa la cantidad recibida
4. Indica el origen (proveedor, transferencia, etc.)
5. Ingresa el nombre del responsable
6. Agrega observaciones si es necesario
7. Haz clic en **"Registrar Entrada"**

La cantidad se suma automáticamente al inventario actual.

### 3. Registrar Salida de Material

1. Ve a la pestaña **"Salida Material"**
2. Selecciona el material
3. Verifica la cantidad disponible mostrada
4. Ingresa la cantidad a retirar
5. Selecciona el destino (PTAR I, PTAR II, etc.)
6. Ingresa el nombre del responsable
7. Agrega observaciones
8. Haz clic en **"Registrar Salida"**

El sistema valida que haya suficiente stock disponible.

### 4. Gestionar Préstamos

#### Registrar Préstamo:
1. Ve a la pestaña **"Préstamos"**
2. Selecciona el material
3. Ingresa la cantidad
4. Indica a quién se presta
5. Especifica el área o proyecto
6. Agrega observaciones
7. Haz clic en **"Registrar Préstamo"**

#### Registrar Devolución:
1. Selecciona el préstamo en la lista
2. Haz clic en **"Registrar Devolución"**
3. Confirma la operación

El material regresa automáticamente al inventario.

### 5. Registrar Material en Uso

1. Ve a la pestaña **"Material en Uso"**
2. Selecciona el material
3. Ingresa la cantidad instalada
4. Especifica el equipo o instalación
5. Indica el responsable
6. Agrega observaciones
7. Haz clic en **"Registrar Material en Uso"**

Este material sale del inventario disponible pero queda registrado su uso.

### 6. Buscar y Filtrar Material

En la pestaña **"Inventario"**:

- **Búsqueda por texto**: Escribe en el campo de búsqueda para filtrar por código, nombre o descripción
- **Filtro por Categoría**: Selecciona la categoría deseada
- **Filtro por Ubicación**: Selecciona la ubicación
- **Filtro por Estado**: 
  - Stock Normal: material con cantidad > stock mínimo
  - Stock Bajo: material con cantidad ≤ stock mínimo
  - Sin Stock: material con cantidad = 0

### 7. Generar Reportes

1. Ve a la pestaña **"Reportes"**
2. Selecciona el tipo de reporte deseado:
   - Inventario Completo
   - Materiales con Stock Bajo
   - Movimientos del Mes
   - Préstamos Activos
   - Material en Uso
3. Elige la ubicación y nombre del archivo
4. Haz clic en **"Guardar"**

Los reportes se generan en formato Excel (.xlsx) con fecha y hora.

### 8. Ver Estadísticas

1. Ve a la pestaña **"Reportes"**
2. Haz clic en **"Actualizar Estadísticas"**
3. Visualiza:
   - Total de materiales registrados
   - Cantidad de materiales con stock bajo
   - Materiales sin stock
   - Préstamos activos
   - Material en uso
   - Movimientos del mes actual
   - Valor total del inventario

## 📊 CÓDIGOS DE COLOR EN EL INVENTARIO

- **Blanco**: Stock normal (cantidad > stock mínimo)
- **Naranja claro**: Stock bajo (cantidad ≤ stock mínimo)
- **Rosa claro**: Sin stock (cantidad = 0)

## 🗄️ BASE DE DATOS

El sistema utiliza SQLite y crea automáticamente el archivo `inventario_ptar.db` en la carpeta del programa. Este archivo contiene toda la información del inventario.

### Tablas de la Base de Datos:
- **materiales**: Información de cada material
- **movimientos**: Historial de entradas, salidas y préstamos
- **prestamos**: Control de préstamos activos y devueltos
- **material_en_uso**: Material instalado en equipos

### Respaldo de Base de Datos

**IMPORTANTE**: Haz copias de seguridad periódicas del archivo `inventario_ptar.db`

Para hacer respaldo:
1. Cierra el programa
2. Copia el archivo `inventario_ptar.db` a una ubicación segura
3. Nombra el respaldo con la fecha (ej: `inventario_ptar_20240115.db`)

Para restaurar un respaldo:
1. Cierra el programa
2. Reemplaza `inventario_ptar.db` con tu archivo de respaldo
3. Reinicia el programa

## 🔧 SOLUCIÓN DE PROBLEMAS

### El programa no inicia

1. Verifica que Python esté instalado:
   ```
   python --version
   ```
2. Reinstala las dependencias:
   ```
   pip install -r requirements.txt
   ```

### Error "No module named 'customtkinter'"

Ejecuta:
```
pip install customtkinter
```

### La ventana se ve muy pequeña o grande

Puedes modificar el tamaño inicial en el código:
```python
self.root.geometry("1400x800")  # Cambia estos valores
```

### Error al exportar a Excel

Verifica que tengas instalado openpyxl:
```
pip install openpyxl
```

### La base de datos está corrupta

1. Cierra el programa
2. Renombra `inventario_ptar.db` a `inventario_ptar_old.db`
3. Inicia el programa (se creará una base de datos nueva)
4. Si es necesario, contacta a soporte técnico para recuperar datos

## 📝 CATEGORÍAS DE MATERIAL SUGERIDAS

### Eléctrico
- Cables, conectores, breakers, contactores, arrancadores, tableros

### Mecánico
- Rodamientos, sellos, acoples, válvulas, tuberías, conexiones

### Químico
- Coagulantes, polímeros, desinfectantes, reactivos

### Herramientas
- Llaves, desarmadores, multímetros, pinzas, taladros

### Instrumentación
- Sensores, transmisores, controladores, medidores

### Consumibles
- Aceites, grasas, trapos, pegamentos, cintas

### Repuestos
- Piezas específicas de equipos principales

## 🎨 PERSONALIZACIÓN

### Cambiar tema de color

En el código, línea 8:
```python
ctk.set_default_color_theme("blue")  # Opciones: "blue", "green", "dark-blue"
```

### Cambiar modo claro/oscuro

En el código, línea 7:
```python
ctk.set_appearance_mode("light")  # Opciones: "light", "dark", "system"
```

### Agregar más ubicaciones

Modifica las listas de ubicaciones en las líneas correspondientes:
```python
ubicaciones = ["Todas", "PTAR I", "PTAR II", "TU_NUEVA_UBICACION", ...]
```

## 📞 SOPORTE Y ACTUALIZACIONES

Para soporte técnico o sugerencias de mejoras:
- Reporta problemas describiendo el error y los pasos para reproducirlo
- Incluye la versión de Python que estás usando
- Adjunta el archivo `inventario_ptar.db` si es necesario (hacer respaldo primero)

## 📄 NOTAS IMPORTANTES

1. **Haz respaldos regulares** de la base de datos
2. **Capacita al personal** en el uso correcto del sistema
3. **Define un sistema de códigos** para los materiales
4. **Establece responsables** para cada tipo de movimiento
5. **Revisa periódicamente** las alertas de stock bajo
6. **Genera reportes mensuales** para análisis

## 🆕 VERSIÓN

**Versión**: 1.0
**Fecha**: Enero 2025
**Desarrollado para**: PTAR Xalapa, Veracruz

## 📋 PRÓXIMAS MEJORAS SUGERIDAS

- [ ] Gráficas de consumo por material
- [ ] Alertas automáticas por email
- [ ] Código de barras / QR
- [ ] Historial de precios
- [ ] Proveedores preferidos
- [ ] Órdenes de compra
- [ ] Fotografías de materiales
- [ ] Sincronización en red local
- [ ] App móvil para consultas
- [ ] Firma digital en movimientos

---

**Sistema desarrollado específicamente para las necesidades de PTAR**

¡Éxito en la gestión de tu inventario! 🚀
