"""
Módulo de Gestión de Productos
Interfaz de usuario para CRUD de productos
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config.settings import COLORS, FONTS, SPACING, BUTTON_STYLES
from utils.validators import validate_positive_number, validate_positive_integer, validate_required_field
from utils.formatters import format_currency

class ProductModule:
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db = db_manager
        self.selected_product_id = None
        
        self.create_ui()
        self.load_products()
    
    def create_ui(self):
        """Crea la interfaz del módulo de productos"""
        
        # ========== HEADER ==========
        header_frame = tk.Frame(self.parent, bg=COLORS['bg_main'])
        header_frame.pack(fill='x', padx=SPACING['lg'], pady=(SPACING['lg'], SPACING['md']))
        
        title = tk.Label(
            header_frame,
            text="📦 Gestión de Productos",
            font=(FONTS['family'], FONTS['title'], 'bold'),
            bg=COLORS['bg_main'],
            fg=COLORS['text_primary']
        )
        title.pack(side='left')
        
        # ========== BARRA DE BÚSQUEDA Y ACCIONES ==========
        search_frame = tk.Frame(self.parent, bg=COLORS['bg_main'])
        search_frame.pack(fill='x', padx=SPACING['lg'], pady=SPACING['md'])
        
        # Búsqueda
        tk.Label(
            search_frame,
            text="Buscar:",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_main'],
            fg=COLORS['text_primary']
        ).pack(side='left', padx=(0, SPACING['sm']))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.search_products())
        
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=(FONTS['family'], FONTS['body']),
            width=30,
            relief='solid',
            borderwidth=1
        )
        search_entry.pack(side='left', padx=SPACING['sm'])
        
        # Botón Nuevo Producto
        btn_new = tk.Button(
            search_frame,
            text="➕ Nuevo Producto",
            command=self.show_add_product_dialog,
            **BUTTON_STYLES['primary']
        )
        btn_new.pack(side='right', padx=SPACING['sm'])
        
        # ========== TABLA DE PRODUCTOS ==========
        table_frame = tk.Frame(self.parent, bg=COLORS['bg_card'])
        table_frame.pack(fill='both', expand=True, padx=SPACING['lg'], pady=SPACING['md'])
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Treeview
        columns = ('ID', 'Nombre', 'Precio', 'Stock', 'Categoría', 'Código')
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            yscrollcommand=scrollbar.set,
            selectmode='browse'
        )
        
        # Configurar columnas
        self.tree.heading('ID', text='ID')
        self.tree.heading('Nombre', text='Nombre')
        self.tree.heading('Precio', text='Precio')
        self.tree.heading('Stock', text='Stock')
        self.tree.heading('Categoría', text='Categoría')
        self.tree.heading('Código', text='Código de Barras')
        
        self.tree.column('ID', width=50, anchor='center')
        self.tree.column('Nombre', width=200, anchor='w')
        self.tree.column('Precio', width=100, anchor='e')
        self.tree.column('Stock', width=80, anchor='center')
        self.tree.column('Categoría', width=120, anchor='w')
        self.tree.column('Código', width=120, anchor='w')
        
        self.tree.pack(fill='both', expand=True)
        scrollbar.config(command=self.tree.yview)
        
        # Evento de selección
        self.tree.bind('<<TreeviewSelect>>', self.on_product_select)
        
        # ========== BOTONES DE ACCIÓN ==========
        actions_frame = tk.Frame(self.parent, bg=COLORS['bg_main'])
        actions_frame.pack(fill='x', padx=SPACING['lg'], pady=SPACING['md'])
        
        self.btn_edit = tk.Button(
            actions_frame,
            text="✏️ Editar",
            command=self.show_edit_product_dialog,
            state='disabled',
            **BUTTON_STYLES['secondary']
        )
        self.btn_edit.pack(side='left', padx=SPACING['sm'])
        
        self.btn_delete = tk.Button(
            actions_frame,
            text="🗑️ Eliminar",
            command=self.delete_product,
            state='disabled',
            **BUTTON_STYLES['danger']
        )
        self.btn_delete.pack(side='left', padx=SPACING['sm'])
    
    def load_products(self, search_term=''):
        """Carga los productos en la tabla"""
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Obtener productos
        if search_term:
            products = self.db.search_products(search_term)
        else:
            products = self.db.get_all_products()
        
        # Insertar en tabla
        for product in products:
            self.tree.insert('', 'end', values=(
                product['id'],
                product['name'],
                format_currency(product['price']),
                product['stock'],
                product['category'] or '',
                product['barcode'] or ''
            ))
    
    def search_products(self):
        """Busca productos según el término de búsqueda"""
        search_term = self.search_var.get()
        self.load_products(search_term)
    
    def on_product_select(self, event):
        """Maneja la selección de un producto en la tabla"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            self.selected_product_id = item['values'][0]
            self.btn_edit.config(state='normal')
            self.btn_delete.config(state='normal')
        else:
            self.selected_product_id = None
            self.btn_edit.config(state='disabled')
            self.btn_delete.config(state='disabled')
    
    def show_add_product_dialog(self):
        """Muestra diálogo para agregar producto"""
        self.show_product_dialog(mode='add')
    
    def show_edit_product_dialog(self):
        """Muestra diálogo para editar producto"""
        if not self.selected_product_id:
            return
        self.show_product_dialog(mode='edit', product_id=self.selected_product_id)
    
    def show_product_dialog(self, mode='add', product_id=None):
        """
        Muestra diálogo para agregar o editar producto
        mode: 'add' o 'edit'
        """
        dialog = tk.Toplevel(self.parent)
        dialog.title("Nuevo Producto" if mode == 'add' else "Editar Producto")
        dialog.geometry("450x400")
        dialog.resizable(False, False)
        dialog.configure(bg=COLORS['bg_card'])
        
        # Centrar ventana
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Si es edición, cargar datos del producto
        product_data = None
        if mode == 'edit' and product_id:
            product_data = self.db.get_product_by_id(product_id)
        
        # ========== FORMULARIO ==========
        form_frame = tk.Frame(dialog, bg=COLORS['bg_card'], padx=SPACING['lg'], pady=SPACING['lg'])
        form_frame.pack(fill='both', expand=True)
        
        # Nombre
        tk.Label(
            form_frame,
            text="Nombre del Producto*",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).grid(row=0, column=0, sticky='w', pady=(0, 5))
        
        entry_name = tk.Entry(form_frame, font=(FONTS['family'], FONTS['body']), width=40)
        entry_name.grid(row=1, column=0, pady=(0, SPACING['md']))
        if product_data:
            entry_name.insert(0, product_data['name'])
        
        # Precio
        tk.Label(
            form_frame,
            text="Precio*",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).grid(row=2, column=0, sticky='w', pady=(0, 5))
        
        entry_price = tk.Entry(form_frame, font=(FONTS['family'], FONTS['body']), width=40)
        entry_price.grid(row=3, column=0, pady=(0, SPACING['md']))
        if product_data:
            entry_price.insert(0, str(product_data['price']))
        
        # Stock
        tk.Label(
            form_frame,
            text="Stock Inicial",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).grid(row=4, column=0, sticky='w', pady=(0, 5))
        
        entry_stock = tk.Entry(form_frame, font=(FONTS['family'], FONTS['body']), width=40)
        entry_stock.grid(row=5, column=0, pady=(0, SPACING['md']))
        if product_data:
            entry_stock.insert(0, str(product_data['stock']))
        else:
            entry_stock.insert(0, "0")
        
        # Categoría
        tk.Label(
            form_frame,
            text="Categoría",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).grid(row=6, column=0, sticky='w', pady=(0, 5))
        
        entry_category = tk.Entry(form_frame, font=(FONTS['family'], FONTS['body']), width=40)
        entry_category.grid(row=7, column=0, pady=(0, SPACING['md']))
        if product_data:
            entry_category.insert(0, product_data['category'] or '')
        
        # Código de barras
        tk.Label(
            form_frame,
            text="Código de Barras",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).grid(row=8, column=0, sticky='w', pady=(0, 5))
        
        entry_barcode = tk.Entry(form_frame, font=(FONTS['family'], FONTS['body']), width=40)
        entry_barcode.grid(row=9, column=0, pady=(0, SPACING['lg']))
        if product_data:
            entry_barcode.insert(0, product_data['barcode'] or '')
        
        # ========== BOTONES ==========
        buttons_frame = tk.Frame(form_frame, bg=COLORS['bg_card'])
        buttons_frame.grid(row=10, column=0, pady=SPACING['md'])
        
        def save_product():
            # Validar campos
            is_valid, msg, name = validate_required_field(entry_name.get(), "Nombre")
            if not is_valid:
                messagebox.showerror("Error", msg)
                return
            
            is_valid, msg, price = validate_positive_number(entry_price.get(), "Precio")
            if not is_valid:
                messagebox.showerror("Error", msg)
                return
            
            is_valid, msg, stock = validate_positive_integer(entry_stock.get(), "Stock")
            if not is_valid:
                messagebox.showerror("Error", msg)
                return
            
            category = entry_category.get().strip()
            barcode = entry_barcode.get().strip()
            
            try:
                if mode == 'add':
                    self.db.add_product(name, price, stock, category, barcode)
                    messagebox.showinfo("Éxito", "Producto agregado correctamente")
                else:
                    self.db.update_product(product_id, name, price, stock, category, barcode)
                    messagebox.showinfo("Éxito", "Producto actualizado correctamente")
                
                self.load_products()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {str(e)}")
        
        btn_save = tk.Button(
            buttons_frame,
            text="💾 Guardar",
            command=save_product,
            **BUTTON_STYLES['success']
        )
        btn_save.pack(side='left', padx=SPACING['sm'])
        
        btn_cancel = tk.Button(
            buttons_frame,
            text="❌ Cancelar",
            command=dialog.destroy,
            **BUTTON_STYLES['secondary']
        )
        btn_cancel.pack(side='left', padx=SPACING['sm'])
    
    def delete_product(self):
        """Elimina el producto seleccionado"""
        if not self.selected_product_id:
            return
        
        # Confirmar eliminación
        response = messagebox.askyesno(
            "Confirmar",
            "¿Está seguro de eliminar este producto?"
        )
        
        if response:
            try:
                self.db.delete_product(self.selected_product_id)
                messagebox.showinfo("Éxito", "Producto eliminado correctamente")
                self.load_products()
                self.selected_product_id = None
                self.btn_edit.config(state='disabled')
                self.btn_delete.config(state='disabled')
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar: {str(e)}")