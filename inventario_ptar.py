import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
import os
import pandas as pd
from PIL import Image, ImageTk
import shutil

# Configuración de CustomTkinter
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class AutocompleteEntry(ctk.CTkFrame):
    """Widget de entrada con autocompletado para materiales"""
    
    def __init__(self, master, items=None, on_select_callback=None, **kwargs):
        super().__init__(master, fg_color="transparent")
        
        self.items = items or []
        self.filtered_items = []
        self.width = kwargs.pop('width', 400)
        self.on_select_callback = on_select_callback
        
        # Entry principal
        self.entry = ctk.CTkEntry(self, width=self.width, **kwargs)
        self.entry.pack(fill="x")
        
        # Frame para la lista desplegable
        self.listbox_frame = ctk.CTkFrame(self, fg_color="white", border_width=1, 
                                         border_color="gray")
        
        # Listbox para sugerencias
        self.listbox = None
        
        # Bindings
        self.entry.bind('<KeyRelease>', self.on_keyrelease)
        self.entry.bind('<FocusOut>', self.on_focus_out)
        
        # Variable para almacenar selección
        self.selection = None
        
    def on_keyrelease(self, event):
        """Filtra items mientras el usuario escribe"""
        
        # Ignorar teclas especiales
        if event.keysym in ('Up', 'Down', 'Return', 'Tab', 'Escape'):
            return
        
        text = self.entry.get()
        
        if not text:
            self.hide_listbox()
            return
        
        # Filtrar items
        text_lower = text.lower()
        self.filtered_items = [item for item in self.items 
                              if text_lower in item.lower()]
        
        if self.filtered_items:
            self.show_listbox()
        else:
            self.hide_listbox()
    
    def show_listbox(self):
        """Muestra la lista de sugerencias"""
        
        # Limpiar listbox anterior si existe
        if self.listbox:
            self.listbox.destroy()
        
        # Crear nuevo listbox
        self.listbox_frame.pack(fill="x", pady=(2, 0))
        
        # Scrollbar
        scrollbar = ctk.CTkScrollbar(self.listbox_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Listbox con tkinter nativo para mejor control
        from tkinter import Listbox
        self.listbox = Listbox(self.listbox_frame, 
                              height=min(8, len(self.filtered_items)),
                              yscrollcommand=scrollbar.set,
                              font=("Arial", 11))
        self.listbox.pack(fill="both", expand=True)
        
        scrollbar.configure(command=self.listbox.yview)
        
        # Llenar con items filtrados
        for item in self.filtered_items:
            self.listbox.insert("end", item)
        
        # Bindings
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        self.listbox.bind('<Double-Button-1>', self.on_select)
        
        # Bindings del entry para navegar con flechas
        self.entry.bind('<Down>', lambda e: self.listbox.focus_set() 
                       if self.listbox else None)
        
    def hide_listbox(self):
        """Oculta la lista de sugerencias"""
        if self.listbox:
            self.listbox.destroy()
            self.listbox = None
        self.listbox_frame.pack_forget()
    
    def on_select(self, event):
        """Cuando se selecciona un item de la lista"""
        if self.listbox:
            selection = self.listbox.curselection()
            if selection:
                selected_text = self.listbox.get(selection[0])
                self.entry.delete(0, 'end')
                self.entry.insert(0, selected_text)
                self.selection = selected_text
                self.hide_listbox()
                self.entry.focus_set()
                
                # Llamar al callback si existe
                if self.on_select_callback:
                    self.on_select_callback()
    
    def on_focus_out(self, event):
        """Cuando pierde el foco, ocultar listbox después de un delay"""
        # Delay para permitir clic en listbox
        self.after(200, self.hide_listbox)
    
    def get(self):
        """Obtiene el texto actual"""
        return self.entry.get()
    
    def delete(self, first, last):
        """Limpia el entry"""
        self.entry.delete(first, last)
    
    def insert(self, index, text):
        """Inserta texto"""
        self.entry.insert(index, text)
    
    def set_items(self, items):
        """Actualiza la lista de items disponibles"""
        self.items = items or []

class InventarioPTAR:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Inventario PTAR - Xalapa, Ver.")
        self.root.geometry("1400x800")
        
        # Inicializar base de datos
        self.init_database()
        
        # Crear directorio para imágenes
        self.imagenes_dir = "imagenes_materiales"
        if not os.path.exists(self.imagenes_dir):
            os.makedirs(self.imagenes_dir)
        
        # Variables
        self.busqueda_var = ctk.StringVar()
        self.filtro_categoria = ctk.StringVar(value="Todas")
        self.filtro_ubicacion = ctk.StringVar(value="Todas")
        self.filtro_estado = ctk.StringVar(value="Todos")

        # Variables de búsqueda para otros módulos
        self.busqueda_entrada_var = ctk.StringVar()
        self.busqueda_salida_var = ctk.StringVar()
        self.busqueda_prestamo_var = ctk.StringVar()
        self.filtro_estado_prestamo = ctk.StringVar(value="Todos")
        self.busqueda_uso_var = ctk.StringVar()
        
        # Crear interfaz
        self.crear_interfaz()
        self.cargar_datos()

        # Cargar datos iniciales en cada tab
        self.filtrar_materiales_entrada()
        self.filtrar_materiales_salida()
        self.filtrar_materiales_prestamo()
        self.filtrar_materiales_uso()
        self.cargar_historial_entradas()
        self.cargar_historial_salidas()
        self.cargar_prestamos()
        self.cargar_material_en_uso()
        
    def init_database(self):
        """Inicializa la base de datos SQLite"""
        self.conn = sqlite3.connect('inventario_ptar.db')
        self.cursor = self.conn.cursor()
        
        # Tabla de materiales
        self.cursor.execute('''
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
                fecha_registro TEXT,
                notas TEXT,
                imagen_ruta TEXT
            )
        ''')
        
        # Verificar si la columna imagen_ruta existe, si no, agregarla
        self.cursor.execute("PRAGMA table_info(materiales)")
        columnas = [columna[1] for columna in self.cursor.fetchall()]
        if 'imagen_ruta' not in columnas:
            self.cursor.execute("ALTER TABLE materiales ADD COLUMN imagen_ruta TEXT")
        
        # Tabla de movimientos
        self.cursor.execute('''
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
        self.cursor.execute('''
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
        self.cursor.execute('''
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
        
        self.conn.commit()
        
    def crear_interfaz(self):
        """Crea la interfaz gráfica principal"""
        
        # Frame principal con pestañas
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Pestañas
        self.tab_inventario = self.tabview.add("Inventario")
        self.tab_entrada = self.tabview.add("Entrada Material")
        self.tab_salida = self.tabview.add("Salida Material")
        self.tab_prestamos = self.tabview.add("Préstamos")
        self.tab_en_uso = self.tabview.add("Material en Uso")
        self.tab_reportes = self.tabview.add("Reportes")
        
        self.crear_tab_inventario()
        self.crear_tab_entrada()
        self.crear_tab_salida()
        self.crear_tab_prestamos()
        self.crear_tab_en_uso()
        self.crear_tab_reportes()
        
    def crear_tab_inventario(self):
        """Crea la pestaña de inventario"""
        
        # Frame superior - Búsqueda y filtros
        frame_busqueda = ctk.CTkFrame(self.tab_inventario)
        frame_busqueda.pack(fill="x", padx=10, pady=10)
        
        # Búsqueda
        ctk.CTkLabel(frame_busqueda, text="Buscar:").grid(row=0, column=0, padx=5, pady=5)
        entry_busqueda = ctk.CTkEntry(frame_busqueda, textvariable=self.busqueda_var, width=300)
        entry_busqueda.grid(row=0, column=1, padx=5, pady=5)
        entry_busqueda.bind('<KeyRelease>', lambda e: self.cargar_datos())
        
        # Filtro Categoría
        ctk.CTkLabel(frame_busqueda, text="Categoría:").grid(row=0, column=2, padx=5, pady=5)
        categorias = ["Todas", "Fontanería y Ferretería", "Herramientas y Equipos", 
                     "Seguridad", "Limpieza", "Papelería"]
        combo_categoria = ctk.CTkComboBox(frame_busqueda, values=categorias, 
                                         variable=self.filtro_categoria,
                                         command=lambda e: self.cargar_datos())
        combo_categoria.grid(row=0, column=3, padx=5, pady=5)
        
        # Filtro Estado
        ctk.CTkLabel(frame_busqueda, text="Estado:").grid(row=0, column=4, padx=5, pady=5)
        estados = ["Todos", "Stock Normal", "Stock Bajo", "Sin Stock"]
        combo_estado = ctk.CTkComboBox(frame_busqueda, values=estados,
                                      variable=self.filtro_estado,
                                      command=lambda e: self.cargar_datos())
        combo_estado.grid(row=0, column=5, padx=5, pady=5)
        
        # Botones
        ctk.CTkButton(frame_busqueda, text="Agregar Material", 
                     command=self.agregar_material).grid(row=1, column=2, padx=5, pady=5)
        ctk.CTkButton(frame_busqueda, text="Ver Imagen", 
                     command=self.ver_imagen_material).grid(row=1, column=3, padx=5, pady=5)
        ctk.CTkButton(frame_busqueda, text="Editar", 
                     command=self.editar_material).grid(row=1, column=4, padx=5, pady=5)
        ctk.CTkButton(frame_busqueda, text="Eliminar", 
                     command=self.eliminar_material).grid(row=1, column=5, padx=5, pady=5)
        ctk.CTkButton(frame_busqueda, text="Actualizar", 
                     command=self.cargar_datos).grid(row=2, column=2, padx=5, pady=5)
        
        # Frame para el Treeview
        frame_tree = ctk.CTkFrame(self.tab_inventario)
        frame_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Scrollbars
        scroll_y = ctk.CTkScrollbar(frame_tree)
        scroll_y.pack(side="right", fill="y")
        
        scroll_x = ctk.CTkScrollbar(frame_tree, orientation="horizontal")
        scroll_x.pack(side="bottom", fill="x")
        
        # Treeview
        columns = ("ID", "Código", "Nombre", "Descripción", "Categoría", "Unidad", 
                  "Cantidad", "Stock Mín", "Costo Unit.", "Estado")
        self.tree_inventario = ttk.Treeview(frame_tree, columns=columns, show="tree headings",
                                           yscrollcommand=scroll_y.set,
                                           xscrollcommand=scroll_x.set)
        
        scroll_y.configure(command=self.tree_inventario.yview)
        scroll_x.configure(command=self.tree_inventario.xview)
        
        # Configurar columnas
        self.tree_inventario.column("#0", width=0, stretch=False)
        self.tree_inventario.column("ID", width=50, anchor="center")
        self.tree_inventario.column("Código", width=100)
        self.tree_inventario.column("Nombre", width=200)
        self.tree_inventario.column("Descripción", width=300)
        self.tree_inventario.column("Categoría", width=120)
        self.tree_inventario.column("Unidad", width=80)
        self.tree_inventario.column("Cantidad", width=100, anchor="center")
        self.tree_inventario.column("Stock Mín", width=100, anchor="center")
        self.tree_inventario.column("Costo Unit.", width=100, anchor="center")
        self.tree_inventario.column("Estado", width=120, anchor="center")
        
        # Encabezados
        for col in columns:
            self.tree_inventario.heading(col, text=col, command=lambda c=col: self.ordenar_columna(c))
        
        self.tree_inventario.pack(fill="both", expand=True)
        
        # Tags para colores
        self.tree_inventario.tag_configure('normal', background='white')
        self.tree_inventario.tag_configure('bajo', background='#FFE5B4')
        self.tree_inventario.tag_configure('sin_stock', background='#FFB6C1')
        
    def crear_tab_entrada(self):
        """Crea la pestaña de entrada de material"""

        # Título
        ctk.CTkLabel(self.tab_entrada, text="ENTRADA DE MATERIAL",
                    font=("Arial", 20, "bold")).pack(pady=10)

        # Frame de búsqueda de materiales
        frame_busqueda_mat = ctk.CTkFrame(self.tab_entrada)
        frame_busqueda_mat.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(frame_busqueda_mat, text="Buscar Material:").pack(side="left", padx=5)
        self.entry_buscar_mat_entrada = ctk.CTkEntry(frame_busqueda_mat, width=300)
        self.entry_buscar_mat_entrada.pack(side="left", padx=5)
        self.entry_buscar_mat_entrada.bind('<KeyRelease>', lambda e: self.filtrar_materiales_entrada())

        ctk.CTkLabel(frame_busqueda_mat, text="Categoría:").pack(side="left", padx=5)
        categorias = ["Todas", "Fontanería y Ferretería", "Herramientas y Equipos",
                     "Seguridad", "Limpieza", "Papelería"]
        self.combo_cat_entrada = ctk.CTkComboBox(frame_busqueda_mat, values=categorias,
                                                 width=180,
                                                 command=lambda e: self.filtrar_materiales_entrada())
        self.combo_cat_entrada.pack(side="left", padx=5)
        self.combo_cat_entrada.set("Todas")

        # Frame para lista de materiales
        frame_lista_mat = ctk.CTkFrame(self.tab_entrada)
        frame_lista_mat.pack(fill="both", expand=True, padx=20, pady=5)

        # Treeview de materiales
        columns_mat = ("ID", "Código", "Nombre", "Categoría", "Stock Actual", "Unidad")
        self.tree_mat_entrada = ttk.Treeview(frame_lista_mat, columns=columns_mat,
                                            show="headings", height=8)

        self.tree_mat_entrada.heading("ID", text="ID")
        self.tree_mat_entrada.heading("Código", text="Código")
        self.tree_mat_entrada.heading("Nombre", text="Nombre")
        self.tree_mat_entrada.heading("Categoría", text="Categoría")
        self.tree_mat_entrada.heading("Stock Actual", text="Stock Actual")
        self.tree_mat_entrada.heading("Unidad", text="Unidad")

        self.tree_mat_entrada.column("ID", width=50)
        self.tree_mat_entrada.column("Código", width=100)
        self.tree_mat_entrada.column("Nombre", width=250)
        self.tree_mat_entrada.column("Categoría", width=150)
        self.tree_mat_entrada.column("Stock Actual", width=100)
        self.tree_mat_entrada.column("Unidad", width=80)

        self.tree_mat_entrada.pack(fill="both", expand=True, padx=5, pady=5)
        self.tree_mat_entrada.bind('<<TreeviewSelect>>', self.seleccionar_material_entrada)

        # Frame de datos de entrada
        frame_datos = ctk.CTkFrame(self.tab_entrada)
        frame_datos.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(frame_datos, text="Material Seleccionado:", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.label_material_sel_entrada = ctk.CTkLabel(frame_datos, text="Ninguno", font=("Arial", 12))
        self.label_material_sel_entrada.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(frame_datos, text="Stock Actual:", font=("Arial", 10)).grid(row=0, column=2, sticky="e", padx=5, pady=5)
        self.label_stock_entrada = ctk.CTkLabel(frame_datos, text="0", font=("Arial", 10, "bold"))
        self.label_stock_entrada.grid(row=0, column=3, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(frame_datos, text="Cantidad:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.entry_cantidad_entrada = ctk.CTkEntry(frame_datos, width=150)
        self.entry_cantidad_entrada.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(frame_datos, text="Origen:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.entry_origen = ctk.CTkEntry(frame_datos, width=300)
        self.entry_origen.grid(row=2, column=1, columnspan=2, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(frame_datos, text="Responsable:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.entry_responsable_entrada = ctk.CTkEntry(frame_datos, width=300)
        self.entry_responsable_entrada.grid(row=3, column=1, columnspan=2, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(frame_datos, text="Observaciones:").grid(row=4, column=0, sticky="ne", padx=5, pady=5)
        self.text_obs_entrada = ctk.CTkTextbox(frame_datos, width=400, height=60)
        self.text_obs_entrada.grid(row=4, column=1, columnspan=3, sticky="w", padx=5, pady=5)

        ctk.CTkButton(frame_datos, text="Registrar Entrada", command=self.registrar_entrada,
                     width=200, height=40).grid(row=5, column=0, columnspan=4, pady=15)

        # Variable para almacenar el material seleccionado
        self.material_seleccionado_entrada = None
        
        # Frame historial
        frame_historial = ctk.CTkFrame(self.tab_entrada)
        frame_historial.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        ctk.CTkLabel(frame_historial, text="Últimas Entradas",
                    font=("Arial", 16, "bold")).pack(pady=10)

        # Frame de búsqueda para historial
        frame_busqueda_entrada = ctk.CTkFrame(frame_historial)
        frame_busqueda_entrada.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(frame_busqueda_entrada, text="Buscar:").pack(side="left", padx=5)
        entry_busqueda_entrada = ctk.CTkEntry(frame_busqueda_entrada,
                                             textvariable=self.busqueda_entrada_var,
                                             width=300)
        entry_busqueda_entrada.pack(side="left", padx=5)
        entry_busqueda_entrada.bind('<KeyRelease>', lambda e: self.cargar_historial_entradas())

        ctk.CTkButton(frame_busqueda_entrada, text="Actualizar",
                     command=self.cargar_historial_entradas).pack(side="left", padx=5)

        # Treeview historial
        columns_hist = ("Fecha", "Material", "Cantidad", "Origen", "Responsable")
        self.tree_entradas = ttk.Treeview(frame_historial, columns=columns_hist,
                                         show="headings", height=10)

        for col in columns_hist:
            self.tree_entradas.heading(col, text=col)
            self.tree_entradas.column(col, width=200)
        
        self.tree_entradas.pack(fill="both", expand=True, padx=10, pady=10)
        
    def crear_tab_salida(self):
        """Crea la pestaña de salida de material"""

        # Título
        ctk.CTkLabel(self.tab_salida, text="SALIDA DE MATERIAL",
                    font=("Arial", 20, "bold")).pack(pady=10)

        # Frame de búsqueda de materiales
        frame_busqueda_mat = ctk.CTkFrame(self.tab_salida)
        frame_busqueda_mat.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(frame_busqueda_mat, text="Buscar Material:").pack(side="left", padx=5)
        self.entry_buscar_mat_salida = ctk.CTkEntry(frame_busqueda_mat, width=300)
        self.entry_buscar_mat_salida.pack(side="left", padx=5)
        self.entry_buscar_mat_salida.bind('<KeyRelease>', lambda e: self.filtrar_materiales_salida())

        ctk.CTkLabel(frame_busqueda_mat, text="Categoría:").pack(side="left", padx=5)
        categorias = ["Todas", "Fontanería y Ferretería", "Herramientas y Equipos",
                     "Seguridad", "Limpieza", "Papelería"]
        self.combo_cat_salida = ctk.CTkComboBox(frame_busqueda_mat, values=categorias,
                                                width=180,
                                                command=lambda e: self.filtrar_materiales_salida())
        self.combo_cat_salida.pack(side="left", padx=5)
        self.combo_cat_salida.set("Todas")

        # Frame para lista de materiales
        frame_lista_mat = ctk.CTkFrame(self.tab_salida)
        frame_lista_mat.pack(fill="both", expand=True, padx=20, pady=5)

        # Treeview de materiales
        columns_mat = ("ID", "Código", "Nombre", "Categoría", "Stock Actual", "Unidad")
        self.tree_mat_salida = ttk.Treeview(frame_lista_mat, columns=columns_mat,
                                           show="headings", height=8)

        for col in columns_mat:
            self.tree_mat_salida.heading(col, text=col)

        self.tree_mat_salida.column("ID", width=50)
        self.tree_mat_salida.column("Código", width=100)
        self.tree_mat_salida.column("Nombre", width=250)
        self.tree_mat_salida.column("Categoría", width=150)
        self.tree_mat_salida.column("Stock Actual", width=100)
        self.tree_mat_salida.column("Unidad", width=80)

        self.tree_mat_salida.pack(fill="both", expand=True, padx=5, pady=5)
        self.tree_mat_salida.bind('<<TreeviewSelect>>', self.seleccionar_material_salida)

        # Frame de datos de salida
        frame_datos = ctk.CTkFrame(self.tab_salida)
        frame_datos.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(frame_datos, text="Material Seleccionado:", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.label_material_sel_salida = ctk.CTkLabel(frame_datos, text="Ninguno", font=("Arial", 12))
        self.label_material_sel_salida.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(frame_datos, text="Stock Disponible:", font=("Arial", 10)).grid(row=0, column=2, sticky="e", padx=5, pady=5)
        self.label_stock_salida = ctk.CTkLabel(frame_datos, text="0", font=("Arial", 10, "bold"), text_color="#1f4788")
        self.label_stock_salida.grid(row=0, column=3, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(frame_datos, text="Cantidad a Retirar:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.entry_cantidad_salida = ctk.CTkEntry(frame_datos, width=150)
        self.entry_cantidad_salida.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(frame_datos, text="Destino:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        destinos = ["PTAR2 - Almacén", "PTAR2 - Taller", "PTAR2 - Bombeo",
                   "PTAR2 - Laboratorio", "PTAR2 - Oficinas", "PTAR2 - Mantenimiento", "Otro"]
        self.combo_destino = ctk.CTkComboBox(frame_datos, values=destinos, width=300)
        self.combo_destino.grid(row=2, column=1, columnspan=2, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(frame_datos, text="Responsable:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.entry_responsable_salida = ctk.CTkEntry(frame_datos, width=300)
        self.entry_responsable_salida.grid(row=3, column=1, columnspan=2, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(frame_datos, text="Observaciones:").grid(row=4, column=0, sticky="ne", padx=5, pady=5)
        self.text_obs_salida = ctk.CTkTextbox(frame_datos, width=400, height=60)
        self.text_obs_salida.grid(row=4, column=1, columnspan=3, sticky="w", padx=5, pady=5)

        ctk.CTkButton(frame_datos, text="Registrar Salida", command=self.registrar_salida,
                     width=200, height=40).grid(row=5, column=0, columnspan=4, pady=15)

        # Variable para almacenar el material seleccionado
        self.material_seleccionado_salida = None
        
        # Frame historial
        frame_historial = ctk.CTkFrame(self.tab_salida)
        frame_historial.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        ctk.CTkLabel(frame_historial, text="Últimas Salidas",
                    font=("Arial", 16, "bold")).pack(pady=10)

        # Frame de búsqueda para historial
        frame_busqueda_salida = ctk.CTkFrame(frame_historial)
        frame_busqueda_salida.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(frame_busqueda_salida, text="Buscar:").pack(side="left", padx=5)
        entry_busqueda_salida = ctk.CTkEntry(frame_busqueda_salida,
                                             textvariable=self.busqueda_salida_var,
                                             width=300)
        entry_busqueda_salida.pack(side="left", padx=5)
        entry_busqueda_salida.bind('<KeyRelease>', lambda e: self.cargar_historial_salidas())

        ctk.CTkButton(frame_busqueda_salida, text="Actualizar",
                     command=self.cargar_historial_salidas).pack(side="left", padx=5)

        # Treeview historial
        columns_hist = ("Fecha", "Material", "Cantidad", "Destino", "Responsable")
        self.tree_salidas = ttk.Treeview(frame_historial, columns=columns_hist,
                                        show="headings", height=10)

        for col in columns_hist:
            self.tree_salidas.heading(col, text=col)
            self.tree_salidas.column(col, width=200)

        self.tree_salidas.pack(fill="both", expand=True, padx=10, pady=10)
        
    def crear_tab_prestamos(self):
        """Crea la pestaña de préstamos"""

        # Título
        ctk.CTkLabel(self.tab_prestamos, text="REGISTRO DE PRÉSTAMOS",
                    font=("Arial", 20, "bold")).pack(pady=10)

        # Frame de búsqueda de materiales
        frame_busqueda_mat = ctk.CTkFrame(self.tab_prestamos)
        frame_busqueda_mat.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(frame_busqueda_mat, text="Buscar Material:").pack(side="left", padx=5)
        self.entry_buscar_mat_prestamo = ctk.CTkEntry(frame_busqueda_mat, width=300)
        self.entry_buscar_mat_prestamo.pack(side="left", padx=5)
        self.entry_buscar_mat_prestamo.bind('<KeyRelease>', lambda e: self.filtrar_materiales_prestamo())

        ctk.CTkLabel(frame_busqueda_mat, text="Categoría:").pack(side="left", padx=5)
        categorias = ["Todas", "Fontanería y Ferretería", "Herramientas y Equipos",
                     "Seguridad", "Limpieza", "Papelería"]
        self.combo_cat_prestamo = ctk.CTkComboBox(frame_busqueda_mat, values=categorias,
                                                 width=180,
                                                 command=lambda e: self.filtrar_materiales_prestamo())
        self.combo_cat_prestamo.pack(side="left", padx=5)
        self.combo_cat_prestamo.set("Todas")

        # Frame para lista de materiales
        frame_lista_mat = ctk.CTkFrame(self.tab_prestamos)
        frame_lista_mat.pack(fill="both", expand=True, padx=20, pady=5)

        # Treeview de materiales
        columns_mat = ("ID", "Código", "Nombre", "Categoría", "Stock Actual", "Unidad")
        self.tree_mat_prestamo = ttk.Treeview(frame_lista_mat, columns=columns_mat,
                                             show="headings", height=6)

        for col in columns_mat:
            self.tree_mat_prestamo.heading(col, text=col)

        self.tree_mat_prestamo.column("ID", width=50)
        self.tree_mat_prestamo.column("Código", width=100)
        self.tree_mat_prestamo.column("Nombre", width=250)
        self.tree_mat_prestamo.column("Categoría", width=150)
        self.tree_mat_prestamo.column("Stock Actual", width=100)
        self.tree_mat_prestamo.column("Unidad", width=80)

        self.tree_mat_prestamo.pack(fill="both", expand=True, padx=5, pady=5)
        self.tree_mat_prestamo.bind('<<TreeviewSelect>>', self.seleccionar_material_prestamo)

        # Frame de datos de préstamo
        frame_datos = ctk.CTkFrame(self.tab_prestamos)
        frame_datos.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(frame_datos, text="Material Seleccionado:", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.label_material_sel_prestamo = ctk.CTkLabel(frame_datos, text="Ninguno", font=("Arial", 12))
        self.label_material_sel_prestamo.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(frame_datos, text="Stock Disponible:", font=("Arial", 10)).grid(row=0, column=2, sticky="e", padx=5, pady=5)
        self.label_stock_prestamo = ctk.CTkLabel(frame_datos, text="0", font=("Arial", 10, "bold"))
        self.label_stock_prestamo.grid(row=0, column=3, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(frame_datos, text="Cantidad:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.entry_cantidad_prestamo = ctk.CTkEntry(frame_datos, width=150)
        self.entry_cantidad_prestamo.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(frame_datos, text="Prestado a:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.entry_prestado_a = ctk.CTkEntry(frame_datos, width=300)
        self.entry_prestado_a.grid(row=2, column=1, columnspan=2, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(frame_datos, text="Área/Destino:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.entry_area_prestamo = ctk.CTkEntry(frame_datos, width=300)
        self.entry_area_prestamo.grid(row=3, column=1, columnspan=2, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(frame_datos, text="Observaciones:").grid(row=4, column=0, sticky="ne", padx=5, pady=5)
        self.text_obs_prestamo = ctk.CTkTextbox(frame_datos, width=400, height=50)
        self.text_obs_prestamo.grid(row=4, column=1, columnspan=3, sticky="w", padx=5, pady=5)

        ctk.CTkButton(frame_datos, text="Registrar Préstamo", command=self.registrar_prestamo,
                     width=200, height=40).grid(row=5, column=0, columnspan=4, pady=10)

        # Variable para almacenar el material seleccionado
        self.material_seleccionado_prestamo = None
        
        # Frame para lista de préstamos
        frame_lista = ctk.CTkFrame(self.tab_prestamos)
        frame_lista.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        ctk.CTkLabel(frame_lista, text="PRÉSTAMOS ACTIVOS", 
                    font=("Arial", 16, "bold")).pack(pady=10)
        
        # Frame de búsqueda y filtros
        frame_busqueda_prestamo = ctk.CTkFrame(frame_lista)
        frame_busqueda_prestamo.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(frame_busqueda_prestamo, text="Buscar:").pack(side="left", padx=5)
        entry_busqueda_prestamo = ctk.CTkEntry(frame_busqueda_prestamo,
                                               textvariable=self.busqueda_prestamo_var,
                                               width=250)
        entry_busqueda_prestamo.pack(side="left", padx=5)
        entry_busqueda_prestamo.bind('<KeyRelease>', lambda e: self.cargar_prestamos())

        ctk.CTkLabel(frame_busqueda_prestamo, text="Estado:").pack(side="left", padx=5)
        estados = ["Todos", "Activo", "Devuelto"]
        combo_estado_prestamo = ctk.CTkComboBox(frame_busqueda_prestamo, values=estados,
                                                variable=self.filtro_estado_prestamo,
                                                command=lambda e: self.cargar_prestamos(),
                                                width=120)
        combo_estado_prestamo.pack(side="left", padx=5)

        # Botones
        frame_botones = ctk.CTkFrame(frame_lista)
        frame_botones.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(frame_botones, text="Registrar Devolución",
                     command=self.registrar_devolucion).pack(side="left", padx=5)
        ctk.CTkButton(frame_botones, text="Actualizar",
                     command=self.cargar_prestamos).pack(side="left", padx=5)
        
        # Treeview
        columns = ("ID", "Material", "Cantidad", "Prestado a", "Área", "Fecha Préstamo", "Estado")
        self.tree_prestamos = ttk.Treeview(frame_lista, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree_prestamos.heading(col, text=col)
            if col == "ID":
                self.tree_prestamos.column(col, width=50)
            elif col == "Cantidad":
                self.tree_prestamos.column(col, width=100)
            else:
                self.tree_prestamos.column(col, width=150)
        
        self.tree_prestamos.pack(fill="both", expand=True, padx=10, pady=10)
        
    def crear_tab_en_uso(self):
        """Crea la pestaña de material en uso"""

        # Título
        ctk.CTkLabel(self.tab_en_uso, text="REGISTRAR MATERIAL EN USO",
                    font=("Arial", 20, "bold")).pack(pady=10)

        # Frame de búsqueda de materiales
        frame_busqueda_mat = ctk.CTkFrame(self.tab_en_uso)
        frame_busqueda_mat.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(frame_busqueda_mat, text="Buscar Material:").pack(side="left", padx=5)
        self.entry_buscar_mat_uso = ctk.CTkEntry(frame_busqueda_mat, width=300)
        self.entry_buscar_mat_uso.pack(side="left", padx=5)
        self.entry_buscar_mat_uso.bind('<KeyRelease>', lambda e: self.filtrar_materiales_uso())

        ctk.CTkLabel(frame_busqueda_mat, text="Categoría:").pack(side="left", padx=5)
        categorias = ["Todas", "Fontanería y Ferretería", "Herramientas y Equipos",
                     "Seguridad", "Limpieza", "Papelería"]
        self.combo_cat_uso = ctk.CTkComboBox(frame_busqueda_mat, values=categorias,
                                            width=180,
                                            command=lambda e: self.filtrar_materiales_uso())
        self.combo_cat_uso.pack(side="left", padx=5)
        self.combo_cat_uso.set("Todas")

        # Frame para lista de materiales
        frame_lista_mat = ctk.CTkFrame(self.tab_en_uso)
        frame_lista_mat.pack(fill="both", expand=True, padx=20, pady=5)

        # Treeview de materiales
        columns_mat = ("ID", "Código", "Nombre", "Categoría", "Stock Actual", "Unidad")
        self.tree_mat_uso = ttk.Treeview(frame_lista_mat, columns=columns_mat,
                                        show="headings", height=6)

        for col in columns_mat:
            self.tree_mat_uso.heading(col, text=col)

        self.tree_mat_uso.column("ID", width=50)
        self.tree_mat_uso.column("Código", width=100)
        self.tree_mat_uso.column("Nombre", width=250)
        self.tree_mat_uso.column("Categoría", width=150)
        self.tree_mat_uso.column("Stock Actual", width=100)
        self.tree_mat_uso.column("Unidad", width=80)

        self.tree_mat_uso.pack(fill="both", expand=True, padx=5, pady=5)
        self.tree_mat_uso.bind('<<TreeviewSelect>>', self.seleccionar_material_uso)

        # Frame de datos
        frame_datos = ctk.CTkFrame(self.tab_en_uso)
        frame_datos.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(frame_datos, text="Material Seleccionado:", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.label_material_sel_uso = ctk.CTkLabel(frame_datos, text="Ninguno", font=("Arial", 12))
        self.label_material_sel_uso.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(frame_datos, text="Stock Disponible:", font=("Arial", 10)).grid(row=0, column=2, sticky="e", padx=5, pady=5)
        self.label_stock_uso = ctk.CTkLabel(frame_datos, text="0", font=("Arial", 10, "bold"))
        self.label_stock_uso.grid(row=0, column=3, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(frame_datos, text="Cantidad:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.entry_cantidad_uso = ctk.CTkEntry(frame_datos, width=150)
        self.entry_cantidad_uso.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(frame_datos, text="Equipo/Instalación:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.entry_equipo_uso = ctk.CTkEntry(frame_datos, width=300)
        self.entry_equipo_uso.grid(row=2, column=1, columnspan=2, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(frame_datos, text="Responsable:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.entry_responsable_uso = ctk.CTkEntry(frame_datos, width=300)
        self.entry_responsable_uso.grid(row=3, column=1, columnspan=2, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(frame_datos, text="Observaciones:").grid(row=4, column=0, sticky="ne", padx=5, pady=5)
        self.text_obs_uso = ctk.CTkTextbox(frame_datos, width=400, height=50)
        self.text_obs_uso.grid(row=4, column=1, columnspan=3, sticky="w", padx=5, pady=5)

        ctk.CTkButton(frame_datos, text="Registrar Material en Uso", command=self.registrar_material_uso,
                     width=200, height=40).grid(row=5, column=0, columnspan=4, pady=10)

        # Variable para almacenar el material seleccionado
        self.material_seleccionado_uso = None
        
        # Frame para lista
        frame_lista = ctk.CTkFrame(self.tab_en_uso)
        frame_lista.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        ctk.CTkLabel(frame_lista, text="MATERIAL ACTUALMENTE EN USO",
                    font=("Arial", 16, "bold")).pack(pady=10)

        # Frame de búsqueda
        frame_busqueda_uso = ctk.CTkFrame(frame_lista)
        frame_busqueda_uso.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(frame_busqueda_uso, text="Buscar:").pack(side="left", padx=5)
        entry_busqueda_uso = ctk.CTkEntry(frame_busqueda_uso,
                                          textvariable=self.busqueda_uso_var,
                                          width=300)
        entry_busqueda_uso.pack(side="left", padx=5)
        entry_busqueda_uso.bind('<KeyRelease>', lambda e: self.cargar_material_en_uso())

        # Botones
        frame_botones = ctk.CTkFrame(frame_lista)
        frame_botones.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(frame_botones, text="Dar de Baja",
                     command=self.dar_baja_material_uso).pack(side="left", padx=5)
        ctk.CTkButton(frame_botones, text="Actualizar",
                     command=self.cargar_material_en_uso).pack(side="left", padx=5)
        
        # Treeview
        columns = ("ID", "Material", "Cantidad", "Equipo/Instalación", "Fecha Instalación", "Responsable")
        self.tree_en_uso = ttk.Treeview(frame_lista, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree_en_uso.heading(col, text=col)
            if col == "ID":
                self.tree_en_uso.column(col, width=50)
            elif col == "Cantidad":
                self.tree_en_uso.column(col, width=100)
            else:
                self.tree_en_uso.column(col, width=180)
        
        self.tree_en_uso.pack(fill="both", expand=True, padx=10, pady=10)
        
    def crear_tab_reportes(self):
        """Crea la pestaña de reportes"""
        
        frame = ctk.CTkFrame(self.tab_reportes)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="REPORTES Y EXPORTACIÓN", 
                    font=("Arial", 20, "bold")).pack(pady=20)
        
        # Frame de reportes
        frame_reportes = ctk.CTkFrame(frame)
        frame_reportes.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(frame_reportes, text="📊 Inventario Completo (Excel)", 
                     command=lambda: self.exportar_reporte("inventario"),
                     width=300, height=50).pack(pady=10)
        
        ctk.CTkButton(frame_reportes, text="⚠️ Materiales con Stock Bajo (Excel)", 
                     command=lambda: self.exportar_reporte("stock_bajo"),
                     width=300, height=50).pack(pady=10)
        
        ctk.CTkButton(frame_reportes, text="📦 Movimientos del Mes (Excel)", 
                     command=lambda: self.exportar_reporte("movimientos"),
                     width=300, height=50).pack(pady=10)
        
        ctk.CTkButton(frame_reportes, text="🔄 Préstamos Activos (Excel)", 
                     command=lambda: self.exportar_reporte("prestamos"),
                     width=300, height=50).pack(pady=10)
        
        ctk.CTkButton(frame_reportes, text="🔧 Material en Uso (Excel)", 
                     command=lambda: self.exportar_reporte("en_uso"),
                     width=300, height=50).pack(pady=10)
        
        # Estadísticas
        frame_stats = ctk.CTkFrame(frame)
        frame_stats.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame_stats, text="ESTADÍSTICAS", 
                    font=("Arial", 18, "bold")).pack(pady=10)
        
        self.label_stats = ctk.CTkLabel(frame_stats, text="", font=("Arial", 12), justify="left")
        self.label_stats.pack(pady=20)
        
        ctk.CTkButton(frame_stats, text="Actualizar Estadísticas", 
                     command=self.actualizar_estadisticas).pack(pady=10)
        
    def cargar_datos(self):
        """Carga los datos en el Treeview del inventario"""
        
        # Limpiar treeview
        for item in self.tree_inventario.get_children():
            self.tree_inventario.delete(item)
        
        # Construir query con filtros
        query = "SELECT * FROM materiales WHERE 1=1"
        params = []
        
        # Filtro de búsqueda
        if self.busqueda_var.get():
            query += " AND (codigo LIKE ? OR nombre LIKE ? OR descripcion LIKE ?)"
            search_term = f"%{self.busqueda_var.get()}%"
            params.extend([search_term, search_term, search_term])
        
        # Filtro categoría
        if self.filtro_categoria.get() != "Todas":
            query += " AND categoria = ?"
            params.append(self.filtro_categoria.get())
        
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        
        for row in rows:
            cantidad = row[6]
            stock_min = row[7]
            
            # Determinar estado
            if cantidad <= 0:
                estado = "Sin Stock"
                tag = 'sin_stock'
            elif cantidad <= stock_min:
                estado = "Stock Bajo"
                tag = 'bajo'
            else:
                estado = "Normal"
                tag = 'normal'
            
            # Filtro de estado
            if self.filtro_estado.get() != "Todos":
                if self.filtro_estado.get() == "Stock Normal" and estado != "Normal":
                    continue
                elif self.filtro_estado.get() == "Stock Bajo" and estado != "Stock Bajo":
                    continue
                elif self.filtro_estado.get() == "Sin Stock" and estado != "Sin Stock":
                    continue
            
            # Sin ubicación: row[0]=id, [1]=codigo, [2]=nombre, [3]=desc, [4]=cat, [5]=unidad,
            # [6]=cantidad, [7]=stock_min, [8]=ubicacion, [9]=costo, [10]=fecha, [11]=notas, [12]=imagen
            values = (row[0], row[1], row[2], row[3], row[4], row[5], 
                     f"{cantidad:.2f}", f"{stock_min:.2f}", 
                     f"${row[9]:.2f}", estado)
            
            self.tree_inventario.insert("", "end", values=values, tags=(tag,))
        
        # Actualizar combos de materiales
        self.actualizar_combos_materiales()
        
        # Actualizar historial de movimientos
        self.cargar_historial_movimientos()
        
    def actualizar_combos_materiales(self):
        """Actualiza los combobox con la lista de materiales"""
        
        self.cursor.execute("SELECT nombre FROM materiales ORDER BY nombre")
        materiales = [row[0] for row in self.cursor.fetchall()]
        
        if materiales:
            self.combo_material_entrada.set_items(materiales)
            self.combo_material_salida.set_items(materiales)
            self.combo_material_prestamo.set_items(materiales)
            self.combo_material_uso.set_items(materiales)
        
    def generar_codigo_automatico(self, categoria):
        """Genera un código único automático basado en la categoría"""
        
        # Prefijos por categoría
        prefijos = {
            "Fontanería y Ferretería": "FON",
            "Herramientas y Equipos": "HER",
            "Seguridad": "SEG",
            "Limpieza": "LIM",
            "Papelería": "PAP"
        }
        
        prefijo = prefijos.get(categoria, "MAT")
        
        # Buscar el último número usado para esta categoría
        self.cursor.execute("""
            SELECT codigo FROM materiales 
            WHERE codigo LIKE ? 
            ORDER BY codigo DESC 
            LIMIT 1
        """, (f"{prefijo}-%",))
        
        resultado = self.cursor.fetchone()
        
        if resultado:
            # Extraer el número del último código
            try:
                ultimo_numero = int(resultado[0].split('-')[1])
                nuevo_numero = ultimo_numero + 1
            except:
                nuevo_numero = 1
        else:
            nuevo_numero = 1
        
        # Generar código con formato: PREFIJO-###
        codigo = f"{prefijo}-{nuevo_numero:03d}"
        
        # Verificar que no existe (por seguridad)
        self.cursor.execute("SELECT codigo FROM materiales WHERE codigo = ?", (codigo,))
        if self.cursor.fetchone():
            # Si existe, buscar el próximo disponible
            contador = nuevo_numero + 1
            while True:
                codigo = f"{prefijo}-{contador:03d}"
                self.cursor.execute("SELECT codigo FROM materiales WHERE codigo = ?", (codigo,))
                if not self.cursor.fetchone():
                    break
                contador += 1
        
        return codigo
    
    def agregar_material(self):
        """Abre ventana para agregar nuevo material"""
        
        ventana = ctk.CTkToplevel(self.root)
        ventana.title("Agregar Nuevo Material")
        ventana.geometry("700x850")
        ventana.grab_set()
        
        # Variable para la imagen
        imagen_seleccionada = {"ruta": None}
        
        # Variable para código automático
        auto_codigo = ctk.BooleanVar(value=True)
        
        # Frame principal con scroll
        main_frame = ctk.CTkScrollableFrame(ventana, width=650, height=800)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título
        ctk.CTkLabel(main_frame, text="AGREGAR NUEVO MATERIAL", 
                    font=("Arial", 18, "bold")).grid(row=0, column=0, columnspan=3, pady=15)
        
        # Frame para código con checkbox
        frame_codigo = ctk.CTkFrame(main_frame, fg_color="transparent")
        frame_codigo.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(frame_codigo, text="Código:").pack(side="left", padx=(0, 10))
        
        entry_codigo = ctk.CTkEntry(frame_codigo, width=150)
        entry_codigo.pack(side="left", padx=(0, 10))
        
        check_auto = ctk.CTkCheckBox(frame_codigo, text="🔄 Generar automáticamente", 
                                     variable=auto_codigo,
                                     command=lambda: actualizar_codigo_auto())
        check_auto.pack(side="left", padx=5)
        
        # Etiqueta de vista previa del código
        label_preview = ctk.CTkLabel(frame_codigo, text="", 
                                     font=("Arial", 11, "bold"),
                                     text_color="#1f4788")
        label_preview.pack(side="left", padx=10)
        
        # Campos restantes
        campos = [
            ("Nombre:", "nombre"),
            ("Descripción:", "descripcion"),
            ("Categoría:", "categoria"),
            ("Unidad:", "unidad"),
            ("Cantidad Inicial:", "cantidad"),
            ("Stock Mínimo:", "stock_min"),
            ("Costo Unitario:", "costo"),
            ("Notas:", "notas")
        ]
        
        entries = {"codigo": entry_codigo}
        row = 2
        
        for i, (label, key) in enumerate(campos):
            ctk.CTkLabel(main_frame, text=label).grid(row=row, column=0, sticky="e", padx=10, pady=10)
            
            if key == "categoria":
                entry = ctk.CTkComboBox(main_frame, width=300, 
                                       values=["Fontanería y Ferretería", "Herramientas y Equipos", 
                                              "Seguridad", "Limpieza", "Papelería"],
                                       command=lambda e: actualizar_codigo_auto())
                entry.set("Fontanería y Ferretería")  # Valor por defecto
            elif key == "unidad":
                entry = ctk.CTkComboBox(main_frame, width=300,
                                       values=["Piezas", "Litros", "Kilogramos", "Metros",
                                              "Cajas", "Sets", "Rollos", "Bolsas", "Galones"])
                entry.set("Piezas")  # Valor por defecto
            elif key in ["descripcion", "notas"]:
                entry = ctk.CTkTextbox(main_frame, width=300, height=80)
            else:
                entry = ctk.CTkEntry(main_frame, width=300)
            
            entry.grid(row=row, column=1, sticky="w", padx=10, pady=10, columnspan=2)
            entries[key] = entry
            row += 1
        
        def actualizar_codigo_auto():
            """Actualiza el código automáticamente según la categoría"""
            if auto_codigo.get():
                categoria = entries["categoria"].get()
                codigo_generado = self.generar_codigo_automatico(categoria)
                entry_codigo.delete(0, 'end')
                entry_codigo.insert(0, codigo_generado)
                entry_codigo.configure(state="disabled")
                label_preview.configure(text=f"➜ {codigo_generado}")
            else:
                entry_codigo.configure(state="normal")
                label_preview.configure(text="")
        
        # Generar código inicial
        actualizar_codigo_auto()
        
        # Separador
        ctk.CTkLabel(main_frame, text="").grid(row=row, column=0, pady=5)
        row += 1
        
        # Sección de imagen
        ctk.CTkLabel(main_frame, text="IMAGEN DEL MATERIAL", 
                    font=("Arial", 14, "bold")).grid(row=row, column=0, columnspan=3, pady=10)
        row += 1
        
        # Frame para la imagen
        frame_imagen = ctk.CTkFrame(main_frame, width=300, height=300, fg_color="gray90")
        frame_imagen.grid(row=row, column=0, columnspan=3, padx=10, pady=10)
        frame_imagen.grid_propagate(False)
        
        label_imagen = ctk.CTkLabel(frame_imagen, text="Sin imagen\n\n📷\n\nHaz clic en 'Seleccionar Imagen'", 
                                    font=("Arial", 12),
                                    text_color="gray")
        label_imagen.pack(expand=True)
        row += 1
        
        def seleccionar_imagen():
            """Permite seleccionar una imagen"""
            archivo = filedialog.askopenfilename(
                title="Seleccionar imagen del material",
                filetypes=[
                    ("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp"),
                    ("Todos los archivos", "*.*")
                ]
            )
            
            if archivo:
                try:
                    # Cargar y redimensionar imagen
                    img = Image.open(archivo)
                    img.thumbnail((280, 280), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    
                    # Mostrar en label
                    label_imagen.configure(image=photo, text="")
                    label_imagen.image = photo  # Mantener referencia
                    
                    # Guardar ruta
                    imagen_seleccionada["ruta"] = archivo
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Error al cargar imagen: {str(e)}")
        
        def eliminar_imagen():
            """Elimina la imagen seleccionada"""
            label_imagen.configure(image="", 
                                  text="Sin imagen\n\n📷\n\nHaz clic en 'Seleccionar Imagen'")
            label_imagen.image = None
            imagen_seleccionada["ruta"] = None
        
        # Botones de imagen
        frame_botones_img = ctk.CTkFrame(main_frame, fg_color="transparent")
        frame_botones_img.grid(row=row, column=0, columnspan=3, pady=10)
        
        ctk.CTkButton(frame_botones_img, text="📷 Seleccionar Imagen", 
                     command=seleccionar_imagen, width=150).pack(side="left", padx=5)
        ctk.CTkButton(frame_botones_img, text="🗑️ Quitar Imagen", 
                     command=eliminar_imagen, width=150).pack(side="left", padx=5)
        row += 1
        
        def guardar():
            try:
                # Habilitar campo código temporalmente para leer
                entry_codigo.configure(state="normal")
                codigo = entry_codigo.get()
                
                nombre = entries["nombre"].get()
                
                if not codigo or not nombre:
                    messagebox.showerror("Error", "Código y Nombre son obligatorios")
                    return
                
                # Verificar que el código no exista
                self.cursor.execute("SELECT codigo FROM materiales WHERE codigo = ?", (codigo,))
                if self.cursor.fetchone():
                    messagebox.showerror("Error", f"El código '{codigo}' ya existe.\n\nPrueba generar uno automático.")
                    return
                
                descripcion = entries["descripcion"].get("1.0", "end-1c") if isinstance(entries["descripcion"], ctk.CTkTextbox) else entries["descripcion"].get()
                categoria = entries["categoria"].get()
                unidad = entries["unidad"].get()
                cantidad = float(entries["cantidad"].get() or 0)
                stock_min = float(entries["stock_min"].get() or 0)
                ubicacion = "PTAR2 - Almacén"
                costo = float(entries["costo"].get() or 0)
                notas = entries["notas"].get("1.0", "end-1c") if isinstance(entries["notas"], ctk.CTkTextbox) else entries["notas"].get()
                
                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Procesar imagen si existe
                imagen_ruta = None
                if imagen_seleccionada["ruta"]:
                    # Crear nombre único para la imagen
                    extension = os.path.splitext(imagen_seleccionada["ruta"])[1]
                    nombre_imagen = f"{codigo}{extension}"
                    ruta_destino = os.path.join(self.imagenes_dir, nombre_imagen)
                    
                    # Copiar imagen
                    shutil.copy2(imagen_seleccionada["ruta"], ruta_destino)
                    imagen_ruta = nombre_imagen
                
                # Insertar en base de datos
                self.cursor.execute('''
                    INSERT INTO materiales (codigo, nombre, descripcion, categoria, unidad,
                                          cantidad_actual, stock_minimo, ubicacion, costo_unitario,
                                          fecha_registro, notas, imagen_ruta)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (codigo, nombre, descripcion, categoria, unidad, cantidad, stock_min,
                     ubicacion, costo, fecha_actual, notas, imagen_ruta))
                
                self.conn.commit()
                
                messagebox.showinfo("Éxito", f"Material agregado correctamente\n\nCódigo: {codigo}")
                ventana.destroy()
                self.cargar_datos()
                
            except ValueError:
                messagebox.showerror("Error", "Verifica que los valores numéricos sean correctos")
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {str(e)}")
        
        # Botón guardar
        ctk.CTkButton(main_frame, text="💾 Guardar Material", command=guardar, 
                     width=250, height=45, font=("Arial", 14, "bold")).grid(
            row=row, column=0, columnspan=3, pady=20)
        
    def editar_material(self):
        """Edita el material seleccionado"""
        
        seleccion = self.tree_inventario.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona un material para editar")
            return
        
        item = self.tree_inventario.item(seleccion[0])
        material_id = item['values'][0]
        
        # Obtener datos actuales
        self.cursor.execute("SELECT * FROM materiales WHERE id = ?", (material_id,))
        material = self.cursor.fetchone()
        
        if not material:
            messagebox.showerror("Error", "Material no encontrado")
            return
        
        # Crear ventana de edición
        ventana = ctk.CTkToplevel(self.root)
        ventana.title("Editar Material")
        ventana.geometry("700x800")
        ventana.grab_set()
        
        # Variable para la imagen
        imagen_seleccionada = {"ruta": None, "cambio": False}
        imagen_actual = material[12] if len(material) > 12 else None  # imagen_ruta
        
        # Frame principal con scroll
        main_frame = ctk.CTkScrollableFrame(ventana, width=650, height=750)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título
        ctk.CTkLabel(main_frame, text="EDITAR MATERIAL", 
                    font=("Arial", 18, "bold")).grid(row=0, column=0, columnspan=3, pady=15)
        
        # Campos con valores actuales
        campos_datos = [
            ("Código:", material[1]),
            ("Nombre:", material[2]),
            ("Descripción:", material[3]),
            ("Categoría:", material[4]),
            ("Unidad:", material[5]),
            ("Cantidad Actual:", material[6]),
            ("Stock Mínimo:", material[7]),
            ("Costo Unitario:", material[9]),
            ("Notas:", material[11])
        ]
        
        entries = {}
        row = 1
        
        for i, (label, valor) in enumerate(campos_datos):
            ctk.CTkLabel(main_frame, text=label).grid(row=row, column=0, sticky="e", padx=10, pady=10)
            
            key = label.replace(":", "").replace(" ", "_").lower()
            
            if "categoría" in label.lower():
                entry = ctk.CTkComboBox(main_frame, width=300, 
                                       values=["Fontanería y Ferretería", "Herramientas y Equipos", 
                                              "Seguridad", "Limpieza", "Papelería"])
                if valor:
                    entry.set(valor)
            elif "unidad" in label.lower():
                entry = ctk.CTkComboBox(main_frame, width=300,
                                       values=["Piezas", "Litros", "Kilogramos", "Metros",
                                              "Cajas", "Sets", "Rollos", "Bolsas", "Galones"])
                if valor:
                    entry.set(valor)
            elif "descripción" in label.lower() or "notas" in label.lower():
                entry = ctk.CTkTextbox(main_frame, width=300, height=80)
                if valor:
                    entry.insert("1.0", str(valor))
            else:
                entry = ctk.CTkEntry(main_frame, width=300)
                if valor is not None:
                    entry.insert(0, str(valor))
            
            entry.grid(row=row, column=1, sticky="w", padx=10, pady=10, columnspan=2)
            entries[key] = entry
            row += 1
        
        # Separador
        ctk.CTkLabel(main_frame, text="").grid(row=row, column=0, pady=5)
        row += 1
        
        # Sección de imagen
        ctk.CTkLabel(main_frame, text="IMAGEN DEL MATERIAL", 
                    font=("Arial", 14, "bold")).grid(row=row, column=0, columnspan=3, pady=10)
        row += 1
        
        # Frame para la imagen
        frame_imagen = ctk.CTkFrame(main_frame, width=300, height=300, fg_color="gray90")
        frame_imagen.grid(row=row, column=0, columnspan=3, padx=10, pady=10)
        frame_imagen.grid_propagate(False)
        
        label_imagen = ctk.CTkLabel(frame_imagen, text="", font=("Arial", 12))
        label_imagen.pack(expand=True)
        
        # Cargar imagen actual si existe
        if imagen_actual:
            ruta_completa = os.path.join(self.imagenes_dir, imagen_actual)
            if os.path.exists(ruta_completa):
                try:
                    img = Image.open(ruta_completa)
                    img.thumbnail((280, 280), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    label_imagen.configure(image=photo, text="")
                    label_imagen.image = photo
                except:
                    label_imagen.configure(text="Sin imagen\n\n📷\n\nHaz clic en 'Seleccionar Imagen'",
                                         text_color="gray")
            else:
                label_imagen.configure(text="Sin imagen\n\n📷\n\nHaz clic en 'Seleccionar Imagen'",
                                     text_color="gray")
        else:
            label_imagen.configure(text="Sin imagen\n\n📷\n\nHaz clic en 'Seleccionar Imagen'",
                                 text_color="gray")
        
        row += 1
        
        def seleccionar_imagen():
            """Permite seleccionar una nueva imagen"""
            archivo = filedialog.askopenfilename(
                title="Seleccionar imagen del material",
                filetypes=[
                    ("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp"),
                    ("Todos los archivos", "*.*")
                ]
            )
            
            if archivo:
                try:
                    # Cargar y redimensionar imagen
                    img = Image.open(archivo)
                    img.thumbnail((280, 280), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    
                    # Mostrar en label
                    label_imagen.configure(image=photo, text="")
                    label_imagen.image = photo
                    
                    # Guardar ruta y marcar cambio
                    imagen_seleccionada["ruta"] = archivo
                    imagen_seleccionada["cambio"] = True
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Error al cargar imagen: {str(e)}")
        
        def eliminar_imagen():
            """Elimina la imagen"""
            label_imagen.configure(image="", 
                                  text="Sin imagen\n\n📷\n\nHaz clic en 'Seleccionar Imagen'",
                                  text_color="gray")
            label_imagen.image = None
            imagen_seleccionada["ruta"] = None
            imagen_seleccionada["cambio"] = True
        
        # Botones de imagen
        frame_botones_img = ctk.CTkFrame(main_frame, fg_color="transparent")
        frame_botones_img.grid(row=row, column=0, columnspan=3, pady=10)
        
        ctk.CTkButton(frame_botones_img, text="📷 Cambiar Imagen", 
                     command=seleccionar_imagen, width=150).pack(side="left", padx=5)
        ctk.CTkButton(frame_botones_img, text="🗑️ Quitar Imagen", 
                     command=eliminar_imagen, width=150).pack(side="left", padx=5)
        row += 1
        
        def guardar_cambios():
            try:
                # Obtener valores
                codigo = entries["código"].get()
                nombre = entries["nombre"].get()
                
                if not codigo or not nombre:
                    messagebox.showerror("Error", "Código y Nombre son obligatorios")
                    return
                
                descripcion = entries["descripción"].get("1.0", "end-1c") if isinstance(entries["descripción"], ctk.CTkTextbox) else entries["descripción"].get()
                categoria = entries["categoría"].get()
                unidad = entries["unidad"].get()
                cantidad = float(entries["cantidad_actual"].get() or 0)
                stock_min = float(entries["stock_mínimo"].get() or 0)
                costo = float(entries["costo_unitario"].get() or 0)
                notas = entries["notas"].get("1.0", "end-1c") if isinstance(entries["notas"], ctk.CTkTextbox) else entries["notas"].get()
                ubicacion = "PTAR2 - Almacén"
                
                # Procesar imagen si hubo cambio
                imagen_ruta = imagen_actual  # Mantener la actual por defecto
                
                if imagen_seleccionada["cambio"]:
                    if imagen_seleccionada["ruta"]:
                        # Nueva imagen seleccionada
                        extension = os.path.splitext(imagen_seleccionada["ruta"])[1]
                        nombre_imagen = f"{codigo}{extension}"
                        ruta_destino = os.path.join(self.imagenes_dir, nombre_imagen)
                        
                        # Borrar imagen anterior si existe y es diferente
                        if imagen_actual and imagen_actual != nombre_imagen:
                            ruta_anterior = os.path.join(self.imagenes_dir, imagen_actual)
                            if os.path.exists(ruta_anterior):
                                os.remove(ruta_anterior)
                        
                        # Copiar nueva imagen
                        shutil.copy2(imagen_seleccionada["ruta"], ruta_destino)
                        imagen_ruta = nombre_imagen
                    else:
                        # Imagen eliminada
                        if imagen_actual:
                            ruta_anterior = os.path.join(self.imagenes_dir, imagen_actual)
                            if os.path.exists(ruta_anterior):
                                os.remove(ruta_anterior)
                        imagen_ruta = None
                
                # Actualizar en base de datos
                self.cursor.execute('''
                    UPDATE materiales 
                    SET codigo=?, nombre=?, descripcion=?, categoria=?, unidad=?,
                        cantidad_actual=?, stock_minimo=?, ubicacion=?, costo_unitario=?,
                        notas=?, imagen_ruta=?
                    WHERE id=?
                ''', (codigo, nombre, descripcion, categoria, unidad, cantidad, stock_min,
                     ubicacion, costo, notas, imagen_ruta, material_id))
                
                self.conn.commit()
                
                messagebox.showinfo("Éxito", "Material actualizado correctamente")
                ventana.destroy()
                self.cargar_datos()
                
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "El código ya existe")
            except ValueError:
                messagebox.showerror("Error", "Verifica que los valores numéricos sean correctos")
            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar: {str(e)}")
        
        # Botones
        frame_botones = ctk.CTkFrame(main_frame, fg_color="transparent")
        frame_botones.grid(row=row, column=0, columnspan=3, pady=20)
        
        ctk.CTkButton(frame_botones, text="💾 Guardar Cambios", command=guardar_cambios, 
                     width=200, height=45, font=("Arial", 14, "bold")).pack(side="left", padx=5)
        ctk.CTkButton(frame_botones, text="❌ Cancelar", command=ventana.destroy, 
                     width=150, height=45).pack(side="left", padx=5)
        
    def ver_imagen_material(self):
        """Muestra la imagen del material seleccionado"""
        
        seleccion = self.tree_inventario.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona un material para ver su imagen")
            return
        
        item = self.tree_inventario.item(seleccion[0])
        material_id = item['values'][0]
        material_nombre = item['values'][2]
        
        # Obtener datos del material incluyendo imagen
        self.cursor.execute("SELECT imagen_ruta FROM materiales WHERE id = ?", (material_id,))
        resultado = self.cursor.fetchone()
        
        if not resultado or not resultado[0]:
            messagebox.showinfo("Sin imagen", 
                              f"El material '{material_nombre}' no tiene imagen asociada.\n\n"
                              "Puedes agregarla editando el material.")
            return
        
        imagen_ruta = resultado[0]
        ruta_completa = os.path.join(self.imagenes_dir, imagen_ruta)
        
        if not os.path.exists(ruta_completa):
            messagebox.showerror("Error", "El archivo de imagen no existe")
            return
        
        # Crear ventana para mostrar imagen
        ventana = ctk.CTkToplevel(self.root)
        ventana.title(f"Imagen: {material_nombre}")
        ventana.geometry("600x650")
        
        # Título
        ctk.CTkLabel(ventana, text=material_nombre, 
                    font=("Arial", 16, "bold")).pack(pady=10)
        
        # Frame para la imagen
        frame_imagen = ctk.CTkFrame(ventana, width=550, height=550)
        frame_imagen.pack(padx=20, pady=10)
        frame_imagen.pack_propagate(False)
        
        try:
            # Cargar y mostrar imagen
            img = Image.open(ruta_completa)
            img.thumbnail((530, 530), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            label_img = ctk.CTkLabel(frame_imagen, image=photo, text="")
            label_img.image = photo  # Mantener referencia
            label_img.pack(expand=True)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar imagen: {str(e)}")
            ventana.destroy()
            return
        
        # Botón cerrar
        ctk.CTkButton(ventana, text="Cerrar", command=ventana.destroy, 
                     width=150).pack(pady=10)
        
    def eliminar_material(self):
        """Elimina el material seleccionado"""
        
        seleccion = self.tree_inventario.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona un material para eliminar")
            return
        
        item = self.tree_inventario.item(seleccion[0])
        material_id = item['values'][0]
        nombre = item['values'][2]
        
        respuesta = messagebox.askyesno("Confirmar", 
                                       f"¿Estás seguro de eliminar '{nombre}'?\n\n"
                                       "Esta acción no se puede deshacer.")
        
        if respuesta:
            try:
                self.cursor.execute("DELETE FROM materiales WHERE id = ?", (material_id,))
                self.conn.commit()
                messagebox.showinfo("Éxito", "Material eliminado correctamente")
                self.cargar_datos()
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar: {str(e)}")

    def filtrar_materiales_entrada(self):
        """Filtra los materiales en el tab de entrada"""
        for item in self.tree_mat_entrada.get_children():
            self.tree_mat_entrada.delete(item)

        busqueda = self.entry_buscar_mat_entrada.get().lower()
        categoria = self.combo_cat_entrada.get()

        query = "SELECT id, codigo, nombre, categoria, cantidad_actual, unidad FROM materiales WHERE 1=1"
        params = []

        if busqueda:
            query += " AND (LOWER(nombre) LIKE ? OR LOWER(codigo) LIKE ?)"
            params.extend([f"%{busqueda}%", f"%{busqueda}%"])

        if categoria != "Todas":
            query += " AND categoria = ?"
            params.append(categoria)

        query += " ORDER BY nombre"

        self.cursor.execute(query, params)
        for row in self.cursor.fetchall():
            self.tree_mat_entrada.insert("", "end", values=row)

    def seleccionar_material_entrada(self, event):
        """Maneja la selección de un material en entrada"""
        seleccion = self.tree_mat_entrada.selection()
        if seleccion:
            item = self.tree_mat_entrada.item(seleccion[0])
            valores = item['values']
            self.material_seleccionado_entrada = {
                'id': valores[0],
                'codigo': valores[1],
                'nombre': valores[2],
                'stock': valores[4],
                'unidad': valores[5]
            }
            self.label_material_sel_entrada.configure(text=valores[2])
            self.label_stock_entrada.configure(text=f"{valores[4]} {valores[5]}")

    def registrar_entrada(self):
        """Registra una entrada de material"""

        try:
            if not self.material_seleccionado_entrada:
                messagebox.showwarning("Advertencia", "Selecciona un material de la lista")
                return
            
            cantidad = float(self.entry_cantidad_entrada.get())
            if cantidad <= 0:
                messagebox.showwarning("Advertencia", "La cantidad debe ser mayor a 0")
                return

            origen = self.entry_origen.get()
            responsable = self.entry_responsable_entrada.get()
            observaciones = self.text_obs_entrada.get("1.0", "end-1c")

            material_id = self.material_seleccionado_entrada['id']
            cantidad_actual = self.material_seleccionado_entrada['stock']
            nueva_cantidad = cantidad_actual + cantidad
            
            # Actualizar cantidad
            self.cursor.execute("UPDATE materiales SET cantidad_actual = ? WHERE id = ?",
                              (nueva_cantidad, material_id))
            
            # Registrar movimiento
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute('''
                INSERT INTO movimientos (material_id, tipo_movimiento, cantidad, fecha,
                                       responsable, destino_origen, observaciones)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (material_id, 'ENTRADA', cantidad, fecha_actual, responsable, origen, observaciones))
            
            self.conn.commit()
            
            messagebox.showinfo("Éxito", f"Entrada registrada correctamente\n"
                              f"Nueva cantidad: {nueva_cantidad:.2f}")

            # Limpiar campos
            self.entry_cantidad_entrada.delete(0, 'end')
            self.entry_origen.delete(0, 'end')
            self.entry_responsable_entrada.delete(0, 'end')
            self.text_obs_entrada.delete("1.0", "end")
            self.label_material_sel_entrada.configure(text="Ninguno")
            self.label_stock_entrada.configure(text="0")
            self.material_seleccionado_entrada = None

            self.cargar_datos()
            self.filtrar_materiales_entrada()
            self.cargar_historial_entradas()
            
        except ValueError:
            messagebox.showerror("Error", "La cantidad debe ser un número válido")
        except Exception as e:
            messagebox.showerror("Error", f"Error al registrar entrada: {str(e)}")
        
    def filtrar_materiales_salida(self):
        """Filtra los materiales en el tab de salida"""
        for item in self.tree_mat_salida.get_children():
            self.tree_mat_salida.delete(item)

        busqueda = self.entry_buscar_mat_salida.get().lower()
        categoria = self.combo_cat_salida.get()

        query = "SELECT id, codigo, nombre, categoria, cantidad_actual, unidad FROM materiales WHERE 1=1"
        params = []

        if busqueda:
            query += " AND (LOWER(nombre) LIKE ? OR LOWER(codigo) LIKE ?)"
            params.extend([f"%{busqueda}%", f"%{busqueda}%"])

        if categoria != "Todas":
            query += " AND categoria = ?"
            params.append(categoria)

        query += " ORDER BY nombre"

        self.cursor.execute(query, params)
        for row in self.cursor.fetchall():
            self.tree_mat_salida.insert("", "end", values=row)

    def seleccionar_material_salida(self, event):
        """Maneja la selección de un material en salida"""
        seleccion = self.tree_mat_salida.selection()
        if seleccion:
            item = self.tree_mat_salida.item(seleccion[0])
            valores = item['values']
            self.material_seleccionado_salida = {
                'id': valores[0],
                'codigo': valores[1],
                'nombre': valores[2],
                'stock': valores[4],
                'unidad': valores[5]
            }
            self.label_material_sel_salida.configure(text=valores[2])
            self.label_stock_salida.configure(text=f"{valores[4]} {valores[5]}")

    def registrar_salida(self):
        """Registra una salida de material"""

        try:
            if not self.material_seleccionado_salida:
                messagebox.showwarning("Advertencia", "Selecciona un material de la lista")
                return

            cantidad = float(self.entry_cantidad_salida.get())
            if cantidad <= 0:
                messagebox.showwarning("Advertencia", "La cantidad debe ser mayor a 0")
                return

            destino = self.combo_destino.get()
            responsable = self.entry_responsable_salida.get()
            observaciones = self.text_obs_salida.get("1.0", "end-1c")

            material_id = self.material_seleccionado_salida['id']
            cantidad_actual = self.material_seleccionado_salida['stock']

            if cantidad > cantidad_actual:
                messagebox.showerror("Error", 
                                   f"No hay suficiente stock\n"
                                   f"Disponible: {cantidad_actual:.2f}\n"
                                   f"Solicitado: {cantidad:.2f}")
                return
            
            nueva_cantidad = cantidad_actual - cantidad
            
            # Actualizar cantidad
            self.cursor.execute("UPDATE materiales SET cantidad_actual = ? WHERE id = ?",
                              (nueva_cantidad, material_id))
            
            # Registrar movimiento
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute('''
                INSERT INTO movimientos (material_id, tipo_movimiento, cantidad, fecha,
                                       responsable, destino_origen, observaciones)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (material_id, 'SALIDA', cantidad, fecha_actual, responsable, destino, observaciones))
            
            self.conn.commit()
            
            messagebox.showinfo("Éxito", f"Salida registrada correctamente\n"
                              f"Nueva cantidad: {nueva_cantidad:.2f}")

            # Limpiar campos
            self.entry_cantidad_salida.delete(0, 'end')
            self.entry_responsable_salida.delete(0, 'end')
            self.text_obs_salida.delete("1.0", "end")
            self.label_material_sel_salida.configure(text="Ninguno")
            self.label_stock_salida.configure(text="0")
            self.material_seleccionado_salida = None

            self.cargar_datos()
            self.filtrar_materiales_salida()
            self.cargar_historial_salidas()
            
        except ValueError:
            messagebox.showerror("Error", "La cantidad debe ser un número válido")
        except Exception as e:
            messagebox.showerror("Error", f"Error al registrar salida: {str(e)}")
        
    def mostrar_stock_actual_entrada(self):
        """Muestra el stock actual del material seleccionado en entrada"""
        
        material_nombre = self.combo_material_entrada.get().strip()
        
        if not material_nombre:
            self.label_stock_actual_entrada.configure(text="")
            return
        
        self.cursor.execute("SELECT cantidad_actual FROM materiales WHERE nombre = ?", 
                          (material_nombre,))
        resultado = self.cursor.fetchone()
        
        if resultado:
            self.label_stock_actual_entrada.configure(
                text=f"(Stock actual: {resultado[0]:.2f})",
                text_color="#666666"
            )
        else:
            self.label_stock_actual_entrada.configure(text="")
    
    def actualizar_cantidad_desde_seleccion(self):
        """Actualiza la cantidad disponible del material seleccionado/escrito"""
        
        material_nombre = self.combo_material_salida.get().strip()
        
        if not material_nombre:
            self.label_cantidad_disponible.configure(text="0.00", text_color="#1f4788")
            return
        
        # Buscar el material en la base de datos
        self.cursor.execute("SELECT cantidad_actual FROM materiales WHERE nombre = ?", 
                          (material_nombre,))
        resultado = self.cursor.fetchone()
        
        if resultado:
            cantidad = resultado[0]
            # Cambiar color según cantidad
            if cantidad > 0:
                color = "#2fa72f"  # Verde
            else:
                color = "#d32f2f"  # Rojo
            self.label_cantidad_disponible.configure(text=f"{cantidad:.2f}", text_color=color)
        else:
            # Material no encontrado - buscar coincidencias parciales
            self.cursor.execute("""
                SELECT nombre, cantidad_actual FROM materiales 
                WHERE nombre LIKE ? 
                ORDER BY nombre 
                LIMIT 1
            """, (f"%{material_nombre}%",))
            
            resultado_parcial = self.cursor.fetchone()
            if resultado_parcial:
                messagebox.showinfo("Sugerencia", 
                                  f"No se encontró '{material_nombre}'\n\n"
                                  f"¿Quisiste decir: '{resultado_parcial[0]}'?\n"
                                  f"Cantidad disponible: {resultado_parcial[1]:.2f}")
                self.combo_material_salida.delete(0, 'end')
                self.combo_material_salida.insert(0, resultado_parcial[0])
                self.label_cantidad_disponible.configure(text=f"{resultado_parcial[1]:.2f}", 
                                                        text_color="#2fa72f")
            else:
                self.label_cantidad_disponible.configure(text="0.00", text_color="#d32f2f")
                messagebox.showwarning("Advertencia", 
                                     f"Material '{material_nombre}' no encontrado\n\n"
                                     "Asegúrate de seleccionar de la lista o escribe el nombre exacto")
    
    def actualizar_cantidad_disponible(self, event):
        """Método legacy - redirige al nuevo método"""
        self.actualizar_cantidad_desde_seleccion()
        
    def filtrar_materiales_prestamo(self):
        """Filtra los materiales en el tab de préstamos"""
        for item in self.tree_mat_prestamo.get_children():
            self.tree_mat_prestamo.delete(item)

        busqueda = self.entry_buscar_mat_prestamo.get().lower()
        categoria = self.combo_cat_prestamo.get()

        query = "SELECT id, codigo, nombre, categoria, cantidad_actual, unidad FROM materiales WHERE 1=1"
        params = []

        if busqueda:
            query += " AND (LOWER(nombre) LIKE ? OR LOWER(codigo) LIKE ?)"
            params.extend([f"%{busqueda}%", f"%{busqueda}%"])

        if categoria != "Todas":
            query += " AND categoria = ?"
            params.append(categoria)

        query += " ORDER BY nombre"

        self.cursor.execute(query, params)
        for row in self.cursor.fetchall():
            self.tree_mat_prestamo.insert("", "end", values=row)

    def seleccionar_material_prestamo(self, event):
        """Maneja la selección de un material en préstamos"""
        seleccion = self.tree_mat_prestamo.selection()
        if seleccion:
            item = self.tree_mat_prestamo.item(seleccion[0])
            valores = item['values']
            self.material_seleccionado_prestamo = {
                'id': valores[0],
                'codigo': valores[1],
                'nombre': valores[2],
                'stock': valores[4],
                'unidad': valores[5]
            }
            self.label_material_sel_prestamo.configure(text=valores[2])
            self.label_stock_prestamo.configure(text=f"{valores[4]} {valores[5]}")

    def registrar_prestamo(self):
        """Registra un préstamo de material"""

        try:
            if not self.material_seleccionado_prestamo:
                messagebox.showwarning("Advertencia", "Selecciona un material de la lista")
                return

            cantidad = float(self.entry_cantidad_prestamo.get())
            prestado_a = self.entry_prestado_a.get()
            area = self.entry_area_prestamo.get()
            observaciones = self.text_obs_prestamo.get("1.0", "end-1c")

            if not prestado_a:
                messagebox.showwarning("Advertencia", "Indica a quién se presta el material")
                return

            material_id = self.material_seleccionado_prestamo['id']
            cantidad_actual = self.material_seleccionado_prestamo['stock']

            if cantidad > cantidad_actual:
                messagebox.showerror("Error", "No hay suficiente stock disponible")
                return

            # Reducir stock
            nueva_cantidad = cantidad_actual - cantidad
            self.cursor.execute("UPDATE materiales SET cantidad_actual = ? WHERE id = ?",
                              (nueva_cantidad, material_id))
            
            # Registrar préstamo
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute('''
                INSERT INTO prestamos (material_id, cantidad, fecha_prestamo, prestado_a,
                                     area_destino, estado, observaciones)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (material_id, cantidad, fecha_actual, prestado_a, area, 'ACTIVO', observaciones))
            
            # Registrar movimiento
            self.cursor.execute('''
                INSERT INTO movimientos (material_id, tipo_movimiento, cantidad, fecha,
                                       responsable, destino_origen, observaciones)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (material_id, 'PRÉSTAMO', cantidad, fecha_actual, prestado_a, area, observaciones))
            
            self.conn.commit()
            
            messagebox.showinfo("Éxito", "Préstamo registrado correctamente")

            # Limpiar campos
            self.entry_cantidad_prestamo.delete(0, 'end')
            self.entry_prestado_a.delete(0, 'end')
            self.entry_area_prestamo.delete(0, 'end')
            self.text_obs_prestamo.delete("1.0", "end")
            self.label_material_sel_prestamo.configure(text="Ninguno")
            self.label_stock_prestamo.configure(text="0")
            self.material_seleccionado_prestamo = None

            self.cargar_datos()
            self.filtrar_materiales_prestamo()
            self.cargar_prestamos()
            
        except ValueError:
            messagebox.showerror("Error", "La cantidad debe ser un número válido")
        except Exception as e:
            messagebox.showerror("Error", f"Error al registrar préstamo: {str(e)}")
        
    def cargar_prestamos(self):
        """Carga la lista de préstamos con filtros"""

        for item in self.tree_prestamos.get_children():
            self.tree_prestamos.delete(item)

        query = '''
            SELECT p.id, m.nombre, p.cantidad, p.prestado_a, p.area_destino,
                   p.fecha_prestamo, p.estado
            FROM prestamos p
            JOIN materiales m ON p.material_id = m.id
            WHERE 1=1
        '''
        params = []

        # Filtro de estado
        if self.filtro_estado_prestamo.get() == "Activo":
            query += " AND p.estado = 'ACTIVO'"
        elif self.filtro_estado_prestamo.get() == "Devuelto":
            query += " AND p.estado = 'DEVUELTO'"

        # Filtro de búsqueda
        if self.busqueda_prestamo_var.get():
            query += " AND (m.nombre LIKE ? OR p.prestado_a LIKE ? OR p.area_destino LIKE ?)"
            search_term = f"%{self.busqueda_prestamo_var.get()}%"
            params.extend([search_term, search_term, search_term])

        query += " ORDER BY p.fecha_prestamo DESC"

        self.cursor.execute(query, params)
        for row in self.cursor.fetchall():
            self.tree_prestamos.insert("", "end", values=row)
        
    def registrar_devolucion(self):
        """Registra la devolución de un préstamo"""
        
        seleccion = self.tree_prestamos.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona un préstamo")
            return
        
        item = self.tree_prestamos.item(seleccion[0])
        prestamo_id = item['values'][0]
        material_nombre = item['values'][1]
        cantidad = float(item['values'][2])
        
        respuesta = messagebox.askyesno("Confirmar Devolución",
                                       f"¿Confirmar devolución de:\n"
                                       f"{material_nombre}\n"
                                       f"Cantidad: {cantidad:.2f}?")
        
        if respuesta:
            try:
                # Obtener material_id
                self.cursor.execute("SELECT id, cantidad_actual FROM materiales WHERE nombre = ?",
                                  (material_nombre,))
                material_id, cantidad_actual = self.cursor.fetchone()
                
                # Actualizar stock
                nueva_cantidad = cantidad_actual + cantidad
                self.cursor.execute("UPDATE materiales SET cantidad_actual = ? WHERE id = ?",
                                  (nueva_cantidad, material_id))
                
                # Actualizar préstamo
                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.cursor.execute('''
                    UPDATE prestamos 
                    SET estado = 'DEVUELTO', fecha_devolucion = ?
                    WHERE id = ?
                ''', (fecha_actual, prestamo_id))
                
                # Registrar movimiento
                self.cursor.execute('''
                    INSERT INTO movimientos (material_id, tipo_movimiento, cantidad, fecha,
                                           responsable, destino_origen, observaciones)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (material_id, 'DEVOLUCIÓN', cantidad, fecha_actual, 
                     'Sistema', 'Devolución de préstamo', f'Préstamo ID: {prestamo_id}'))
                
                self.conn.commit()
                
                messagebox.showinfo("Éxito", "Devolución registrada correctamente")
                self.cargar_datos()
                self.cargar_prestamos()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al registrar devolución: {str(e)}")
        
    def filtrar_materiales_uso(self):
        """Filtra los materiales en el tab de material en uso"""
        for item in self.tree_mat_uso.get_children():
            self.tree_mat_uso.delete(item)

        busqueda = self.entry_buscar_mat_uso.get().lower()
        categoria = self.combo_cat_uso.get()

        query = "SELECT id, codigo, nombre, categoria, cantidad_actual, unidad FROM materiales WHERE 1=1"
        params = []

        if busqueda:
            query += " AND (LOWER(nombre) LIKE ? OR LOWER(codigo) LIKE ?)"
            params.extend([f"%{busqueda}%", f"%{busqueda}%"])

        if categoria != "Todas":
            query += " AND categoria = ?"
            params.append(categoria)

        query += " ORDER BY nombre"

        self.cursor.execute(query, params)
        for row in self.cursor.fetchall():
            self.tree_mat_uso.insert("", "end", values=row)

    def seleccionar_material_uso(self, event):
        """Maneja la selección de un material en uso"""
        seleccion = self.tree_mat_uso.selection()
        if seleccion:
            item = self.tree_mat_uso.item(seleccion[0])
            valores = item['values']
            self.material_seleccionado_uso = {
                'id': valores[0],
                'codigo': valores[1],
                'nombre': valores[2],
                'stock': valores[4],
                'unidad': valores[5]
            }
            self.label_material_sel_uso.configure(text=valores[2])
            self.label_stock_uso.configure(text=f"{valores[4]} {valores[5]}")

    def registrar_material_uso(self):
        """Registra material puesto en uso"""

        try:
            if not self.material_seleccionado_uso:
                messagebox.showwarning("Advertencia", "Selecciona un material de la lista")
                return

            cantidad = float(self.entry_cantidad_uso.get())
            equipo = self.entry_equipo_uso.get()
            responsable = self.entry_responsable_uso.get()
            observaciones = self.text_obs_uso.get("1.0", "end-1c")

            if not equipo:
                messagebox.showwarning("Advertencia", "Indica el equipo o instalación")
                return

            material_id = self.material_seleccionado_uso['id']
            cantidad_actual = self.material_seleccionado_uso['stock']

            if cantidad > cantidad_actual:
                messagebox.showerror("Error", "No hay suficiente stock disponible")
                return

            # Reducir stock
            nueva_cantidad = cantidad_actual - cantidad
            self.cursor.execute("UPDATE materiales SET cantidad_actual = ? WHERE id = ?",
                              (nueva_cantidad, material_id))
            
            # Registrar material en uso
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute('''
                INSERT INTO material_en_uso (material_id, cantidad, equipo_instalacion,
                                            fecha_instalacion, responsable, observaciones)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (material_id, cantidad, equipo, fecha_actual, responsable, observaciones))
            
            # Registrar movimiento
            self.cursor.execute('''
                INSERT INTO movimientos (material_id, tipo_movimiento, cantidad, fecha,
                                       responsable, destino_origen, observaciones)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (material_id, 'EN USO', cantidad, fecha_actual, responsable, equipo, observaciones))
            
            self.conn.commit()
            
            messagebox.showinfo("Éxito", "Material en uso registrado correctamente")

            # Limpiar campos
            self.entry_cantidad_uso.delete(0, 'end')
            self.entry_equipo_uso.delete(0, 'end')
            self.entry_responsable_uso.delete(0, 'end')
            self.text_obs_uso.delete("1.0", "end")
            self.label_material_sel_uso.configure(text="Ninguno")
            self.label_stock_uso.configure(text="0")
            self.material_seleccionado_uso = None

            self.cargar_datos()
            self.filtrar_materiales_uso()
            self.cargar_material_en_uso()
            
        except ValueError:
            messagebox.showerror("Error", "La cantidad debe ser un número válido")
        except Exception as e:
            messagebox.showerror("Error", f"Error al registrar: {str(e)}")
        
    def cargar_material_en_uso(self):
        """Carga la lista de material en uso con filtros"""

        for item in self.tree_en_uso.get_children():
            self.tree_en_uso.delete(item)

        query = '''
            SELECT u.id, m.nombre, u.cantidad, u.equipo_instalacion,
                   u.fecha_instalacion, u.responsable
            FROM material_en_uso u
            JOIN materiales m ON u.material_id = m.id
            WHERE 1=1
        '''
        params = []

        # Filtro de búsqueda
        if self.busqueda_uso_var.get():
            query += " AND (m.nombre LIKE ? OR u.equipo_instalacion LIKE ? OR u.responsable LIKE ?)"
            search_term = f"%{self.busqueda_uso_var.get()}%"
            params.extend([search_term, search_term, search_term])

        query += " ORDER BY u.fecha_instalacion DESC"

        self.cursor.execute(query, params)
        for row in self.cursor.fetchall():
            self.tree_en_uso.insert("", "end", values=row)
        
    def dar_baja_material_uso(self):
        """Da de baja material en uso"""
        
        seleccion = self.tree_en_uso.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona un registro")
            return
        
        item = self.tree_en_uso.item(seleccion[0])
        uso_id = item['values'][0]
        
        respuesta = messagebox.askyesno("Confirmar", 
                                       "¿Dar de baja este registro?\n"
                                       "El material no regresará al inventario.")
        
        if respuesta:
            try:
                self.cursor.execute("DELETE FROM material_en_uso WHERE id = ?", (uso_id,))
                self.conn.commit()
                
                messagebox.showinfo("Éxito", "Registro dado de baja")
                self.cargar_material_en_uso()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error: {str(e)}")
        
    def cargar_historial_entradas(self):
        """Carga el historial de entradas con filtros"""

        for item in self.tree_entradas.get_children():
            self.tree_entradas.delete(item)

        query = '''
            SELECT m.fecha, mat.nombre, m.cantidad, m.destino_origen, m.responsable
            FROM movimientos m
            JOIN materiales mat ON m.material_id = mat.id
            WHERE m.tipo_movimiento = 'ENTRADA'
        '''
        params = []

        # Filtro de búsqueda
        if self.busqueda_entrada_var.get():
            query += " AND (mat.nombre LIKE ? OR m.destino_origen LIKE ? OR m.responsable LIKE ?)"
            search_term = f"%{self.busqueda_entrada_var.get()}%"
            params.extend([search_term, search_term, search_term])

        query += " ORDER BY m.fecha DESC LIMIT 50"

        self.cursor.execute(query, params)
        for row in self.cursor.fetchall():
            self.tree_entradas.insert("", "end", values=row)

    def cargar_historial_salidas(self):
        """Carga el historial de salidas con filtros"""

        for item in self.tree_salidas.get_children():
            self.tree_salidas.delete(item)

        query = '''
            SELECT m.fecha, mat.nombre, m.cantidad, m.destino_origen, m.responsable
            FROM movimientos m
            JOIN materiales mat ON m.material_id = mat.id
            WHERE m.tipo_movimiento = 'SALIDA'
        '''
        params = []

        # Filtro de búsqueda
        if self.busqueda_salida_var.get():
            query += " AND (mat.nombre LIKE ? OR m.destino_origen LIKE ? OR m.responsable LIKE ?)"
            search_term = f"%{self.busqueda_salida_var.get()}%"
            params.extend([search_term, search_term, search_term])

        query += " ORDER BY m.fecha DESC LIMIT 50"

        self.cursor.execute(query, params)
        for row in self.cursor.fetchall():
            self.tree_salidas.insert("", "end", values=row)

    def cargar_historial_movimientos(self):
        """Carga el historial de movimientos recientes"""
        self.cargar_historial_entradas()
        self.cargar_historial_salidas()
        
    def exportar_reporte(self, tipo):
        """Exporta reportes a Excel"""
        
        try:
            if tipo == "inventario":
                self.cursor.execute("SELECT * FROM materiales")
                df = pd.DataFrame(self.cursor.fetchall(), 
                                columns=['ID', 'Código', 'Nombre', 'Descripción', 'Categoría',
                                        'Unidad', 'Cantidad', 'Stock Mín', 'Ubicación', 
                                        'Costo Unit', 'Fecha Registro', 'Notas'])
                filename = f"Inventario_PTAR_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                
            elif tipo == "stock_bajo":
                self.cursor.execute('''
                    SELECT codigo, nombre, categoria, cantidad_actual, stock_minimo, ubicacion
                    FROM materiales 
                    WHERE cantidad_actual <= stock_minimo
                    ORDER BY cantidad_actual ASC
                ''')
                df = pd.DataFrame(self.cursor.fetchall(),
                                columns=['Código', 'Nombre', 'Categoría', 'Cantidad', 
                                        'Stock Mín', 'Ubicación'])
                filename = f"Stock_Bajo_PTAR_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                
            elif tipo == "movimientos":
                self.cursor.execute('''
                    SELECT m.fecha, mat.nombre, m.tipo_movimiento, m.cantidad, 
                           m.responsable, m.destino_origen, m.observaciones
                    FROM movimientos m
                    JOIN materiales mat ON m.material_id = mat.id
                    WHERE m.fecha >= date('now', '-30 days')
                    ORDER BY m.fecha DESC
                ''')
                df = pd.DataFrame(self.cursor.fetchall(),
                                columns=['Fecha', 'Material', 'Tipo', 'Cantidad',
                                        'Responsable', 'Destino/Origen', 'Observaciones'])
                filename = f"Movimientos_PTAR_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                
            elif tipo == "prestamos":
                self.cursor.execute('''
                    SELECT p.fecha_prestamo, m.nombre, p.cantidad, p.prestado_a,
                           p.area_destino, p.estado, p.fecha_devolucion
                    FROM prestamos p
                    JOIN materiales m ON p.material_id = m.id
                    ORDER BY p.fecha_prestamo DESC
                ''')
                df = pd.DataFrame(self.cursor.fetchall(),
                                columns=['Fecha Préstamo', 'Material', 'Cantidad', 'Prestado a',
                                        'Área', 'Estado', 'Fecha Devolución'])
                filename = f"Prestamos_PTAR_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                
            elif tipo == "en_uso":
                self.cursor.execute('''
                    SELECT u.fecha_instalacion, m.nombre, u.cantidad, u.equipo_instalacion,
                           u.responsable, u.observaciones
                    FROM material_en_uso u
                    JOIN materiales m ON u.material_id = m.id
                    ORDER BY u.fecha_instalacion DESC
                ''')
                df = pd.DataFrame(self.cursor.fetchall(),
                                columns=['Fecha Instalación', 'Material', 'Cantidad', 
                                        'Equipo/Instalación', 'Responsable', 'Observaciones'])
                filename = f"Material_En_Uso_PTAR_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            # Guardar archivo
            filepath = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=filename
            )
            
            if filepath:
                df.to_excel(filepath, index=False, sheet_name='Reporte')
                messagebox.showinfo("Éxito", f"Reporte exportado:\n{filepath}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")
        
    def actualizar_estadisticas(self):
        """Actualiza las estadísticas del sistema"""
        
        # Total de materiales
        self.cursor.execute("SELECT COUNT(*) FROM materiales")
        total_materiales = self.cursor.fetchone()[0]
        
        # Materiales con stock bajo
        self.cursor.execute("SELECT COUNT(*) FROM materiales WHERE cantidad_actual <= stock_minimo")
        stock_bajo = self.cursor.fetchone()[0]
        
        # Sin stock
        self.cursor.execute("SELECT COUNT(*) FROM materiales WHERE cantidad_actual = 0")
        sin_stock = self.cursor.fetchone()[0]
        
        # Préstamos activos
        self.cursor.execute("SELECT COUNT(*) FROM prestamos WHERE estado = 'ACTIVO'")
        prestamos_activos = self.cursor.fetchone()[0]
        
        # Material en uso
        self.cursor.execute("SELECT COUNT(*) FROM material_en_uso")
        material_uso = self.cursor.fetchone()[0]
        
        # Movimientos del mes
        self.cursor.execute("""
            SELECT COUNT(*) FROM movimientos 
            WHERE fecha >= date('now', 'start of month')
        """)
        movimientos_mes = self.cursor.fetchone()[0]
        
        # Valor total del inventario
        self.cursor.execute("SELECT SUM(cantidad_actual * costo_unitario) FROM materiales")
        valor_total = self.cursor.fetchone()[0] or 0
        
        texto_stats = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 ESTADÍSTICAS GENERALES

Total de Materiales: {total_materiales}
Materiales con Stock Bajo: {stock_bajo}
Materiales Sin Stock: {sin_stock}

🔄 Préstamos Activos: {prestamos_activos}
🔧 Material en Uso: {material_uso}

📦 Movimientos del Mes: {movimientos_mes}

💰 Valor Total del Inventario: ${valor_total:,.2f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        
        self.label_stats.configure(text=texto_stats)
        
    def ordenar_columna(self, col):
        """Ordena el treeview por la columna seleccionada"""
        # Implementación básica de ordenamiento
        pass
    
    def __del__(self):
        """Cierra la conexión a la base de datos"""
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    root = ctk.CTk()
    app = InventarioPTAR(root)
    root.mainloop()
