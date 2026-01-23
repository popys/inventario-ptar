// ================================
// VARIABLES GLOBALES
// ================================
let materialesData = [];
let editandoMaterialId = null;

// ================================
// INICIALIZACIÓN
// ================================
document.addEventListener('DOMContentLoaded', function() {
    inicializarEventos();
    cargarDatosIniciales();
});

function inicializarEventos() {
    // Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            cambiarTab(this.dataset.tab);
        });
    });

    // Filtros de inventario
    document.getElementById('searchInput')?.addEventListener('input', filtrarInventario);
    document.getElementById('filterCategoria')?.addEventListener('change', filtrarInventario);
    document.getElementById('filterUbicacion')?.addEventListener('change', filtrarInventario);
    document.getElementById('filterEstado')?.addEventListener('change', filtrarInventario);

    // Forms
    document.getElementById('formMaterial')?.addEventListener('submit', guardarMaterial);
    document.getElementById('formEntrada')?.addEventListener('submit', registrarEntrada);
    document.getElementById('formSalida')?.addEventListener('submit', registrarSalida);
    document.getElementById('formPrestamo')?.addEventListener('submit', registrarPrestamo);
    document.getElementById('formEnUso')?.addEventListener('submit', registrarEnUso);

    // Preview de imagen
    document.getElementById('materialImagen')?.addEventListener('change', previsualizarImagen);

    // Selects de material con info de disponibilidad
    document.getElementById('salidaMaterialId')?.addEventListener('change', mostrarDisponible('salida'));
    document.getElementById('prestamoMaterialId')?.addEventListener('change', mostrarDisponible('prestamo'));
    document.getElementById('enUsoMaterialId')?.addEventListener('change', mostrarDisponible('enUso'));

    // Cerrar modal al hacer click fuera
    document.getElementById('modalMaterial')?.addEventListener('click', function(e) {
        if (e.target === this) cerrarModal();
    });
}

function cargarDatosIniciales() {
    cargarMateriales();
    actualizarEstadisticas();
    cargarMovimientos();
    cargarPrestamos();
    cargarMaterialEnUso();
    cargarSelectsMaterial();
}

// ================================
// NAVEGACIÓN TABS
// ================================
function cambiarTab(tabName) {
    // Cambiar botón activo
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Cambiar contenido activo
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabName).classList.add('active');

    // Cargar datos específicos del tab
    if (tabName === 'reportes') {
        actualizarEstadisticas();
    }
}

// ================================
// API - MATERIALES
// ================================
async function cargarMateriales() {
    try {
        const params = new URLSearchParams({
            categoria: document.getElementById('filterCategoria')?.value || '',
            ubicacion: document.getElementById('filterUbicacion')?.value || '',
            estado: document.getElementById('filterEstado')?.value || '',
            busqueda: document.getElementById('searchInput')?.value || ''
        });

        const response = await fetch(`/api/materiales?${params}`);
        materialesData = await response.json();

        renderizarInventario();
        actualizarHeaderStats();
    } catch (error) {
        mostrarToast('Error al cargar materiales', 'error');
        console.error(error);
    }
}

