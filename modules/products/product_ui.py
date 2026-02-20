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
        
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side='right', fill='y')
        
        columns = ('ID', 'Nombre', 'Precio', 'Stock', 'Categoría', 'Código')
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            yscrollcommand=scrollbar.set,
            selectmode='browse'
        )
        
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
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if search_term:
            products = self.db.search_products(search_term)
        else:
            products = self.db.get_all_products()
        
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
        """Muestra diálogo para agregar o editar producto"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Nuevo Producto" if mode == 'add' else "Editar Producto")
        dialog.geometry("560x820")
        dialog.update_idletasks()
        _sw = dialog.winfo_screenwidth()
        _sh = dialog.winfo_screenheight()
        dialog.geometry(f"560x820+{(_sw-560)//2}+{(_sh-820)//2}")
        dialog.resizable(False, False)
        dialog.configure(bg=COLORS['bg_card'])
        dialog.transient(self.parent)
        dialog.grab_set()
        
        product_data = None
        if mode == 'edit' and product_id:
            product_data = self.db.get_product_by_id(product_id)
        
        main_container = tk.Frame(dialog, bg=COLORS['bg_card'])
        main_container.pack(fill='both', expand=True)

        # Botones primero para reservar espacio en bottom
        buttons_frame = tk.Frame(main_container, bg=COLORS['bg_card'], padx=SPACING['lg'], pady=SPACING['md'])
        buttons_frame.pack(fill='x', side='bottom')

        form_frame = tk.Frame(main_container, bg=COLORS['bg_card'], padx=SPACING['lg'], pady=SPACING['lg'])
        form_frame.pack(fill='both', expand=True)
        
        tk.Label(
            form_frame,
            text="Nuevo Producto" if mode == 'add' else "Editar Producto",
            font=(FONTS['family'], FONTS['heading'], 'bold'),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).pack(anchor='w', pady=(0, SPACING['lg']))
        
        tk.Label(form_frame, text="Nombre del Producto*", font=(FONTS['family'], FONTS['body']),
                bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 5))
        entry_name = tk.Entry(form_frame, font=(FONTS['family'], FONTS['body']))
        entry_name.pack(fill='x', pady=(0, SPACING['md']))
        if product_data:
            entry_name.insert(0, product_data['name'])
        entry_name.focus()
        
        # ── Precio de Costo ──────────────────────────────────
        tk.Label(form_frame, text="Precio de Costo*",
                font=(FONTS['family'], FONTS['body'], 'bold'),
                bg=COLORS['bg_card'], fg='#d97706').pack(anchor='w', pady=(0, 5))
        entry_cost = tk.Entry(form_frame, font=(FONTS['family'], FONTS['body']))
        entry_cost.pack(fill='x', pady=(0, SPACING['md']))
        if product_data:
            entry_cost.insert(0, str(int(product_data.get('cost', product_data.get('costo', 0)))))
        else:
            entry_cost.insert(0, "0")

        # ── Precio de Venta (calculado o manual) ─────────────
        tk.Label(form_frame, text="Precio Contado (se calcula automaticamente)",
                font=(FONTS['family'], FONTS['body']),
                bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 5))
        entry_price = tk.Entry(form_frame, font=(FONTS['family'], FONTS['body']))
        entry_price.pack(fill='x', pady=(0, SPACING['md']))
        if product_data:
            entry_price.insert(0, str(int(product_data['price'])))
        
        tk.Label(form_frame, text="Stock Inicial", font=(FONTS['family'], FONTS['body']),
                bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 5))
        entry_stock = tk.Entry(form_frame, font=(FONTS['family'], FONTS['body']))
        entry_stock.pack(fill='x', pady=(0, SPACING['md']))
        if product_data:
            entry_stock.insert(0, str(product_data['stock']))
        else:
            entry_stock.insert(0, "0")
        
        tk.Label(form_frame, text="Categoría", font=(FONTS['family'], FONTS['body']),
                bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 5))
        entry_category = tk.Entry(form_frame, font=(FONTS['family'], FONTS['body']))
        entry_category.pack(fill='x', pady=(0, SPACING['md']))
        if product_data:
            entry_category.insert(0, product_data['category'] or '')
        
        tk.Label(form_frame, text="Código de Barras", font=(FONTS['family'], FONTS['body']),
                bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 5))
        entry_barcode = tk.Entry(form_frame, font=(FONTS['family'], FONTS['body']))
        entry_barcode.pack(fill='x', pady=(0, SPACING['md']))
        if product_data:
            entry_barcode.insert(0, product_data['barcode'] or '')

        # ── Tabla precios calculados ──────────────────────────
        tk.Label(form_frame, text="Tabla de Precios por Modalidad",
                font=(FONTS['family'], FONTS['body'], 'bold'),
                bg=COLORS['bg_card'], fg='#2563eb').pack(anchor='w', pady=(SPACING['md'],4))

        cols_p = ("Modalidad", "Ganancia", "Precio Venta", "Cuota")
        tree_prices = ttk.Treeview(form_frame, columns=cols_p, show='headings', height=5)
        for col, w in zip(cols_p, [120, 75, 110, 100]):
            tree_prices.heading(col, text=col)
            tree_prices.column(col, width=w, anchor='center')
        tree_prices.tag_configure('contado', background='#f0fdf4', foreground='#166534')
        tree_prices.tag_configure('credito', background='#eff6ff', foreground='#1e40af')
        tree_prices.pack(fill='x', pady=(0, SPACING['sm']))

        def _update_prices_table(*args):
            try:
                costo_val = float(entry_cost.get().replace(',','').replace('.','') or 0)
            except ValueError:
                return
            for row in tree_prices.get_children():
                tree_prices.delete(row)
            if not costo_val:
                return
            try:
                precios = self.db.calcular_precios_producto(costo_val)
                for p in precios:
                    cuota_txt = f"Gs. {p['cuota_monto']:,.0f}" if p['cuota_monto'] else "-"
                    tag = 'contado' if p['tipo'] == 'contado' else 'credito'
                    tree_prices.insert('', 'end', values=(
                        p['nombre'],
                        f"{p['porcentaje']:.0f}%",
                        f"Gs. {p['precio']:,.0f}",
                        cuota_txt,
                    ), tags=(tag,))
                    # Autocompletar precio contado
                    if p['tipo'] == 'contado' and not entry_price.get():
                        entry_price.delete(0, 'end')
                        entry_price.insert(0, str(int(p['precio'])))
            except Exception:
                pass

        entry_cost.bind('<FocusOut>', _update_prices_table)
        entry_cost.bind('<Return>',   _update_prices_table)

        # Cargar precios si estamos editando
        if product_data and product_data.get('cost', product_data.get('costo', 0)):
            form_frame.after(100, _update_prices_table)

        def save_product():
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
            
            # Obtener costo
            try:
                cost = float(entry_cost.get().replace(',','').replace('.','') or 0)
            except ValueError:
                cost = 0

            try:
                if mode == 'add':
                    self.db.add_product(name, price, stock, category, barcode, costo=cost)
                    messagebox.showinfo("Exito", "Producto agregado correctamente")
                else:
                    self.db.update_product(product_id, name, price, stock, category, barcode, costo=cost)
                    messagebox.showinfo("Exito", "Producto actualizado correctamente")
                
                self.load_products()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {str(e)}")
        
        tk.Button(buttons_frame, text="💾 Guardar", command=save_product,
                 **BUTTON_STYLES['success']).pack(side='left', padx=SPACING['sm'])
        tk.Button(buttons_frame, text="❌ Cancelar", command=dialog.destroy,
                 **BUTTON_STYLES['secondary']).pack(side='left', padx=SPACING['sm'])
    
    def delete_product(self):
        """Elimina el producto seleccionado"""
        if not self.selected_product_id:
            return
        
        response = messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este producto?")
        
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