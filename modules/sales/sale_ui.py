"""
Módulo de Punto de Venta (POS)
Interfaz principal para realizar ventas
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from config.settings import COLORS, FONTS, SPACING, BUTTON_STYLES, BUSINESS
from utils.validators import validate_positive_integer, validate_stock_availability
from utils.formatters import format_currency, generate_ticket
from datetime import datetime

class SalesModule:
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db = db_manager
        self.cart = []  # Lista de productos en el carrito
        self.selected_customer_id = None
        
        self.create_ui()
        self.load_products()
        self.update_totals()
    
    def create_ui(self):
        """Crea la interfaz del módulo de ventas"""
        
        # ========== HEADER ==========
        header_frame = tk.Frame(self.parent, bg=COLORS['bg_main'])
        header_frame.pack(fill='x', padx=SPACING['lg'], pady=(SPACING['lg'], SPACING['md']))
        
        title = tk.Label(
            header_frame,
            text="💰 Punto de Venta",
            font=(FONTS['family'], FONTS['title'], 'bold'),
            bg=COLORS['bg_main'],
            fg=COLORS['text_primary']
        )
        title.pack(side='left')
        
        # Botón para nuevo cliente rápido
        btn_quick_customer = tk.Button(
            header_frame,
            text="👤 Cliente General",
            command=self.clear_customer,
            **BUTTON_STYLES['secondary']
        )
        btn_quick_customer.pack(side='right', padx=SPACING['sm'])
        
        # ========== CONTENEDOR PRINCIPAL (2 COLUMNAS) ==========
        main_container = tk.Frame(self.parent, bg=COLORS['bg_main'])
        main_container.pack(fill='both', expand=True, padx=SPACING['lg'], pady=SPACING['md'])
        
        # ========== COLUMNA IZQUIERDA: PRODUCTOS ==========
        left_column = tk.Frame(main_container, bg=COLORS['bg_card'])
        left_column.pack(side='left', fill='both', expand=True, padx=(0, SPACING['md']))
        
        # Título
        tk.Label(
            left_column,
            text="Buscar Productos",
            font=(FONTS['family'], FONTS['heading'], 'bold'),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).pack(padx=SPACING['md'], pady=(SPACING['md'], SPACING['sm']))
        
        # Búsqueda
        search_frame = tk.Frame(left_column, bg=COLORS['bg_card'])
        search_frame.pack(fill='x', padx=SPACING['md'], pady=SPACING['sm'])
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.search_products())
        
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=(FONTS['family'], FONTS['body']),
            relief='solid',
            borderwidth=1
        )
        search_entry.pack(fill='x', pady=SPACING['sm'])
        search_entry.focus()
        
        # Listbox de productos
        list_frame = tk.Frame(left_column, bg=COLORS['bg_card'])
        list_frame.pack(fill='both', expand=True, padx=SPACING['md'], pady=SPACING['sm'])
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.products_listbox = tk.Listbox(
            list_frame,
            font=(FONTS['family'], FONTS['body']),
            yscrollcommand=scrollbar.set,
            relief='solid',
            borderwidth=1,
            activestyle='none'
        )
        self.products_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.products_listbox.yview)
        
        # Bind doble click para agregar producto
        self.products_listbox.bind('<Double-Button-1>', lambda e: self.add_to_cart())
        self.products_listbox.bind('<Return>', lambda e: self.add_to_cart())
        
        # Botón agregar
        btn_add = tk.Button(
            left_column,
            text="➕ Agregar al Carrito",
            command=self.add_to_cart,
            **BUTTON_STYLES['primary']
        )
        btn_add.pack(pady=SPACING['md'])
        
        # ========== COLUMNA DERECHA: CARRITO ==========
        right_column = tk.Frame(main_container, bg=COLORS['bg_card'], width=400)
        right_column.pack(side='right', fill='both', padx=(SPACING['md'], 0))
        right_column.pack_propagate(False)
        
        # Título
        tk.Label(
            right_column,
            text="Carrito de Compra",
            font=(FONTS['family'], FONTS['heading'], 'bold'),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).pack(padx=SPACING['md'], pady=(SPACING['md'], SPACING['sm']))
        
        # Tabla del carrito
        cart_frame = tk.Frame(right_column, bg=COLORS['bg_card'])
        cart_frame.pack(fill='both', expand=True, padx=SPACING['md'], pady=SPACING['sm'])
        
        cart_scroll = ttk.Scrollbar(cart_frame)
        cart_scroll.pack(side='right', fill='y')
        
        columns = ('Producto', 'Cant', 'Precio', 'Subtotal')
        self.cart_tree = ttk.Treeview(
            cart_frame,
            columns=columns,
            show='headings',
            yscrollcommand=cart_scroll.set,
            selectmode='browse',
            height=10
        )
        
        self.cart_tree.heading('Producto', text='Producto')
        self.cart_tree.heading('Cant', text='Cant')
        self.cart_tree.heading('Precio', text='Precio')
        self.cart_tree.heading('Subtotal', text='Subtotal')
        
        self.cart_tree.column('Producto', width=150, anchor='w')
        self.cart_tree.column('Cant', width=50, anchor='center')
        self.cart_tree.column('Precio', width=80, anchor='e')
        self.cart_tree.column('Subtotal', width=80, anchor='e')
        
        self.cart_tree.pack(side='left', fill='both', expand=True)
        cart_scroll.config(command=self.cart_tree.yview)
        
        # Botones de carrito
        cart_buttons = tk.Frame(right_column, bg=COLORS['bg_card'])
        cart_buttons.pack(fill='x', padx=SPACING['md'], pady=SPACING['sm'])
        
        btn_remove = tk.Button(
            cart_buttons,
            text="➖ Quitar",
            command=self.remove_from_cart,
            **BUTTON_STYLES['danger']
        )
        btn_remove.pack(side='left', padx=SPACING['sm'])
        
        btn_clear = tk.Button(
            cart_buttons,
            text="🗑️ Vaciar",
            command=self.clear_cart,
            **BUTTON_STYLES['secondary']
        )
        btn_clear.pack(side='left', padx=SPACING['sm'])
        
        # Totales
        totals_frame = tk.Frame(right_column, bg=COLORS['bg_card'])
        totals_frame.pack(fill='x', padx=SPACING['md'], pady=SPACING['md'])
        
        tk.Label(
            totals_frame,
            text="TOTAL:",
            font=(FONTS['family'], FONTS['heading'], 'bold'),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).pack(side='left')
        
        self.total_label = tk.Label(
            totals_frame,
            text="$0.00",
            font=(FONTS['family'], FONTS['title'], 'bold'),
            bg=COLORS['bg_card'],
            fg=COLORS['success']
        )
        self.total_label.pack(side='right')
        
        # Botón finalizar venta (estilo personalizado)
        checkout_style = BUTTON_STYLES['success'].copy()
        checkout_style['font'] = (FONTS['family'], FONTS['heading'], 'bold')
        
        btn_checkout = tk.Button(
            right_column,
            text="✅ FINALIZAR VENTA",
            command=self.show_checkout_dialog,
            **checkout_style
        )
        btn_checkout.pack(fill='x', padx=SPACING['md'], pady=SPACING['md'])
    
    def load_products(self):
        """Carga todos los productos"""
        self.all_products = self.db.get_all_products()
        self.display_products(self.all_products)
    
    def display_products(self, products):
        """Muestra productos en el listbox"""
        self.products_listbox.delete(0, tk.END)
        for product in products:
            display_text = f"{product['name']} - {format_currency(product['price'])} (Stock: {product['stock']})"
            self.products_listbox.insert(tk.END, display_text)
    
    def search_products(self):
        """Filtra productos según búsqueda"""
        search_term = self.search_var.get().lower()
        if not search_term:
            self.display_products(self.all_products)
            return
        
        filtered = [p for p in self.all_products 
                   if search_term in p['name'].lower() 
                   or search_term in (p['barcode'] or '').lower()]
        self.display_products(filtered)
    
    def add_to_cart(self):
        """Agrega producto seleccionado al carrito"""
        selection = self.products_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un producto")
            return
        
        # Obtener índice de la búsqueda actual
        search_term = self.search_var.get().lower()
        if search_term:
            filtered = [p for p in self.all_products 
                       if search_term in p['name'].lower() 
                       or search_term in (p['barcode'] or '').lower()]
            product = filtered[selection[0]]
        else:
            product = self.all_products[selection[0]]
        
        # Verificar si ya está en el carrito
        for item in self.cart:
            if item['product_id'] == product['id']:
                # Incrementar cantidad
                if item['quantity'] >= product['stock']:
                    messagebox.showwarning("Stock", f"Stock máximo alcanzado: {product['stock']}")
                    return
                item['quantity'] += 1
                item['subtotal'] = item['quantity'] * item['unit_price']
                self.update_cart_display()
                return
        
        # Verificar stock
        if product['stock'] <= 0:
            messagebox.showwarning("Stock", "Producto sin stock disponible")
            return
        
        # Agregar nuevo producto al carrito
        cart_item = {
            'product_id': product['id'],
            'name': product['name'],
            'unit_price': product['price'],
            'quantity': 1,
            'subtotal': product['price'],
            'max_stock': product['stock']
        }
        self.cart.append(cart_item)
        self.update_cart_display()
    
    def remove_from_cart(self):
        """Quita producto seleccionado del carrito"""
        selection = self.cart_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un producto del carrito")
            return
        
        item = self.cart_tree.item(selection[0])
        product_name = item['values'][0]
        
        # Buscar y remover del carrito
        self.cart = [item for item in self.cart if item['name'] != product_name]
        self.update_cart_display()
    
    def clear_cart(self):
        """Vacía el carrito completo"""
        if not self.cart:
            return
        
        response = messagebox.askyesno("Confirmar", "¿Vaciar el carrito?")
        if response:
            self.cart = []
            self.update_cart_display()
    
    def update_cart_display(self):
        """Actualiza la visualización del carrito"""
        # Limpiar tabla
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        # Insertar items
        for item in self.cart:
            self.cart_tree.insert('', 'end', values=(
                item['name'],
                item['quantity'],
                format_currency(item['unit_price']),
                format_currency(item['subtotal'])
            ))
        
        self.update_totals()
    
    def update_totals(self):
        """Actualiza el total de la venta"""
        total = sum(item['subtotal'] for item in self.cart)
        self.total_label.config(text=format_currency(total))
    
    def clear_customer(self):
        """Limpia el cliente seleccionado"""
        self.selected_customer_id = None
    
    def show_checkout_dialog(self):
        """Muestra diálogo para finalizar la venta"""
        if not self.cart:
            messagebox.showwarning("Carrito Vacío", "Agregue productos al carrito")
            return
        
        dialog = tk.Toplevel(self.parent)
        dialog.title("Finalizar Venta")
        dialog.geometry("500x650")
        dialog.resizable(False, False)
        dialog.configure(bg=COLORS['bg_card'])
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Calcular total
        total = sum(item['subtotal'] for item in self.cart)
        
        # ========== RESUMEN ==========
        summary_frame = tk.Frame(dialog, bg=COLORS['bg_card'], padx=SPACING['lg'], pady=SPACING['lg'])
        summary_frame.pack(fill='x')
        
        tk.Label(
            summary_frame,
            text="Resumen de Venta",
            font=(FONTS['family'], FONTS['heading'], 'bold'),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).pack(anchor='w', pady=(0, SPACING['md']))
        
        tk.Label(
            summary_frame,
            text=f"Total a Pagar: {format_currency(total)}",
            font=(FONTS['family'], FONTS['subtitle'], 'bold'),
            bg=COLORS['bg_card'],
            fg=COLORS['success']
        ).pack(anchor='w')
        
        # ========== TIPO DE VENTA ==========
        sale_type_frame = tk.Frame(dialog, bg=COLORS['bg_card'], padx=SPACING['lg'], pady=SPACING['md'])
        sale_type_frame.pack(fill='x')
        
        tk.Label(
            sale_type_frame,
            text="Tipo de Venta*",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).pack(anchor='w', pady=(0, 5))
        
        sale_type_var = tk.StringVar(value="cash")
        
        tk.Radiobutton(
            sale_type_frame,
            text="💵 Venta al Contado",
            variable=sale_type_var,
            value="cash",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary'],
            selectcolor=COLORS['bg_card'],
            command=lambda: toggle_credit_options()
        ).pack(anchor='w')
        
        tk.Radiobutton(
            sale_type_frame,
            text="💳 Venta a Crédito",
            variable=sale_type_var,
            value="credit",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary'],
            selectcolor=COLORS['bg_card'],
            command=lambda: toggle_credit_options()
        ).pack(anchor='w', pady=(5, 0))
        
        # ========== OPCIONES DE CONTADO ==========
        cash_frame = tk.Frame(dialog, bg=COLORS['bg_card'], padx=SPACING['lg'], pady=SPACING['md'])
        cash_frame.pack(fill='x')
        
        # Método de pago
        tk.Label(
            cash_frame,
            text="Método de Pago*",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).grid(row=0, column=0, sticky='w', pady=(0, 5))
        
        payment_var = tk.StringVar(value="Efectivo")
        payment_options = ["Efectivo", "Tarjeta de Crédito", "Tarjeta de Débito", "Transferencia"]
        
        payment_combo = ttk.Combobox(
            cash_frame,
            textvariable=payment_var,
            values=payment_options,
            state='readonly',
            font=(FONTS['family'], FONTS['body']),
            width=25
        )
        payment_combo.grid(row=1, column=0, pady=(0, SPACING['md']))
        
        # Monto pagado
        tk.Label(
            cash_frame,
            text="Monto Pagado*",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).grid(row=2, column=0, sticky='w', pady=(0, 5))
        
        entry_paid = tk.Entry(
            cash_frame,
            font=(FONTS['family'], FONTS['body']),
            width=27
        )
        entry_paid.grid(row=3, column=0, pady=(0, SPACING['md']))
        entry_paid.insert(0, str(int(total)))
        
        # Cambio
        tk.Label(
            cash_frame,
            text="Cambio:",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).grid(row=4, column=0, sticky='w', pady=(0, 5))
        
        change_label = tk.Label(
            cash_frame,
            text="₲0",
            font=(FONTS['family'], FONTS['heading'], 'bold'),
            bg=COLORS['bg_card'],
            fg=COLORS['success']
        )
        change_label.grid(row=5, column=0, sticky='w')
        
        def calculate_change(*args):
            """Calcula el cambio en tiempo real"""
            try:
                paid = float(entry_paid.get())
                change = paid - total
                if change < 0:
                    change_label.config(text="INSUFICIENTE", fg=COLORS['danger'])
                else:
                    change_label.config(text=format_currency(change), fg=COLORS['success'])
            except:
                change_label.config(text="₲0", fg=COLORS['text_secondary'])
        
        entry_paid.bind('<KeyRelease>', calculate_change)
        calculate_change()
        
        # ========== OPCIONES DE CRÉDITO ==========
        credit_frame = tk.Frame(dialog, bg=COLORS['bg_card'], padx=SPACING['lg'], pady=SPACING['md'])
        
        # Cliente (requerido para crédito)
        tk.Label(
            credit_frame,
            text="Cliente*",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).grid(row=0, column=0, sticky='w', pady=(0, 5))
        
        customers = self.db.get_all_customers()
        customer_names = [f"{c['id']} - {c['name']}" for c in customers]
        
        customer_var = tk.StringVar()
        customer_combo = ttk.Combobox(
            credit_frame,
            textvariable=customer_var,
            values=customer_names,
            font=(FONTS['family'], FONTS['body']),
            width=25
        )
        customer_combo.grid(row=1, column=0, pady=(0, SPACING['md']))
        
        # Cuota inicial
        tk.Label(
            credit_frame,
            text="Cuota Inicial*",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).grid(row=2, column=0, sticky='w', pady=(0, 5))
        
        entry_down_payment = tk.Entry(
            credit_frame,
            font=(FONTS['family'], FONTS['body']),
            width=27
        )
        entry_down_payment.grid(row=3, column=0, pady=(0, SPACING['md']))
        min_down = int(total * 0.1)
        entry_down_payment.insert(0, str(min_down))
        
        # Frecuencia de pago
        tk.Label(
            credit_frame,
            text="Frecuencia de Pago*",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).grid(row=4, column=0, sticky='w', pady=(0, 5))
        
        from config.settings import CREDIT
        freq_var = tk.StringVar(value="weekly")
        freq_options = [(v['name'], k) for k, v in CREDIT['payment_frequencies'].items()]
        
        freq_frame = tk.Frame(credit_frame, bg=COLORS['bg_card'])
        freq_frame.grid(row=5, column=0, sticky='w', pady=(0, SPACING['md']))
        
        for text, value in freq_options:
            tk.Radiobutton(
                freq_frame,
                text=text,
                variable=freq_var,
                value=value,
                font=(FONTS['family'], FONTS['body']),
                bg=COLORS['bg_card'],
                fg=COLORS['text_primary'],
                selectcolor=COLORS['bg_card']
            ).pack(side='left', padx=(0, SPACING['md']))
        
        # Número de cuotas
        tk.Label(
            credit_frame,
            text="Número de Cuotas*",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).grid(row=6, column=0, sticky='w', pady=(0, 5))
        
        entry_installments = tk.Entry(
            credit_frame,
            font=(FONTS['family'], FONTS['body']),
            width=27
        )
        entry_installments.grid(row=7, column=0, pady=(0, SPACING['md']))
        entry_installments.insert(0, "4")
        
        def toggle_credit_options():
            """Muestra/oculta opciones según tipo de venta"""
            if sale_type_var.get() == "credit":
                cash_frame.pack_forget()
                credit_frame.pack(fill='x', padx=SPACING['lg'], pady=SPACING['md'])
            else:
                credit_frame.pack_forget()
                cash_frame.pack(fill='x', padx=SPACING['lg'], pady=SPACING['md'])
        
        # Mostrar opciones iniciales (contado por defecto)
        toggle_credit_options()
        
        # ========== BOTONES ==========
        buttons_frame = tk.Frame(dialog, bg=COLORS['bg_card'], padx=SPACING['lg'], pady=SPACING['lg'])
        buttons_frame.pack(fill='x')
        
        def finalize_sale():
            """Finaliza la venta (contado o crédito)"""
            try:
                from datetime import datetime, timedelta
                
                if sale_type_var.get() == "cash":
                    # Venta al contado
                    paid = float(entry_paid.get())
                    if paid < total:
                        messagebox.showerror("Error", "El monto pagado es insuficiente")
                        return
                    
                    change = paid - total
                    
                    cart_items = [{
                        'product_id': item['product_id'],
                        'quantity': item['quantity'],
                        'unit_price': item['unit_price'],
                        'subtotal': item['subtotal']
                    } for item in self.cart]
                    
                    sale_id = self.db.create_sale(
                        customer_id=self.selected_customer_id,
                        total=total,
                        payment_method=payment_var.get(),
                        amount_paid=paid,
                        change_amount=change,
                        cart_items=cart_items,
                        is_credit=False
                    )
                    
                    self.show_ticket(sale_id, total, payment_var.get(), paid, change)
                    
                else:
                    # Venta a crédito
                    if not customer_var.get():
                        messagebox.showerror("Error", "Debe seleccionar un cliente para venta a crédito")
                        return
                    
                    customer_id = int(customer_var.get().split(' - ')[0])
                    down_payment = float(entry_down_payment.get())
                    installments = int(entry_installments.get())
                    
                    if down_payment < total * 0.1:
                        messagebox.showerror("Error", f"La cuota inicial debe ser al menos {format_currency(total * 0.1)}")
                        return
                    
                    if installments < 1 or installments > 24:
                        messagebox.showerror("Error", "El número de cuotas debe estar entre 1 y 24")
                        return
                    
                    remaining = total - down_payment
                    installment_amount = remaining / installments
                    
                    # Calcular primera fecha de pago
                    freq_days = CREDIT['payment_frequencies'][freq_var.get()]['days']
                    first_payment_date = (datetime.now() + timedelta(days=freq_days)).strftime('%Y-%m-%d')
                    
                    cart_items = [{
                        'product_id': item['product_id'],
                        'quantity': item['quantity'],
                        'unit_price': item['unit_price'],
                        'subtotal': item['subtotal']
                    } for item in self.cart]
                    
                    # Crear venta
                    sale_id = self.db.create_sale(
                        customer_id=customer_id,
                        total=total,
                        payment_method="Crédito",
                        amount_paid=down_payment,
                        change_amount=0,
                        cart_items=cart_items,
                        is_credit=True
                    )
                    
                    # Crear registro de crédito
                    self.db.create_credit_sale(
                        sale_id=sale_id,
                        customer_id=customer_id,
                        total_amount=total,
                        down_payment=down_payment,
                        payment_frequency=freq_var.get(),
                        installment_amount=installment_amount,
                        total_installments=installments,
                        next_payment_date=first_payment_date
                    )
                    
                    messagebox.showinfo(
                        "Éxito",
                        f"Venta a crédito registrada\n"
                        f"Total: {format_currency(total)}\n"
                        f"Inicial: {format_currency(down_payment)}\n"
                        f"Saldo: {format_currency(remaining)}\n"
                        f"Cuotas: {installments} de {format_currency(installment_amount)}\n"
                        f"Próximo pago: {first_payment_date}"
                    )
                
                self.cart = []
                self.update_cart_display()
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "Ingrese valores numéricos válidos")
            except Exception as e:
                messagebox.showerror("Error", f"Error al procesar venta: {str(e)}")
        
        confirm_style = BUTTON_STYLES['success'].copy()
        
        btn_finalize = tk.Button(
            buttons_frame,
            text="💾 CONFIRMAR VENTA",
            command=finalize_sale,
            **confirm_style
        )
        btn_finalize.pack(side='left', padx=SPACING['sm'])
        
        btn_cancel = tk.Button(
            buttons_frame,
            text="❌ Cancelar",
            command=dialog.destroy,
            **BUTTON_STYLES['secondary']
        )
        btn_cancel.pack(side='left', padx=SPACING['sm'])
    
    def show_ticket(self, sale_id, total, payment_method, amount_paid, change):
        """Muestra el ticket de venta"""
        ticket_window = tk.Toplevel(self.parent)
        ticket_window.title(f"Ticket #{sale_id}")
        ticket_window.geometry("450x600")
        ticket_window.configure(bg=COLORS['bg_card'])
        
        # Generar ticket
        ticket_data = {
            'id': sale_id,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'items': self.cart,
            'total': total,
            'payment_method': payment_method,
            'amount_paid': amount_paid,
            'change': change
        }
        
        ticket_text = generate_ticket(ticket_data, BUSINESS['name'])
        
        # Mostrar ticket
        text_widget = scrolledtext.ScrolledText(
            ticket_window,
            font=('Courier New', 10),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary'],
            padx=SPACING['md'],
            pady=SPACING['md']
        )
        text_widget.pack(fill='both', expand=True, padx=SPACING['lg'], pady=SPACING['lg'])
        text_widget.insert('1.0', ticket_text)
        text_widget.config(state='disabled')
        
        # Botón cerrar
        btn_close = tk.Button(
            ticket_window,
            text="Cerrar",
            command=ticket_window.destroy,
            **BUTTON_STYLES['secondary']
        )
        btn_close.pack(pady=SPACING['md'])