function renderizarInventario() {
    const tbody = document.getElementById('inventarioTableBody');

    if (materialesData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center">No se encontraron materiales</td></tr>';
        return;
    }

    tbody.innerHTML = materialesData.map(m => `
        <tr class="${m.estado_clase}" data-material-id="${m.id}" data-imagen="${m.imagen_ruta || ''}" style="cursor: ${m.imagen_ruta ? 'pointer' : 'default'};" title="${m.imagen_ruta ? 'Click para ver imagen' : 'Sin imagen'}">
            <td><strong>${m.codigo}</strong></td>
            <td>
                ${m.imagen_ruta ? '<i class="fas fa-image" style="color: #4CAF50; margin-right: 5px;"></i>' : ''}
                ${m.nombre}
            </td>
            <td>${m.descripcion || '-'}</td>
            <td><span class="badge">${m.categoria || '-'}</span></td>
            <td>${m.ubicacion || '-'}</td>
            <td><strong>${m.cantidad_actual}</strong></td>
            <td>${m.unidad || '-'}</td>
            <td>${m.stock_minimo}</td>
            <td>$${parseFloat(m.costo_unitario || 0).toFixed(2)}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="editarMaterial(${m.id}); event.stopPropagation();">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="eliminarMaterial(${m.id}, '${m.nombre}'); event.stopPropagation();">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');

    // Agregar eventos de click a las filas
    tbody.querySelectorAll('tr[data-material-id]').forEach(row => {
        row.addEventListener('click', function(e) {
            // No abrir imagen si se hace click en botones
            if (e.target.closest('button')) return;

            const imagenRuta = this.dataset.imagen;
            const materialId = this.dataset.materialId;

            if (imagenRuta) {
                const material = materialesData.find(m => m.id == materialId);
                mostrarModalImagen(imagenRuta, material);
            }
        });
    });
}

function filtrarInventario() {
    cargarMateriales();
}

function actualizarHeaderStats() {
    const total = materialesData.length;
    const stockBajo = materialesData.filter(m => m.cantidad_actual <= m.stock_minimo && m.cantidad_actual > 0).length;
    const sinStock = materialesData.filter(m => m.cantidad_actual === 0).length;

    document.getElementById('totalMateriales').textContent = total;
    document.getElementById('stockBajo').textContent = stockBajo;
    document.getElementById('sinStock').textContent = sinStock;
}

// ================================
// MODAL - AGREGAR/EDITAR MATERIAL
// ================================
function mostrarModalAgregar() {
    editandoMaterialId = null;
    document.getElementById('modalTitle').innerHTML = '<i class="fas fa-plus"></i> Agregar Material';
    document.getElementById('formMaterial').reset();
    document.getElementById('materialId').value = '';
    document.getElementById('materialImagenRuta').value = '';
    document.getElementById('imagenPreview').innerHTML = '';
    document.getElementById('modalMaterial').classList.add('active');
}

function cerrarModal() {
    document.getElementById('modalMaterial').classList.remove('active');
    document.getElementById('imagenPreview').innerHTML = '';
    editandoMaterialId = null;
}

async function editarMaterial(id) {
    try {
        const response = await fetch(`/api/materiales/${id}`);
        const material = await response.json();

        editandoMaterialId = id;
        document.getElementById('modalTitle').innerHTML = '<i class="fas fa-edit"></i> Editar Material';

        document.getElementById('materialId').value = material.id;
        document.getElementById('materialCodigo').value = material.codigo;
        document.getElementById('materialNombre').value = material.nombre;
        document.getElementById('materialDescripcion').value = material.descripcion || '';
        document.getElementById('materialCategoria').value = material.categoria || '';
        document.getElementById('materialUnidad').value = material.unidad || '';
        document.getElementById('materialCantidad').value = material.cantidad_actual || 0;
        document.getElementById('materialStockMinimo').value = material.stock_minimo || 0;
        document.getElementById('materialUbicacion').value = material.ubicacion || '';
        document.getElementById('materialCosto').value = material.costo_unitario || 0;
        document.getElementById('materialNotas').value = material.notas || '';
        document.getElementById('materialImagenRuta').value = material.imagen_ruta || '';

        // Mostrar imagen actual si existe
        const previewDiv = document.getElementById('imagenPreview');
        if (material.imagen_ruta) {
            previewDiv.innerHTML = `
                <div style="margin-top: 10px;">
                    <p style="color: #666; margin-bottom: 5px;">Imagen actual:</p>
                    <img src="/imagenes_materiales/${material.imagen_ruta}" alt="Imagen actual" style="max-width: 200px; max-height: 200px; border-radius: 4px; border: 2px solid #ddd;">
                    <p style="color: #666; font-size: 0.85em; margin-top: 5px;">Suba una nueva imagen para reemplazarla</p>
                </div>
            `;
        } else {
            previewDiv.innerHTML = '';
        }

        // Deshabilitar campo cantidad al editar
        document.getElementById('materialCantidad').disabled = true;

        document.getElementById('modalMaterial').classList.add('active');
    } catch (error) {
        mostrarToast('Error al cargar material', 'error');
        console.error(error);
    }
}

async function guardarMaterial(e) {
    e.preventDefault();

    const id = editandoMaterialId;
    let imagenRuta = document.getElementById('materialImagenRuta').value;

    // Subir imagen si se seleccionó una nueva
    const imagenInput = document.getElementById('materialImagen');
    if (imagenInput.files && imagenInput.files[0]) {
        try {
            mostrarToast('Subiendo imagen...', 'info');
            const formData = new FormData();
            formData.append('imagen', imagenInput.files[0]);

            const uploadResponse = await fetch('/api/upload-imagen', {
                method: 'POST',
                body: formData
            });

            const uploadResult = await uploadResponse.json();

            if (uploadResponse.ok) {
                imagenRuta = uploadResult.imagen_ruta;
            } else {
                mostrarToast(uploadResult.error, 'error');
                return;
            }
        } catch (error) {
            mostrarToast('Error al subir imagen', 'error');
            console.error(error);
            return;
        }
    }

    const data = {
        codigo: document.getElementById('materialCodigo').value,
        nombre: document.getElementById('materialNombre').value,
        descripcion: document.getElementById('materialDescripcion').value,
        categoria: document.getElementById('materialCategoria').value,
        unidad: document.getElementById('materialUnidad').value,
        stock_minimo: parseFloat(document.getElementById('materialStockMinimo').value) || 0,
        ubicacion: document.getElementById('materialUbicacion').value,
        costo_unitario: parseFloat(document.getElementById('materialCosto').value) || 0,
        notas: document.getElementById('materialNotas').value,
        imagen_ruta: imagenRuta
    };

    // Solo incluir cantidad_actual al crear nuevo
    if (!id) {
        data.cantidad_actual = parseFloat(document.getElementById('materialCantidad').value) || 0;
    }

    try {
        const url = id ? `/api/materiales/${id}` : '/api/materiales';
        const method = id ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            mostrarToast(result.message, 'success');
            cerrarModal();
            cargarMateriales();
            cargarSelectsMaterial();
            document.getElementById('materialCantidad').disabled = false;
        } else {
            mostrarToast(result.error, 'error');
        }
    } catch (error) {
        mostrarToast('Error al guardar material', 'error');
        console.error(error);
    }
}

async function eliminarMaterial(id, nombre) {
    if (!confirm(`¿Está seguro de eliminar el material "${nombre}"?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/materiales/${id}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (response.ok) {
            mostrarToast(result.message, 'success');
            cargarMateriales();
            cargarSelectsMaterial();
        } else {
            mostrarToast(result.error, 'error');
        }
    } catch (error) {
        mostrarToast('Error al eliminar material', 'error');
        console.error(error);
    }
}

