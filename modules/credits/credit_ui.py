"""
Módulo de Gestión de Créditos y Pagos
Interfaz para administrar ventas a crédito y registrar abonos
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config.settings import COLORS, FONTS, SPACING, BUTTON_STYLES, CREDIT
from utils.formatters import format_currency, format_date
from datetime import datetime, timedelta

class CreditsModule:
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db = db_manager
        self.selected_credit_id = None
        
        self.create_ui()
        self.load_credits()
    
    def create_ui(self):
        """Crea la interfaz del módulo de créditos"""
        
        # ========== HEADER ==========
        header_frame = tk.Frame(self.parent, bg=COLORS['bg_main'])
        header_frame.pack(fill='x', padx=SPACING['lg'], pady=(SPACING['lg'], SPACING['md']))
        
        title = tk.Label(
            header_frame,
            text="💳 Gestión de Créditos",
            font=(FONTS['family'], FONTS['title'], 'bold'),
            bg=COLORS['bg_main'],
            fg=COLORS['text_primary']
        )
        title.pack(side='left')
        
        # ========== FILTROS ==========
        filters_frame = tk.Frame(self.parent, bg=COLORS['bg_card'])
        filters_frame.pack(fill='x', padx=SPACING['lg'], pady=SPACING['md'])
        
        filter_inner = tk.Frame(filters_frame, bg=COLORS['bg_card'], padx=SPACING['md'], pady=SPACING['md'])
        filter_inner.pack(fill='x')
        
        tk.Label(
            filter_inner,
            text="Filtrar por estado:",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).pack(side='left', padx=SPACING['sm'])
        
        self.status_var = tk.StringVar(value='all')
        
        status_options = [
            ('Todos', 'all'),
            ('Activos', 'active'),
            ('Pagados', 'paid'),
            ('Vencidos', 'overdue')
        ]
        
        for text, value in status_options:
            rb = tk.Radiobutton(
                filter_inner,
                text=text,
                variable=self.status_var,
                value=value,
                font=(FONTS['family'], FONTS['body']),
                bg=COLORS['bg_card'],
                fg=COLORS['text_primary'],
                selectcolor=COLORS['bg_card'],
                command=self.load_credits
            )
            rb.pack(side='left', padx=SPACING['sm'])
        
        # ========== ESTADÍSTICAS ==========
        stats_frame = tk.Frame(self.parent, bg=COLORS['bg_main'])
        stats_frame.pack(fill='x', padx=SPACING['lg'], pady=SPACING['md'])
        
        self.card_active = self.create_stat_card(stats_frame, "Créditos Activos", "0", COLORS['info'])
        self.card_active.pack(side='left', padx=SPACING['sm'], fill='both', expand=True)
        
        self.card_pending = self.create_stat_card(stats_frame, "Total por Cobrar", "₲0", COLORS['warning'])
        self.card_pending.pack(side='left', padx=SPACING['sm'], fill='both', expand=True)
        
        self.card_overdue = self.create_stat_card(stats_frame, "Vencidos", "0", COLORS['danger'])
        self.card_overdue.pack(side='left', padx=SPACING['sm'], fill='both', expand=True)
        
        # ========== TABLA DE CRÉDITOS ==========
        table_frame = tk.Frame(self.parent, bg=COLORS['bg_card'])
        table_frame.pack(fill='both', expand=True, padx=SPACING['lg'], pady=SPACING['md'])
        
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side='right', fill='y')
        
        columns = ('ID', 'Cliente', 'Total', 'Cuota Inicial', 'Saldo', 'Cuota', 'Pagadas', 'Total Cuotas', 'Próximo Pago', 'Estado')
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            yscrollcommand=scrollbar.set,
            selectmode='browse'
        )
        
        # Configurar columnas
        self.tree.heading('ID', text='ID')
        self.tree.heading('Cliente', text='Cliente')
        self.tree.heading('Total', text='Total')
        self.tree.heading('Cuota Inicial', text='Inicial')
        self.tree.heading('Saldo', text='Saldo')
        self.tree.heading('Cuota', text='Cuota')
        self.tree.heading('Pagadas', text='Pagadas')
        self.tree.heading('Total Cuotas', text='Total')
        self.tree.heading('Próximo Pago', text='Próximo Pago')
        self.tree.heading('Estado', text='Estado')
        
        self.tree.column('ID', width=50, anchor='center')
        self.tree.column('Cliente', width=150, anchor='w')
        self.tree.column('Total', width=100, anchor='e')
        self.tree.column('Cuota Inicial', width=100, anchor='e')
        self.tree.column('Saldo', width=100, anchor='e')
        self.tree.column('Cuota', width=100, anchor='e')
        self.tree.column('Pagadas', width=70, anchor='center')
        self.tree.column('Total Cuotas', width=70, anchor='center')
        self.tree.column('Próximo Pago', width=100, anchor='center')
        self.tree.column('Estado', width=80, anchor='center')
        
        self.tree.pack(fill='both', expand=True)
        scrollbar.config(command=self.tree.yview)
        
        # Evento de selección
        self.tree.bind('<<TreeviewSelect>>', self.on_credit_select)
        self.tree.bind('<Double-Button-1>', lambda e: self.show_credit_details())
        
        # ========== BOTONES DE ACCIÓN ==========
        actions_frame = tk.Frame(self.parent, bg=COLORS['bg_main'])
        actions_frame.pack(fill='x', padx=SPACING['lg'], pady=SPACING['md'])
        
        self.btn_pay = tk.Button(
            actions_frame,
            text="💰 Registrar Pago",
            command=self.show_payment_dialog,
            state='disabled',
            **BUTTON_STYLES['success']
        )
        self.btn_pay.pack(side='left', padx=SPACING['sm'])
        
        self.btn_history = tk.Button(
            actions_frame,
            text="📋 Ver Historial",
            command=self.show_payment_history,
            state='disabled',
            **BUTTON_STYLES['primary']
        )
        self.btn_history.pack(side='left', padx=SPACING['sm'])
        
        self.btn_change_date = tk.Button(
            actions_frame,
            text="📅 Cambiar Fecha",
            command=self.show_change_date_dialog,
            state='disabled',
            **BUTTON_STYLES['secondary']
        )
        self.btn_change_date.pack(side='left', padx=SPACING['sm'])
    
    def create_stat_card(self, parent, title, value, color):
        """Crea una tarjeta de estadística"""
        card = tk.Frame(parent, bg=COLORS['bg_card'], relief='solid', borderwidth=1)
        
        title_label = tk.Label(
            card,
            text=title,
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_secondary']
        )
        title_label.pack(pady=(SPACING['md'], SPACING['sm']))
        
        value_label = tk.Label(
            card,
            text=value,
            font=(FONTS['family'], FONTS['heading'], 'bold'),
            bg=COLORS['bg_card'],
            fg=color
        )
        value_label.pack(pady=(0, SPACING['md']))
        
        card.value_label = value_label
        return card
    
    def load_credits(self):
        """Carga los créditos según el filtro seleccionado"""
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Obtener créditos
        status_filter = self.status_var.get()
        
        if status_filter == 'all':
            credits = self.db.get_all_credit_sales()
        elif status_filter == 'overdue':
            credits = self.db.get_overdue_credits()
        else:
            credits = self.db.get_all_credit_sales(status_filter)
        
        # Calcular estadísticas
        active_count = 0
        total_pending = 0
        overdue_count = 0
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Insertar en tabla
        for credit in credits:
            status_text = 'Activo' if credit['status'] == 'active' else 'Pagado'
            if credit['status'] == 'active' and credit['next_payment_date'] < today:
                status_text = 'Vencido'
                overdue_count += 1
            
            if credit['status'] == 'active':
                active_count += 1
                total_pending += credit['remaining_balance']
            
            self.tree.insert('', 'end', values=(
                credit['id'],
                credit['customer_name'],
                format_currency(credit['total_amount']),
                format_currency(credit['down_payment']),
                format_currency(credit['remaining_balance']),
                format_currency(credit['installment_amount']),
                credit['paid_installments'],
                credit['total_installments'],
                credit['next_payment_date'],
                status_text
            ), tags=(credit['status'],))
        
        # Actualizar estadísticas
        self.card_active.value_label.config(text=str(active_count))
        self.card_pending.value_label.config(text=format_currency(total_pending))
        self.card_overdue.value_label.config(text=str(overdue_count))
        
        # Colorear filas vencidas
        self.tree.tag_configure('active', background='white')
        self.tree.tag_configure('paid', background='#d1fae5')
    
    def on_credit_select(self, event):
        """Maneja la selección de un crédito"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            self.selected_credit_id = item['values'][0]
            
            # Habilitar botones solo si está activo
            status = item['values'][9]
            if status in ['Activo', 'Vencido']:
                self.btn_pay.config(state='normal')
                self.btn_change_date.config(state='normal')
            else:
                self.btn_pay.config(state='disabled')
                self.btn_change_date.config(state='disabled')
            
            self.btn_history.config(state='normal')
        else:
            self.selected_credit_id = None
            self.btn_pay.config(state='disabled')
            self.btn_history.config(state='disabled')
            self.btn_change_date.config(state='disabled')
    
    def show_credit_details(self):
        """Muestra detalles completos del crédito"""
        if not self.selected_credit_id:
            return
        
        credit = self.db.get_credit_sale_by_id(self.selected_credit_id)
        if not credit:
            return
        
        # Crear ventana de detalles
        details_window = tk.Toplevel(self.parent)
        details_window.title(f"Detalles del Crédito #{credit['id']}")
        details_window.geometry("500x400")
        details_window.configure(bg=COLORS['bg_card'])
        details_window.transient(self.parent)
        
        # Contenido
        content = tk.Frame(details_window, bg=COLORS['bg_card'], padx=SPACING['lg'], pady=SPACING['lg'])
        content.pack(fill='both', expand=True)
        
        info = [
            ("Cliente:", credit['customer_name']),
            ("Teléfono:", credit['phone'] or 'N/A'),
            ("Total de la venta:", format_currency(credit['total_amount'])),
            ("Cuota inicial:", format_currency(credit['down_payment'])),
            ("Saldo restante:", format_currency(credit['remaining_balance'])),
            ("Frecuencia de pago:", CREDIT['payment_frequencies'][credit['payment_frequency']]['name']),
            ("Monto de cuota:", format_currency(credit['installment_amount'])),
            ("Cuotas pagadas:", f"{credit['paid_installments']} de {credit['total_installments']}"),
            ("Próximo pago:", credit['next_payment_date']),
            ("Estado:", 'Activo' if credit['status'] == 'active' else 'Pagado'),
        ]
        
        for i, (label, value) in enumerate(info):
            tk.Label(
                content,
                text=label,
                font=(FONTS['family'], FONTS['body'], 'bold'),
                bg=COLORS['bg_card'],
                fg=COLORS['text_primary'],
                anchor='w'
            ).grid(row=i, column=0, sticky='w', pady=5)
            
            tk.Label(
                content,
                text=str(value),
                font=(FONTS['family'], FONTS['body']),
                bg=COLORS['bg_card'],
                fg=COLORS['text_secondary']
            ).grid(row=i, column=1, sticky='w', padx=SPACING['md'], pady=5)
    
    def show_payment_dialog(self):
        """Muestra diálogo para registrar un pago"""
        if not self.selected_credit_id:
            return
        
        credit = self.db.get_credit_sale_by_id(self.selected_credit_id)
        if not credit:
            return
        
        dialog = tk.Toplevel(self.parent)
        dialog.title("Registrar Pago")
        dialog.geometry("400x350")
        dialog.configure(bg=COLORS['bg_card'])
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Contenido
        form_frame = tk.Frame(dialog, bg=COLORS['bg_card'], padx=SPACING['lg'], pady=SPACING['lg'])
        form_frame.pack(fill='both', expand=True)
        
        # Información del crédito
        tk.Label(
            form_frame,
            text=f"Cliente: {credit['customer_name']}",
            font=(FONTS['family'], FONTS['heading'], 'bold'),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).pack(anchor='w', pady=(0, SPACING['md']))
        
        tk.Label(
            form_frame,
            text=f"Saldo actual: {format_currency(credit['remaining_balance'])}",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['danger']
        ).pack(anchor='w', pady=(0, SPACING['sm']))
        
        tk.Label(
            form_frame,
            text=f"Cuota sugerida: {format_currency(credit['installment_amount'])}",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['success']
        ).pack(anchor='w', pady=(0, SPACING['lg']))
        
        # Monto del pago
        tk.Label(
            form_frame,
            text="Monto a Pagar*",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).pack(anchor='w', pady=(0, 5))
        
        entry_amount = tk.Entry(form_frame, font=(FONTS['family'], FONTS['body']), width=30)
        entry_amount.pack(fill='x', pady=(0, SPACING['md']))
        entry_amount.insert(0, str(int(credit['installment_amount'])))
        entry_amount.focus()
        
        # Notas
        tk.Label(
            form_frame,
            text="Notas (opcional)",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).pack(anchor='w', pady=(0, 5))
        
        entry_notes = tk.Text(form_frame, font=(FONTS['family'], FONTS['body']), width=30, height=4)
        entry_notes.pack(fill='x', pady=(0, SPACING['lg']))
        
        # Botones
        buttons_frame = tk.Frame(form_frame, bg=COLORS['bg_card'])
        buttons_frame.pack(fill='x')
        
        def register_payment():
            try:
                amount = float(entry_amount.get())
                if amount <= 0:
                    messagebox.showerror("Error", "El monto debe ser mayor a 0")
                    return
                
                if amount > credit['remaining_balance']:
                    response = messagebox.askyesno(
                        "Confirmar",
                        f"El monto ({format_currency(amount)}) es mayor al saldo restante.\n¿Desea continuar?"
                    )
                    if not response:
                        return
                
                notes = entry_notes.get('1.0', 'end').strip()
                
                # Registrar pago
                self.db.add_credit_payment(self.selected_credit_id, amount, notes)
                
                messagebox.showinfo("Éxito", "Pago registrado correctamente")
                self.load_credits()
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "Ingrese un monto válido")
            except Exception as e:
                messagebox.showerror("Error", f"Error al registrar pago: {str(e)}")
        
        btn_save = tk.Button(
            buttons_frame,
            text="💾 Registrar Pago",
            command=register_payment,
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
    
    def show_payment_history(self):
        """Muestra el historial de pagos de un crédito"""
        if not self.selected_credit_id:
            return
        
        credit = self.db.get_credit_sale_by_id(self.selected_credit_id)
        payments = self.db.get_credit_payments(self.selected_credit_id)
        
        # Crear ventana
        history_window = tk.Toplevel(self.parent)
        history_window.title(f"Historial de Pagos - {credit['customer_name']}")
        history_window.geometry("700x500")
        history_window.configure(bg=COLORS['bg_card'])
        history_window.transient(self.parent)
        
        # Header
        header = tk.Frame(history_window, bg=COLORS['bg_card'], padx=SPACING['lg'], pady=SPACING['lg'])
        header.pack(fill='x')
        
        tk.Label(
            header,
            text=f"Historial de Pagos - {credit['customer_name']}",
            font=(FONTS['family'], FONTS['heading'], 'bold'),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).pack()
        
        # Tabla
        table_frame = tk.Frame(history_window, bg=COLORS['bg_card'])
        table_frame.pack(fill='both', expand=True, padx=SPACING['lg'], pady=SPACING['md'])
        
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side='right', fill='y')
        
        columns = ('Fecha', 'Monto', 'Notas')
        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            yscrollcommand=scrollbar.set
        )
        
        tree.heading('Fecha', text='Fecha de Pago')
        tree.heading('Monto', text='Monto')
        tree.heading('Notas', text='Notas')
        
        tree.column('Fecha', width=150, anchor='w')
        tree.column('Monto', width=120, anchor='e')
        tree.column('Notas', width=300, anchor='w')
        
        tree.pack(fill='both', expand=True)
        scrollbar.config(command=tree.yview)
        
        # Insertar pagos
        total_paid = 0
        for payment in payments:
            tree.insert('', 'end', values=(
                format_date(payment['payment_date']),
                format_currency(payment['amount']),
                payment['notes'] or ''
            ))
            total_paid += payment['amount']
        
        # Resumen
        summary_frame = tk.Frame(history_window, bg=COLORS['bg_card'], padx=SPACING['lg'], pady=SPACING['lg'])
        summary_frame.pack(fill='x')
        
        tk.Label(
            summary_frame,
            text=f"Total Pagado: {format_currency(total_paid)}",
            font=(FONTS['family'], FONTS['body'], 'bold'),
            bg=COLORS['bg_card'],
            fg=COLORS['success']
        ).pack(side='left')
        
        tk.Label(
            summary_frame,
            text=f"Saldo Restante: {format_currency(credit['remaining_balance'])}",
            font=(FONTS['family'], FONTS['body'], 'bold'),
            bg=COLORS['bg_card'],
            fg=COLORS['danger']
        ).pack(side='right')
    
    def show_change_date_dialog(self):
        """Muestra diálogo para cambiar la fecha del próximo pago"""
        if not self.selected_credit_id:
            return
        
        credit = self.db.get_credit_sale_by_id(self.selected_credit_id)
        
        dialog = tk.Toplevel(self.parent)
        dialog.title("Cambiar Fecha de Pago")
        dialog.geometry("400x250")
        dialog.configure(bg=COLORS['bg_card'])
        dialog.transient(self.parent)
        dialog.grab_set()
        
        form_frame = tk.Frame(dialog, bg=COLORS['bg_card'], padx=SPACING['lg'], pady=SPACING['lg'])
        form_frame.pack(fill='both', expand=True)
        
        tk.Label(
            form_frame,
            text=f"Cliente: {credit['customer_name']}",
            font=(FONTS['family'], FONTS['heading'], 'bold'),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).pack(anchor='w', pady=(0, SPACING['md']))
        
        tk.Label(
            form_frame,
            text=f"Fecha actual: {credit['next_payment_date']}",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_secondary']
        ).pack(anchor='w', pady=(0, SPACING['lg']))
        
        tk.Label(
            form_frame,
            text="Nueva Fecha de Pago* (YYYY-MM-DD)",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).pack(anchor='w', pady=(0, 5))
        
        entry_date = tk.Entry(form_frame, font=(FONTS['family'], FONTS['body']), width=30)
        entry_date.pack(fill='x', pady=(0, SPACING['lg']))
        entry_date.insert(0, credit['next_payment_date'])
        entry_date.focus()
        
        buttons_frame = tk.Frame(form_frame, bg=COLORS['bg_card'])
        buttons_frame.pack(fill='x')
        
        def update_date():
            try:
                new_date = entry_date.get()
                # Validar formato
                datetime.strptime(new_date, '%Y-%m-%d')
                
                self.db.update_next_payment_date(self.selected_credit_id, new_date)
                messagebox.showinfo("Éxito", "Fecha actualizada correctamente")
                self.load_credits()
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD")
            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar: {str(e)}")
        
        btn_save = tk.Button(
            buttons_frame,
            text="💾 Actualizar",
            command=update_date,
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