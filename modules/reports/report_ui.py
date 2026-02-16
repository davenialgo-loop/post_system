"""
Módulo de Reportes y Estadísticas
Interfaz para visualizar ventas e indicadores
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config.settings import COLORS, FONTS, SPACING, BUTTON_STYLES
from utils.formatters import format_currency, format_date
from datetime import datetime, timedelta

class ReportsModule:
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db = db_manager
        
        self.create_ui()
        self.load_today_sales()
    
    def create_ui(self):
        """Crea la interfaz del módulo de reportes"""
        
        # ========== HEADER ==========
        header_frame = tk.Frame(self.parent, bg=COLORS['bg_main'])
        header_frame.pack(fill='x', padx=SPACING['lg'], pady=(SPACING['lg'], SPACING['md']))
        
        title = tk.Label(
            header_frame,
            text="📊 Reportes y Estadísticas",
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
        
        # Fecha desde
        tk.Label(
            filter_inner,
            text="Desde:",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).grid(row=0, column=0, padx=SPACING['sm'], pady=SPACING['sm'])
        
        self.date_from = tk.Entry(filter_inner, font=(FONTS['family'], FONTS['body']), width=12)
        self.date_from.grid(row=0, column=1, padx=SPACING['sm'])
        self.date_from.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        # Fecha hasta
        tk.Label(
            filter_inner,
            text="Hasta:",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).grid(row=0, column=2, padx=SPACING['sm'], pady=SPACING['sm'])
        
        self.date_to = tk.Entry(filter_inner, font=(FONTS['family'], FONTS['body']), width=12)
        self.date_to.grid(row=0, column=3, padx=SPACING['sm'])
        self.date_to.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        # Botones rápidos
        btn_today = tk.Button(
            filter_inner,
            text="Hoy",
            command=self.load_today_sales,
            **BUTTON_STYLES['secondary']
        )
        btn_today.grid(row=0, column=4, padx=SPACING['sm'])
        
        btn_week = tk.Button(
            filter_inner,
            text="Esta Semana",
            command=self.load_week_sales,
            **BUTTON_STYLES['secondary']
        )
        btn_week.grid(row=0, column=5, padx=SPACING['sm'])
        
        btn_month = tk.Button(
            filter_inner,
            text="Este Mes",
            command=self.load_month_sales,
            **BUTTON_STYLES['secondary']
        )
        btn_month.grid(row=0, column=6, padx=SPACING['sm'])
        
        btn_search = tk.Button(
            filter_inner,
            text="🔍 Buscar",
            command=self.load_sales_by_date,
            **BUTTON_STYLES['primary']
        )
        btn_search.grid(row=0, column=7, padx=SPACING['sm'])
        
        # ========== ESTADÍSTICAS ==========
        stats_frame = tk.Frame(self.parent, bg=COLORS['bg_main'])
        stats_frame.pack(fill='x', padx=SPACING['lg'], pady=SPACING['md'])
        
        # Card de Total Ventas
        self.card_total = self.create_stat_card(
            stats_frame, 
            "Total Vendido", 
            "$0.00",
            COLORS['success']
        )
        self.card_total.pack(side='left', padx=SPACING['sm'], fill='both', expand=True)
        
        # Card de Cantidad de Ventas
        self.card_count = self.create_stat_card(
            stats_frame,
            "Cantidad de Ventas",
            "0",
            COLORS['primary']
        )
        self.card_count.pack(side='left', padx=SPACING['sm'], fill='both', expand=True)
        
        # Card de Promedio
        self.card_avg = self.create_stat_card(
            stats_frame,
            "Promedio por Venta",
            "$0.00",
            COLORS['info']
        )
        self.card_avg.pack(side='left', padx=SPACING['sm'], fill='both', expand=True)
        
        # ========== TABLA DE VENTAS ==========
        table_frame = tk.Frame(self.parent, bg=COLORS['bg_card'])
        table_frame.pack(fill='both', expand=True, padx=SPACING['lg'], pady=SPACING['md'])
        
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side='right', fill='y')
        
        columns = ('ID', 'Fecha', 'Cliente', 'Total', 'Método Pago')
        self.sales_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            yscrollcommand=scrollbar.set,
            selectmode='browse'
        )
        
        self.sales_tree.heading('ID', text='ID')
        self.sales_tree.heading('Fecha', text='Fecha')
        self.sales_tree.heading('Cliente', text='Cliente')
        self.sales_tree.heading('Total', text='Total')
        self.sales_tree.heading('Método Pago', text='Método de Pago')
        
        self.sales_tree.column('ID', width=60, anchor='center')
        self.sales_tree.column('Fecha', width=150, anchor='w')
        self.sales_tree.column('Cliente', width=200, anchor='w')
        self.sales_tree.column('Total', width=120, anchor='e')
        self.sales_tree.column('Método Pago', width=150, anchor='w')
        
        self.sales_tree.pack(fill='both', expand=True)
        scrollbar.config(command=self.sales_tree.yview)
        
        # Bind doble click para ver detalles
        self.sales_tree.bind('<Double-Button-1>', lambda e: self.show_sale_details())
        
        # ========== BOTONES DE ACCIÓN ==========
        actions_frame = tk.Frame(self.parent, bg=COLORS['bg_main'])
        actions_frame.pack(fill='x', padx=SPACING['lg'], pady=SPACING['md'])
        
        btn_details = tk.Button(
            actions_frame,
            text="👁️ Ver Detalles",
            command=self.show_sale_details,
            **BUTTON_STYLES['primary']
        )
        btn_details.pack(side='left', padx=SPACING['sm'])
    
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
            font=(FONTS['family'], FONTS['title'], 'bold'),
            bg=COLORS['bg_card'],
            fg=color
        )
        value_label.pack(pady=(0, SPACING['md']))
        
        # Guardar referencia al label de valor
        card.value_label = value_label
        
        return card
    
    def load_today_sales(self):
        """Carga ventas del día actual"""
        today = datetime.now().strftime('%Y-%m-%d')
        self.date_from.delete(0, tk.END)
        self.date_from.insert(0, today)
        self.date_to.delete(0, tk.END)
        self.date_to.insert(0, today)
        self.load_sales_by_date()
    
    def load_week_sales(self):
        """Carga ventas de la última semana"""
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        
        self.date_from.delete(0, tk.END)
        self.date_from.insert(0, week_ago.strftime('%Y-%m-%d'))
        self.date_to.delete(0, tk.END)
        self.date_to.insert(0, today.strftime('%Y-%m-%d'))
        self.load_sales_by_date()
    
    def load_month_sales(self):
        """Carga ventas del mes actual"""
        today = datetime.now()
        first_day = today.replace(day=1)
        
        self.date_from.delete(0, tk.END)
        self.date_from.insert(0, first_day.strftime('%Y-%m-%d'))
        self.date_to.delete(0, tk.END)
        self.date_to.insert(0, today.strftime('%Y-%m-%d'))
        self.load_sales_by_date()
    
    def load_sales_by_date(self):
        """Carga ventas según rango de fechas"""
        try:
            start_date = self.date_from.get()
            end_date = self.date_to.get()
            
            # Validar formato de fechas
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
            
            # Obtener ventas
            sales = self.db.get_sales_by_date(start_date, end_date)
            
            # Limpiar tabla
            for item in self.sales_tree.get_children():
                self.sales_tree.delete(item)
            
            # Insertar ventas
            for sale in sales:
                customer_name = sale['customer_name'] if sale['customer_name'] else 'Cliente General'
                self.sales_tree.insert('', 'end', values=(
                    sale['id'],
                    format_date(sale['sale_date']),
                    customer_name,
                    format_currency(sale['total']),
                    sale['payment_method']
                ))
            
            # Actualizar estadísticas
            summary = self.db.get_sales_summary(start_date, end_date)
            if summary:
                total_sales = summary['total_sales'] or 0
                total_revenue = summary['total_revenue'] or 0
                avg_sale = summary['average_sale'] or 0
                
                self.card_total.value_label.config(text=format_currency(total_revenue))
                self.card_count.value_label.config(text=str(total_sales))
                self.card_avg.value_label.config(text=format_currency(avg_sale))
            
        except ValueError:
            messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar ventas: {str(e)}")
    
    def show_sale_details(self):
        """Muestra los detalles de una venta seleccionada"""
        selection = self.sales_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione una venta")
            return
        
        item = self.sales_tree.item(selection[0])
        sale_id = item['values'][0]
        
        # Obtener detalles de la venta
        details = self.db.get_sale_details(sale_id)
        
        if not details:
            messagebox.showinfo("Info", "No se encontraron detalles")
            return
        
        # Crear ventana de detalles
        details_window = tk.Toplevel(self.parent)
        details_window.title(f"Detalles de Venta #{sale_id}")
        details_window.geometry("600x400")
        details_window.configure(bg=COLORS['bg_card'])
        details_window.transient(self.parent)
        
        # Título
        tk.Label(
            details_window,
            text=f"Productos de la Venta #{sale_id}",
            font=(FONTS['family'], FONTS['heading'], 'bold'),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).pack(pady=SPACING['lg'])
        
        # Tabla de detalles
        table_frame = tk.Frame(details_window, bg=COLORS['bg_card'])
        table_frame.pack(fill='both', expand=True, padx=SPACING['lg'], pady=SPACING['md'])
        
        columns = ('Producto', 'Cantidad', 'Precio Unit.', 'Subtotal')
        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            selectmode='browse'
        )
        
        tree.heading('Producto', text='Producto')
        tree.heading('Cantidad', text='Cantidad')
        tree.heading('Precio Unit.', text='Precio Unitario')
        tree.heading('Subtotal', text='Subtotal')
        
        tree.column('Producto', width=250, anchor='w')
        tree.column('Cantidad', width=100, anchor='center')
        tree.column('Precio Unit.', width=120, anchor='e')
        tree.column('Subtotal', width=120, anchor='e')
        
        tree.pack(fill='both', expand=True)
        
        # Insertar detalles
        total = 0
        for detail in details:
            tree.insert('', 'end', values=(
                detail['product_name'],
                detail['quantity'],
                format_currency(detail['unit_price']),
                format_currency(detail['subtotal'])
            ))
            total += detail['subtotal']
        
        # Total
        total_frame = tk.Frame(details_window, bg=COLORS['bg_card'])
        total_frame.pack(fill='x', padx=SPACING['lg'], pady=SPACING['md'])
        
        tk.Label(
            total_frame,
            text="TOTAL:",
            font=(FONTS['family'], FONTS['heading'], 'bold'),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).pack(side='left')
        
        tk.Label(
            total_frame,
            text=format_currency(total),
            font=(FONTS['family'], FONTS['heading'], 'bold'),
            bg=COLORS['bg_card'],
            fg=COLORS['success']
        ).pack(side='right')
        
        # Botón cerrar
        btn_close = tk.Button(
            details_window,
            text="Cerrar",
            command=details_window.destroy,
            **BUTTON_STYLES['secondary']
        )
        btn_close.pack(pady=SPACING['md'])