// ================================
// CARGAR SELECTS DE MATERIAL
// ================================
async function cargarSelectsMaterial() {
    try {
        const response = await fetch('/api/materiales');
        const materiales = await response.json();

        const selects = [
            'entradaMaterialId',
            'salidaMaterialId',
            'prestamoMaterialId',
            'enUsoMaterialId'
        ];

        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                select.innerHTML = '<option value="">Seleccione un material...</option>' +
                    materiales.map(m =>
                        `<option value="${m.id}">${m.codigo} - ${m.nombre} (Disponible: ${m.cantidad_actual} ${m.unidad || ''})</option>`
                    ).join('');
            }
        });
    } catch (error) {
        console.error('Error al cargar selects:', error);
    }
}

function mostrarDisponible(tipo) {
    return async function(e) {
        const materialId = e.target.value;
        const displayId = `${tipo}Disponible`;

        if (!materialId) {
            document.getElementById(displayId).textContent = '';
            return;
        }

        try {
            const response = await fetch(`/api/materiales/${materialId}`);
            const material = await response.json();

            document.getElementById(displayId).textContent =
                `Disponible: ${material.cantidad_actual} ${material.unidad || ''}`;
        } catch (error) {
            console.error('Error al obtener disponibilidad:', error);
        }
    };
}

