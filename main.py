"""
Sistema de Punto de Venta (POS)
Aplicación principal con interfaz moderna en Tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config.settings import COLORS, FONTS, WINDOW, SPACING, BUTTON_STYLES
from database.db_manager import DatabaseManager

class POSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Venialgo Sistemas - POS Profesional")
        self.root.geometry(f"{WINDOW['main_width']}x{WINDOW['main_height']}")
        self.root.minsize(WINDOW['min_width'], WINDOW['min_height'])
        
        # Inicializar base de datos
        self.db = DatabaseManager()
        
        # Variable para rastrear módulo actual
        self.current_module = None
        
        # Configurar estilos
        self.setup_styles()
        
        # Crear interfaz
        self.create_layout()
        
        # Cargar módulo de ventas por defecto
        self.show_sales_module()
    
    def setup_styles(self):
        """Configura estilos personalizados de ttk"""
        style = ttk.Style()
        
        # Estilo para Treeview (tablas)
        style.configure("Treeview",
                       background=COLORS['bg_card'],
                       foreground=COLORS['text_primary'],
                       rowheight=30,
                       fieldbackground=COLORS['bg_card'],
                       borderwidth=0)
        
        style.configure("Treeview.Heading",
                       background=COLORS['primary'],
                       foreground=COLORS['text_white'],
                       relief="flat",
                       font=(FONTS['family'], FONTS['body'], 'bold'))
        
        style.map('Treeview.Heading',
                 background=[('active', COLORS['primary_hover'])])
    
    def create_layout(self):
        """Crea el layout principal de la aplicación"""
        
        # ========== HEADER ==========
        header = tk.Frame(self.root, bg=COLORS['bg_card'], height=60)
        header.pack(fill='x', side='top')
        header.pack_propagate(False)
        
        # Logo/Título
        title_label = tk.Label(
            header,
            text="🏪 VENIALGO SISTEMAS",
            font=(FONTS['family'], FONTS['title'], 'bold'),
            bg=COLORS['bg_card'],
            fg=COLORS['primary']
        )
        title_label.pack(side='left', padx=SPACING['lg'], pady=SPACING['md'])
        
        # Información de sesión
        info_label = tk.Label(
            header,
            text="Sistema de Punto de Venta Profesional",
            font=(FONTS['family'], FONTS['small']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_secondary']
        )
        info_label.pack(side='right', padx=SPACING['lg'])
        
        # ========== CONTENEDOR PRINCIPAL ==========
        main_container = tk.Frame(self.root, bg=COLORS['bg_main'])
        main_container.pack(fill='both', expand=True)
        
        # ========== SIDEBAR (MENÚ) ==========
        self.sidebar = tk.Frame(
            main_container,
            bg=COLORS['bg_sidebar'],
            width=220
        )
        self.sidebar.pack(fill='y', side='left')
        self.sidebar.pack_propagate(False)
        
        # Título del menú
        menu_title = tk.Label(
            self.sidebar,
            text="MENÚ PRINCIPAL",
            font=(FONTS['family'], FONTS['body'], 'bold'),
            bg=COLORS['bg_sidebar'],
            fg=COLORS['text_white'],
            pady=SPACING['lg']
        )
        menu_title.pack(fill='x', padx=SPACING['md'])
        
        # Botones del menú
        self.menu_buttons = {}
        
        menu_items = [
            ("💰 Punto de Venta", self.show_sales_module, "sales"),
            ("💳 Créditos", self.show_credits_module, "credits"),
            ("📦 Productos", self.show_products_module, "products"),
            ("👥 Clientes", self.show_customers_module, "customers"),
            ("📊 Reportes", self.show_reports_module, "reports"),
        ]
        
        for text, command, key in menu_items:
            btn = tk.Button(
                self.sidebar,
                text=text,
                command=command,
                bg=COLORS['bg_sidebar'],
                fg=COLORS['text_white'],
                font=(FONTS['family'], FONTS['body']),
                relief='flat',
                cursor='hand2',
                anchor='w',
                padx=SPACING['lg'],
                pady=SPACING['md']
            )
            btn.pack(fill='x', padx=SPACING['sm'], pady=2)
            self.menu_buttons[key] = btn
            
            # Efecto hover
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg=COLORS['primary']))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg=COLORS['bg_sidebar']))
        
        # ========== ÁREA DE CONTENIDO ==========
        self.content_area = tk.Frame(
            main_container,
            bg=COLORS['bg_main']
        )
        self.content_area.pack(fill='both', expand=True, side='left')
    
    def clear_content_area(self):
        """Limpia el área de contenido"""
        for widget in self.content_area.winfo_children():
            widget.destroy()
    
    def highlight_menu_button(self, active_key):
        """Resalta el botón del menú activo"""
        for key, btn in self.menu_buttons.items():
            if key == active_key:
                btn.config(bg=COLORS['primary'], fg=COLORS['text_white'])
            else:
                btn.config(bg=COLORS['bg_sidebar'], fg=COLORS['text_white'])
    
    # ========== MÉTODOS PARA MOSTRAR MÓDULOS ==========
    
    def show_sales_module(self):
        """Muestra el módulo de punto de venta"""
        self.clear_content_area()
        self.highlight_menu_button('sales')
        
        # Importar y crear módulo de ventas
        from modules.sales.sale_ui import SalesModule
        SalesModule(self.content_area, self.db)
    
    def show_credits_module(self):
        """Muestra el módulo de gestión de créditos"""
        self.clear_content_area()
        self.highlight_menu_button('credits')
        
        # Importar y crear módulo de créditos
        from modules.credits.credit_ui import CreditsModule
        CreditsModule(self.content_area, self.db)
    
    def show_products_module(self):
        """Muestra el módulo de gestión de productos"""
        self.clear_content_area()
        self.highlight_menu_button('products')
        
        # Importar y crear módulo de productos
        from modules.products.product_ui import ProductModule
        ProductModule(self.content_area, self.db)
    
    def show_customers_module(self):
        """Muestra el módulo de gestión de clientes"""
        self.clear_content_area()
        self.highlight_menu_button('customers')
        
        # Importar y crear módulo de clientes
        from modules.customers.customer_ui import CustomerModule
        CustomerModule(self.content_area, self.db)
    
    def show_reports_module(self):
        """Muestra el módulo de reportes"""
        self.clear_content_area()
        self.highlight_menu_button('reports')
        
        # Importar y crear módulo de reportes
        from modules.reports.report_ui import ReportsModule
        ReportsModule(self.content_area, self.db)

def main():
    """Función principal"""
    root = tk.Tk()
    app = POSApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()