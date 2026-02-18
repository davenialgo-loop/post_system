"""
Módulo de Punto de Venta (POS)
Interfaz principal para realizar ventas
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from config.settings import COLORS, FONTS, SPACING, BUTTON_STYLES, BUSINESS
from utils.formatters import format_currency, generate_ticket
from datetime import datetime

class SalesModule:
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db = db_manager
        self.cart = []
        self.selected_customer_id = None
        
        self.create_ui()
        self.load_products()
        self.update_totals()
    
    def create_ui(self):
        """Crea la interfaz del módulo de ventas"""
        header_frame = tk.Frame(self.parent, bg=COLORS['bg_main'])
        header_frame.pack(fill='x', padx=SPACING['lg'], pady=(SPACING['lg'], SPACING['md']))
        
        title = tk.Label(header_frame, text="💰 Punto de Venta",
                        font=(FONTS['family'], FONTS['title'], 'bold'),
                        bg=COLORS['bg_main'], fg=COLORS['text_primary'])
        title.pack(side='left')
        
        main_container = tk.Frame(self.parent, bg=COLORS['bg_main'])
        main_container.pack(fill='both', expand=True, padx=SPACING['lg'], pady=SPACING['md'])
        
        left_column = tk.Frame(main_container, bg=COLORS['bg_card'])
        left_column.pack(side='left', fill='both', expand=True, padx=(0, SPACING['md']))
        
        tk.Label(left_column, text="Buscar Productos",
                font=(FONTS['family'], FONTS['heading'], 'bold'),
                bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(padx=SPACING['md'], pady=(SPACING['md'], SPACING['sm']))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.search_products())
        
        search_entry = tk.Entry(left_column, textvariable=self.search_var,
                               font=(FONTS['family'], FONTS['body']), relief='solid', borderwidth=1)
        search_entry.pack(fill='x', padx=SPACING['md'], pady=SPACING['sm'])
        search_entry.focus()
        
        list_frame = tk.Frame(left_column, bg=COLORS['bg_card'])
        list_frame.pack(fill='both', expand=True, padx=SPACING['md'], pady=SPACING['sm'])
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.products_listbox = tk.Listbox(list_frame, font=(FONTS['family'], FONTS['body']),
                                           yscrollcommand=scrollbar.set, relief='solid',
                                           borderwidth=1, activestyle='none')
        self.products_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.products_listbox.yview)
        
        self.products_listbox.bind('<Double-Button-1>', lambda e: self.add_to_cart())
        
        tk.Button(left_column, text="➕ Agregar al Carrito", command=self.add_to_cart,
                 **BUTTON_STYLES['primary']).pack(pady=SPACING['md'])
        
        right_column = tk.Frame(main_container, bg=COLORS['bg_card'], width=400)
        right_column.pack(side='right', fill='both', padx=(SPACING['md'], 0))
        right_column.pack_propagate(False)
        
        tk.Label(right_column, text="Carrito de Compra",
                font=(FONTS['family'], FONTS['heading'], 'bold'),
                bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(padx=SPACING['md'], pady=(SPACING['md'], SPACING['sm']))
        
        cart_frame = tk.Frame(right_column, bg=COLORS['bg_card'])
        cart_frame.pack(fill='both', expand=True, padx=SPACING['md'], pady=SPACING['sm'])
        
        cart_scroll = ttk.Scrollbar(cart_frame)
        cart_scroll.pack(side='right', fill='y')
        
        columns = ('Producto', 'Cant', 'Precio', 'Subtotal')
        self.cart_tree = ttk.Treeview(cart_frame, columns=columns, show='headings',
                                      yscrollcommand=cart_scroll.set, selectmode='browse', height=10)
        
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
        
        cart_buttons = tk.Frame(right_column, bg=COLORS['bg_card'])
        cart_buttons.pack(fill='x', padx=SPACING['md'], pady=SPACING['sm'])
        
        tk.Button(cart_buttons, text="➖ Quitar", command=self.remove_from_cart,
                 **BUTTON_STYLES['danger']).pack(side='left', padx=SPACING['sm'])
        tk.Button(cart_buttons, text="🗑️ Vaciar", command=self.clear_cart,
                 **BUTTON_STYLES['secondary']).pack(side='left', padx=SPACING['sm'])
        
        totals_frame = tk.Frame(right_column, bg=COLORS['bg_card'])
        totals_frame.pack(fill='x', padx=SPACING['md'], pady=SPACING['md'])
        
        tk.Label(totals_frame, text="TOTAL:", font=(FONTS['family'], FONTS['heading'], 'bold'),
                bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(side='left')
        
        self.total_label = tk.Label(totals_frame, text="₲0",
                                    font=(FONTS['family'], FONTS['title'], 'bold'),
                                    bg=COLORS['bg_card'], fg=COLORS['success'])
        self.total_label.pack(side='right')
        
        checkout_style = BUTTON_STYLES['success'].copy()
        checkout_style['font'] = (FONTS['family'], FONTS['heading'], 'bold')
        
        tk.Button(right_column, text="✅ FINALIZAR VENTA", command=self.show_checkout_dialog,
                 **checkout_style).pack(fill='x', padx=SPACING['md'], pady=SPACING['md'])
    
    def load_products(self):
        self.all_products = self.db.get_all_products()
        self.display_products(self.all_products)
    
    def display_products(self, products):
        self.products_listbox.delete(0, tk.END)
        for product in products:
            display_text = f"{product['name']} - {format_currency(product['price'])} (Stock: {product['stock']})"
            self.products_listbox.insert(tk.END, display_text)
    
    def search_products(self):
        search_term = self.search_var.get().lower()
        if not search_term:
            self.display_products(self.all_products)
            return
        filtered = [p for p in self.all_products 
                   if search_term in p['name'].lower() or search_term in (p['barcode'] or '').lower()]
        self.display_products(filtered)
    
    def add_to_cart(self):
        selection = self.products_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un producto")
            return
        
        search_term = self.search_var.get().lower()
        if search_term:
            filtered = [p for p in self.all_products 
                       if search_term in p['name'].lower() or search_term in (p['barcode'] or '').lower()]
            product = filtered[selection[0]]
        else:
            product = self.all_products[selection[0]]
        
        for item in self.cart:
            if item['product_id'] == product['id']:
                if item['quantity'] >= product['stock']:
                    messagebox.showwarning("Stock", f"Stock máximo: {product['stock']}")
                    return
                item['quantity'] += 1
                item['subtotal'] = item['quantity'] * item['unit_price']
                self.update_cart_display()
                return
        
        if product['stock'] <= 0:
            messagebox.showwarning("Stock", "Sin stock")
            return
        
        self.cart.append({
            'product_id': product['id'],
            'name': product['name'],
            'unit_price': product['price'],
            'quantity': 1,
            'subtotal': product['price'],
            'max_stock': product['stock']
        })
        self.update_cart_display()
    
    def remove_from_cart(self):
        selection = self.cart_tree.selection()
        if not selection:
            return
        item = self.cart_tree.item(selection[0])
        self.cart = [i for i in self.cart if i['name'] != item['values'][0]]
        self.update_cart_display()
    
    def clear_cart(self):
        if self.cart and messagebox.askyesno("Confirmar", "¿Vaciar carrito?"):
            self.cart = []
            self.update_cart_display()
    
    def update_cart_display(self):
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        for item in self.cart:
            self.cart_tree.insert('', 'end', values=(
                item['name'], item['quantity'],
                format_currency(item['unit_price']),
                format_currency(item['subtotal'])))
        self.update_totals()
    
    def update_totals(self):
        total = sum(item['subtotal'] for item in self.cart)
        self.total_label.config(text=format_currency(total))
    
    def clear_customer(self):
        self.selected_customer_id = None
    
    def show_checkout_dialog(self):
        if not self.cart:
            messagebox.showwarning("Carrito Vacío", "Agregue productos")
            return
        
        dialog = tk.Toplevel(self.parent)
        dialog.title("Finalizar Venta")
        dialog.geometry("520x700")
        dialog.configure(bg='white')
        dialog.transient(self.parent)
        dialog.grab_set()
        
        total = sum(item['subtotal'] for item in self.cart)
        
        # Header
        tk.Label(dialog, text="Resumen de Venta", font=('Segoe UI', 16, 'bold'),
                bg='white').pack(anchor='w', padx=20, pady=(20, 10))
        tk.Label(dialog, text=f"Total: {format_currency(total)}", font=('Segoe UI', 14, 'bold'),
                bg='white', fg='#10b981').pack(anchor='w', padx=20, pady=(0, 10))
        tk.Frame(dialog, bg='#e2e8f0', height=2).pack(fill='x', padx=20, pady=10)
        
        # Tipo venta
        tk.Label(dialog, text="Tipo de Venta*", font=('Segoe UI', 11, 'bold'),
                bg='white').pack(anchor='w', padx=20, pady=(10, 5))
        
        sale_type = tk.StringVar(value="cash")
        radio_frame = tk.Frame(dialog, bg='white')
        radio_frame.pack(fill='x', padx=20)
        
        # Container opciones
        options_container = tk.Frame(dialog, bg='white')
        options_container.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Opciones contado
        cash_frame = tk.Frame(options_container, bg='white')
        tk.Label(cash_frame, text="Método de Pago*", bg='white', font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))
        payment_var = tk.StringVar(value="Efectivo")
        ttk.Combobox(cash_frame, textvariable=payment_var,
                    values=["Efectivo", "Tarjeta Crédito", "Tarjeta Débito", "Transferencia"],
                    state='readonly').pack(fill='x', pady=(0, 10))
        
        tk.Label(cash_frame, text="Monto Pagado*", bg='white', font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))
        entry_paid = tk.Entry(cash_frame, font=('Segoe UI', 11))
        entry_paid.pack(fill='x', pady=(0, 10))
        entry_paid.insert(0, str(int(total)))
        
        tk.Label(cash_frame, text="Cambio:", bg='white', font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))
        change_label = tk.Label(cash_frame, text="₲0", bg='white', font=('Segoe UI', 14, 'bold'), fg='#10b981')
        change_label.pack(anchor='w')
        
        def calc_change(*args):
            try:
                paid = float(entry_paid.get())
                change = paid - total
                change_label.config(text="INSUFICIENTE" if change < 0 else format_currency(change),
                                   fg='#ef4444' if change < 0 else '#10b981')
            except:
                change_label.config(text="₲0")
        entry_paid.bind('<KeyRelease>', calc_change)
        
        # Opciones crédito
        credit_frame = tk.Frame(options_container, bg='white')
        tk.Label(credit_frame, text="Cliente*", bg='white', font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))
        customers = self.db.get_all_customers()
        customer_var = tk.StringVar()
        ttk.Combobox(credit_frame, textvariable=customer_var,
                    values=[f"{c['id']} - {c['name']}" for c in customers]).pack(fill='x', pady=(0, 10))
        
        tk.Label(credit_frame, text=f"Cuota Inicial* (Min {format_currency(int(total*0.1))})",
                bg='white', font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))
        entry_down = tk.Entry(credit_frame, font=('Segoe UI', 11))
        entry_down.pack(fill='x', pady=(0, 10))
        entry_down.insert(0, str(int(total * 0.1)))
        
        tk.Label(credit_frame, text="Frecuencia*", bg='white', font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))
        freq_var = tk.StringVar(value="weekly")
        freq_frame = tk.Frame(credit_frame, bg='white')
        freq_frame.pack(fill='x', pady=(0, 10))
        from config.settings import CREDIT
        for key, val in CREDIT['payment_frequencies'].items():
            tk.Radiobutton(freq_frame, text=val['name'], variable=freq_var, value=key,
                          bg='white', selectcolor='white').pack(side='left', padx=(0, 10))
        
        tk.Label(credit_frame, text="Cuotas* (1-24)", bg='white', font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))
        entry_install = tk.Entry(credit_frame, font=('Segoe UI', 11))
        entry_install.pack(fill='x', pady=(0, 10))
        entry_install.insert(0, "4")
        
        def toggle():
            if sale_type.get() == "credit":
                cash_frame.pack_forget()
                credit_frame.pack(fill='both', expand=True)
            else:
                credit_frame.pack_forget()
                cash_frame.pack(fill='both', expand=True)
        
        tk.Radiobutton(radio_frame, text="💵 Contado", variable=sale_type, value="cash",
                      bg='white', selectcolor='white', command=toggle).pack(anchor='w', pady=2)
        tk.Radiobutton(radio_frame, text="💳 Crédito", variable=sale_type, value="credit",
                      bg='white', selectcolor='white', command=toggle).pack(anchor='w', pady=2)
        
        tk.Frame(dialog, bg='#e2e8f0', height=2).pack(fill='x', padx=20, pady=10)
        
        # Botones
        btn_frame = tk.Frame(dialog, bg='white')
        btn_frame.pack(fill='x', side='bottom', padx=20, pady=20)
        
        def finalize():
            try:
                from datetime import timedelta
                if sale_type.get() == "cash":
                    paid = float(entry_paid.get())
                    if paid < total:
                        messagebox.showerror("Error", "Monto insuficiente")
                        return
                    cart_items = [{'product_id': i['product_id'], 'quantity': i['quantity'],
                                  'unit_price': i['unit_price'], 'subtotal': i['subtotal']} for i in self.cart]
                    sale_id = self.db.create_sale(self.selected_customer_id, total, payment_var.get(),
                                                 paid, paid - total, cart_items, False)
                    self.show_ticket(sale_id, total, payment_var.get(), paid, paid - total)
                    messagebox.showinfo("Éxito", f"Venta #{sale_id}")
                else:
                    if not customer_var.get():
                        messagebox.showerror("Error", "Seleccione cliente")
                        return
                    cust_id = int(customer_var.get().split(' - ')[0])
                    down = float(entry_down.get())
                    inst = int(entry_install.get())
                    if down < total * 0.1:
                        messagebox.showerror("Error", f"Mínimo {format_currency(total*0.1)}")
                        return
                    if not 1 <= inst <= 24:
                        messagebox.showerror("Error", "Cuotas: 1-24")
                        return
                    rem = total - down
                    inst_amt = rem / inst
                    freq_days = CREDIT['payment_frequencies'][freq_var.get()]['days']
                    first_date = (datetime.now() + timedelta(days=freq_days)).strftime('%Y-%m-%d')
                    cart_items = [{'product_id': i['product_id'], 'quantity': i['quantity'],
                                  'unit_price': i['unit_price'], 'subtotal': i['subtotal']} for i in self.cart]
                    sale_id = self.db.create_sale(cust_id, total, "Crédito", down, 0, cart_items, True)
                    self.db.create_credit_sale(sale_id, cust_id, total, down, freq_var.get(),
                                              inst_amt, inst, first_date)
                    messagebox.showinfo("Éxito", f"Crédito registrado\nTotal: {format_currency(total)}\n"
                                       f"Inicial: {format_currency(down)}\nSaldo: {format_currency(rem)}\n"
                                       f"Cuotas: {inst} de {format_currency(inst_amt)}\nPróximo: {first_date}")
                self.cart = []
                self.update_cart_display()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        tk.Button(btn_frame, text="💾 CONFIRMAR", command=finalize, bg='#10b981', fg='white',
                 font=('Segoe UI', 11, 'bold'), relief='flat', padx=20, pady=8).pack(side='left', padx=5)
        tk.Button(btn_frame, text="❌ Cancelar", command=dialog.destroy, bg='#64748b', fg='white',
                 font=('Segoe UI', 11), relief='flat', padx=20, pady=8).pack(side='left', padx=5)
        
        cash_frame.pack(fill='both', expand=True)
        calc_change()
    
    def show_ticket(self, sale_id, total, payment_method, amount_paid, change):
        ticket_window = tk.Toplevel(self.parent)
        ticket_window.title(f"Ticket #{sale_id}")
        ticket_window.geometry("450x600")
        ticket_window.configure(bg='white')
        
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
        
        text_widget = scrolledtext.ScrolledText(ticket_window, font=('Courier New', 10),
                                               bg='white', padx=20, pady=20)
        text_widget.pack(fill='both', expand=True, padx=20, pady=20)
        text_widget.insert('1.0', ticket_text)
        text_widget.config(state='disabled')
        
        tk.Button(ticket_window, text="Cerrar", command=ticket_window.destroy,
                 **BUTTON_STYLES['secondary']).pack(pady=20)