// ================================
// ENTRADA DE MATERIAL
// ================================
async function registrarEntrada(e) {
    e.preventDefault();

    const data = {
        material_id: parseInt(document.getElementById('entradaMaterialId').value),
        cantidad: parseFloat(document.getElementById('entradaCantidad').value),
        origen: document.getElementById('entradaOrigen').value,
        responsable: document.getElementById('entradaResponsable').value,
        observaciones: document.getElementById('entradaObservaciones').value
    };

    try {
        const response = await fetch('/api/movimientos/entrada', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            mostrarToast(result.message, 'success');
            document.getElementById('formEntrada').reset();
            cargarMateriales();
            cargarMovimientos('ENTRADA', 'entradasTableBody');
            actualizarEstadisticas();
        } else {
            mostrarToast(result.error, 'error');
        }
    } catch (error) {
        mostrarToast('Error al registrar entrada', 'error');
        console.error(error);
    }
}

// ================================
// SALIDA DE MATERIAL
// ================================
async function registrarSalida(e) {
    e.preventDefault();

    const data = {
        material_id: parseInt(document.getElementById('salidaMaterialId').value),
        cantidad: parseFloat(document.getElementById('salidaCantidad').value),
        destino: document.getElementById('salidaDestino').value,
        responsable: document.getElementById('salidaResponsable').value,
        observaciones: document.getElementById('salidaObservaciones').value
    };

    try {
        const response = await fetch('/api/movimientos/salida', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            mostrarToast(result.message, 'success');
            document.getElementById('formSalida').reset();
            document.getElementById('salidaDisponible').textContent = '';
            cargarMateriales();
            cargarMovimientos('SALIDA', 'salidasTableBody');
            actualizarEstadisticas();
        } else {
            mostrarToast(result.error, 'error');
        }
    } catch (error) {
        mostrarToast('Error al registrar salida', 'error');
        console.error(error);
    }
}

// ================================
// PRÉSTAMOS
// ================================
async function registrarPrestamo(e) {
    e.preventDefault();

    const data = {
        material_id: parseInt(document.getElementById('prestamoMaterialId').value),
        cantidad: parseFloat(document.getElementById('prestamoCantidad').value),
        prestado_a: document.getElementById('prestamoPrestadoA').value,
        area_destino: document.getElementById('prestamoArea').value,
        observaciones: document.getElementById('prestamoObservaciones').value
    };

    try {
        const response = await fetch('/api/prestamos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            mostrarToast(result.message, 'success');
            document.getElementById('formPrestamo').reset();
            document.getElementById('prestamoDisponible').textContent = '';
            cargarMateriales();
            cargarPrestamos();
            actualizarEstadisticas();
        } else {
            mostrarToast(result.error, 'error');
        }
    } catch (error) {
        mostrarToast('Error al registrar préstamo', 'error');
        console.error(error);
    }
}

async function cargarPrestamos() {
    try {
        const response = await fetch('/api/prestamos');
        const prestamos = await response.json();

        const tbody = document.getElementById('prestamosTableBody');

        if (prestamos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No hay préstamos activos</td></tr>';
            return;
        }

        tbody.innerHTML = prestamos.map(p => `
            <tr>
                <td>${formatearFecha(p.fecha_prestamo)}</td>
                <td>${p.material_codigo} - ${p.material_nombre}</td>
                <td>${p.cantidad}</td>
                <td>${p.prestado_a}</td>
                <td>${p.area_destino}</td>
                <td>
                    <button class="btn btn-sm btn-success" onclick="devolverPrestamo(${p.id})">
                        <i class="fas fa-undo"></i> Devolver
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error al cargar préstamos:', error);
    }
}

async function devolverPrestamo(id) {
    if (!confirm('¿Confirmar devolución de este préstamo?')) {
        return;
    }

    try {
        const response = await fetch(`/api/prestamos/${id}/devolver`, {
            method: 'POST'
        });

        const result = await response.json();

        if (response.ok) {
            mostrarToast(result.message, 'success');
            cargarMateriales();
            cargarPrestamos();
            actualizarEstadisticas();
        } else {
            mostrarToast(result.error, 'error');
        }
    } catch (error) {
        mostrarToast('Error al devolver préstamo', 'error');
        console.error(error);
    }
}

// ================================
// MATERIAL EN USO
// ================================
async function registrarEnUso(e) {
    e.preventDefault();

    const data = {
        material_id: parseInt(document.getElementById('enUsoMaterialId').value),
        cantidad: parseFloat(document.getElementById('enUsoCantidad').value),
        equipo_instalacion: document.getElementById('enUsoEquipo').value,
        responsable: document.getElementById('enUsoResponsable').value,
        observaciones: document.getElementById('enUsoObservaciones').value
    };

    try {
        const response = await fetch('/api/material-en-uso', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            mostrarToast(result.message, 'success');
            document.getElementById('formEnUso').reset();
            document.getElementById('enUsoDisponible').textContent = '';
            cargarMateriales();
            cargarMaterialEnUso();
            actualizarEstadisticas();
        } else {
            mostrarToast(result.error, 'error');
        }
    } catch (error) {
        mostrarToast('Error al registrar material en uso', 'error');
        console.error(error);
    }
}

async function cargarMaterialEnUso() {
    try {
        const response = await fetch('/api/material-en-uso');
        const materiales = await response.json();

        const tbody = document.getElementById('enUsoTableBody');

        if (materiales.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">No hay material en uso registrado</td></tr>';
            return;
        }

        tbody.innerHTML = materiales.map(m => `
            <tr>
                <td>${formatearFecha(m.fecha_instalacion)}</td>
                <td>${m.material_codigo} - ${m.material_nombre}</td>
                <td>${m.cantidad}</td>
                <td>${m.equipo_instalacion}</td>
                <td>${m.responsable}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error al cargar material en uso:', error);
    }
}

// ================================
// MOVIMIENTOS
// ================================
async function cargarMovimientos(tipo = '', tbodyId = '') {
    try {
        const url = tipo ? `/api/movimientos?tipo=${tipo}` : '/api/movimientos';
        const response = await fetch(url);
        const movimientos = await response.json();

        // Si se especifica un tbody específico, renderizar solo ahí
        if (tbodyId) {
            const tbody = document.getElementById(tbodyId);
            if (tbody) {
                if (movimientos.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" class="text-center">No hay movimientos registrados</td></tr>';
                } else {
                    tbody.innerHTML = movimientos.slice(0, 10).map(m => `
                        <tr>
                            <td>${formatearFecha(m.fecha)}</td>
                            <td>${m.material_codigo} - ${m.material_nombre}</td>
                            <td>${m.cantidad}</td>
                            <td>${m.destino_origen}</td>
                            <td>${m.responsable}</td>
                        </tr>
                    `).join('');
                }
            }
        }
    } catch (error) {
        console.error('Error al cargar movimientos:', error);
    }
}

// ================================
// ESTADÍSTICAS
// ================================
async function actualizarEstadisticas() {
    try {
        const response = await fetch('/api/estadisticas');
        const stats = await response.json();

        document.getElementById('statTotalMateriales').textContent = stats.total_materiales;
        document.getElementById('statStockBajo').textContent = stats.stock_bajo;
        document.getElementById('statSinStock').textContent = stats.sin_stock;
        document.getElementById('statPrestamosActivos').textContent = stats.prestamos_activos;
        document.getElementById('statMaterialEnUso').textContent = stats.material_en_uso;
        document.getElementById('statMovimientosMes').textContent = stats.movimientos_mes;
        document.getElementById('statValorTotal').textContent = `$${stats.valor_total.toLocaleString('es-MX', {minimumFractionDigits: 2})}`;
    } catch (error) {
        console.error('Error al actualizar estadísticas:', error);
    }
}

// ================================
// REPORTES
// ================================
async function descargarReporte(tipo) {
    const urls = {
        'inventario': '/api/reportes/inventario',
        'stock-bajo': '/api/reportes/stock-bajo',
        'movimientos': '/api/reportes/movimientos'
    };

    const url = urls[tipo];
    if (!url) return;

    try {
        mostrarToast('Generando reporte...', 'info');

        // Realizar la petición al servidor
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error('Error al generar el reporte');
        }

        // Obtener el blob (archivo binario)
        const blob = await response.blob();

        // Obtener el nombre del archivo desde los headers o generar uno
        const contentDisposition = response.headers.get('content-disposition');
        let filename = 'reporte.xlsx';

        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
            if (filenameMatch && filenameMatch[1]) {
                filename = filenameMatch[1].replace(/['"]/g, '');
            }
        }

        // Crear un enlace temporal y forzar la descarga
        const blobUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = blobUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();

        // Limpiar
        document.body.removeChild(link);
        window.URL.revokeObjectURL(blobUrl);

        mostrarToast('Reporte descargado exitosamente', 'success');
    } catch (error) {
        mostrarToast('Error al descargar el reporte', 'error');
        console.error('Error:', error);
    }
}

// ================================
// UTILIDADES
// ================================
function formatearFecha(fechaStr) {
    if (!fechaStr) return '-';
    const fecha = new Date(fechaStr);
    return fecha.toLocaleString('es-MX', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function mostrarToast(mensaje, tipo = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = mensaje;
    toast.className = `toast ${tipo} show`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// ================================
// IMÁGENES
// ================================
function previsualizarImagen(e) {
    const file = e.target.files[0];
    const previewDiv = document.getElementById('imagenPreview');

    if (file) {
        // Validar tamaño (16MB)
        if (file.size > 16 * 1024 * 1024) {
            mostrarToast('La imagen es demasiado grande. Máximo 16MB', 'error');
            e.target.value = '';
            previewDiv.innerHTML = '';
            return;
        }

        // Validar tipo
        const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
        if (!validTypes.includes(file.type)) {
            mostrarToast('Formato no válido. Use PNG, JPG, JPEG, GIF o WEBP', 'error');
            e.target.value = '';
            previewDiv.innerHTML = '';
            return;
        }

        // Mostrar preview
        const reader = new FileReader();
        reader.onload = function(event) {
            previewDiv.innerHTML = `
                <div style="margin-top: 10px;">
                    <p style="color: #666; margin-bottom: 5px;">Vista previa:</p>
                    <img src="${event.target.result}" alt="Preview" style="max-width: 200px; max-height: 200px; border-radius: 4px; border: 2px solid #4CAF50;">
                    <p style="color: #666; font-size: 0.85em; margin-top: 5px;">${file.name} (${(file.size / 1024).toFixed(2)} KB)</p>
                </div>
            `;
        };
        reader.readAsDataURL(file);
    } else {
        previewDiv.innerHTML = '';
    }
}

function mostrarModalImagen(imagenRuta, material) {
    const modal = document.getElementById('modalImagen');
    const img = document.getElementById('modalImagenImg');
    const title = document.getElementById('modalImagenTitle');
    const info = document.getElementById('modalImagenInfo');

    img.src = `/imagenes_materiales/${imagenRuta}`;
    title.innerHTML = `<i class="fas fa-image"></i> ${material.nombre}`;
    info.textContent = `Código: ${material.codigo} | Categoría: ${material.categoria || 'N/A'} | Ubicación: ${material.ubicacion || 'N/A'}`;

    modal.classList.add('active');
}

function cerrarModalImagen() {
    const modal = document.getElementById('modalImagen');
    modal.classList.remove('active');
}

// Cerrar modal de imagen al hacer click fuera
document.getElementById('modalImagen')?.addEventListener('click', function(e) {
    if (e.target === this) cerrarModalImagen();
});

// Cerrar modal de imagen con tecla Escape
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        cerrarModalImagen();
    }
});

// Cargar movimientos cuando se cambia a esas pestañas
document.addEventListener('DOMContentLoaded', function() {
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.target.classList.contains('active')) {
                const tabId = mutation.target.id;
                if (tabId === 'entrada') {
                    cargarMovimientos('ENTRADA', 'entradasTableBody');
                } else if (tabId === 'salida') {
                    cargarMovimientos('SALIDA', 'salidasTableBody');
                }
            }
        });
    });

    document.querySelectorAll('.tab-content').forEach(tab => {
        observer.observe(tab, { attributes: true, attributeFilter: ['class'] });
    });
});
