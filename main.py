"""
Sistema de Punto de Venta (POS)
Aplicación principal con interfaz moderna en Tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config.settings import COLORS, FONTS, WINDOW, SPACING, BUTTON_STYLES
from database.db_manager import DatabaseManager

# ── Asegurar tablas de administración al arrancar ────────
from modules.admin.admin_ui import _ensure_tables
from modules.admin.login_window import add_footer, LoginWindow
_ensure_tables()


class POSApp:
    def __init__(self, root, current_user=None):
        self.root = root
        # current_user = {"id": uid, "nombre": nombre, "rol": rol}
        self.current_user = current_user or {"id": 0, "nombre": "Sistema", "rol": "Administrador"}

        self.root.title("Venialgo Sistemas - POS")
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

        try:
            style.theme_use('clam')
        except:
            pass

        style.configure("Treeview",
                        background="white",
                        foreground="black",
                        rowheight=30,
                        fieldbackground="white",
                        borderwidth=1)

        style.configure("Treeview.Heading",
                        background="#1e293b",
                        foreground="white",
                        relief="flat",
                        borderwidth=1,
                        font=(FONTS['family'], FONTS['body'], 'bold'))

        style.map('Treeview.Heading',
                  background=[('active', '#2563eb')],
                  foreground=[('active', 'white')])

        style.map('Treeview',
                  background=[('selected', '#2563eb')],
                  foreground=[('selected', 'white')])

    def create_layout(self):
        """Crea el layout principal de la aplicación"""

        # ── HEADER ──────────────────────────────────────
        header = tk.Frame(self.root, bg=COLORS['bg_card'], height=60)
        header.pack(fill='x', side='top')
        header.pack_propagate(False)

        # Logo/Título
        tk.Label(
            header,
            text="🪪 VENIALGO SISTEMAS",
            font=(FONTS['family'], FONTS['title'], 'bold'),
            bg=COLORS['bg_card'],
            fg=COLORS['primary']
        ).pack(side='left', padx=SPACING['lg'], pady=SPACING['md'])

        # Badge usuario/rol
        rol   = self.current_user.get('rol', '')
        nombre = self.current_user.get('nombre', '')
        rol_colors = {
            'Administrador': '#7c3aed',
            'Supervisor':    '#0891b2',
            'Cajero':        '#16a34a',
        }
        badge_bg = rol_colors.get(rol, COLORS['primary'])

        badge_frm = tk.Frame(header, bg=COLORS['bg_card'])
        badge_frm.pack(side='right', padx=SPACING['lg'])
        tk.Label(badge_frm,
                 text=f"👤 {nombre}",
                 font=(FONTS['family'], FONTS['body']),
                 bg=COLORS['bg_card'],
                 fg=COLORS['text_secondary']).pack(side='left', padx=(0,6))
        tk.Label(badge_frm,
                 text=f" {rol} ",
                 font=(FONTS['family'], FONTS['small'], 'bold'),
                 bg=badge_bg, fg='white',
                 padx=6, pady=2).pack(side='left')

        # ── CONTENEDOR PRINCIPAL ─────────────────────────
        main_container = tk.Frame(self.root, bg=COLORS['bg_main'])
        main_container.pack(fill='both', expand=True)

        # ── SIDEBAR ──────────────────────────────────────
        self.sidebar = tk.Frame(
            main_container,
            bg=COLORS['bg_sidebar'],
            width=220
        )
        self.sidebar.pack(fill='y', side='left')
        self.sidebar.pack_propagate(False)

        tk.Label(
            self.sidebar,
            text="MENÚ PRINCIPAL",
            font=(FONTS['family'], FONTS['body'], 'bold'),
            bg=COLORS['bg_sidebar'],
            fg=COLORS['text_white'],
            pady=SPACING['lg']
        ).pack(fill='x', padx=SPACING['md'])

        self.menu_buttons = {}

        # Definir ítems con rol mínimo requerido
        menu_items = [
            ("💰 Punto de Venta",  self.show_sales_module,     "sales",     ["Administrador","Supervisor","Cajero"]),
            ("💳 Créditos",         self.show_credits_module,   "credits",   ["Administrador","Supervisor","Cajero"]),
            ("📦 Productos",        self.show_products_module,  "products",  ["Administrador","Supervisor"]),
            ("👥 Clientes",         self.show_customers_module, "customers", ["Administrador","Supervisor"]),
            ("📊 Reportes",         self.show_reports_module,   "reports",   ["Administrador","Supervisor"]),
        ]

        for text, command, key, roles in menu_items:
            if self.current_user.get('rol') not in roles:
                continue
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
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg=COLORS['primary']))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg=COLORS['bg_sidebar']))

        # Separador + botón Administración (solo Administrador)
        if self.current_user.get('rol') == 'Administrador':
            sep_frm = tk.Frame(self.sidebar, bg=COLORS['bg_sidebar'])
            sep_frm.pack(fill='x', padx=SPACING['md'], pady=(8, 4))
            ttk.Separator(sep_frm).pack(fill='x')

            btn_adm = tk.Button(
                self.sidebar,
                text="⚙️ Administración",
                command=self.show_admin_module,
                bg=COLORS['bg_sidebar'],
                fg='#a78bfa',
                font=(FONTS['family'], FONTS['body'], 'bold'),
                relief='flat',
                cursor='hand2',
                anchor='w',
                padx=SPACING['lg'],
                pady=SPACING['md']
            )
            btn_adm.pack(fill='x', padx=SPACING['sm'], pady=2)
            self.menu_buttons['admin'] = btn_adm
            btn_adm.bind('<Enter>', lambda e: btn_adm.config(bg='#4c1d95'))
            btn_adm.bind('<Leave>', lambda e: btn_adm.config(bg=COLORS['bg_sidebar']))

        # Botón cerrar sesión al fondo del sidebar
        tk.Frame(self.sidebar, bg=COLORS['bg_sidebar']).pack(fill='both', expand=True)
        btn_logout = tk.Button(
            self.sidebar,
            text="🚪 Cerrar Sesión",
            command=self._logout,
            bg='#7f1d1d',
            fg=COLORS['text_white'],
            font=(FONTS['family'], FONTS['body'], 'bold'),
            relief='flat',
            cursor='hand2',
            pady=SPACING['md']
        )
        btn_logout.pack(fill='x', padx=SPACING['sm'], pady=(0, SPACING['sm']))
        btn_logout.bind('<Enter>', lambda e: btn_logout.config(bg='#dc2626'))
        btn_logout.bind('<Leave>', lambda e: btn_logout.config(bg='#7f1d1d'))

        # ── ÁREA DE CONTENIDO ────────────────────────────
        self.content_area = tk.Frame(main_container, bg=COLORS['bg_main'])
        self.content_area.pack(fill='both', expand=True, side='left')

        # ── FOOTER ───────────────────────────────────────
        add_footer(self.root)

    def clear_content_area(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()

    def highlight_menu_button(self, active_key):
        for key, btn in self.menu_buttons.items():
            if key == active_key:
                btn.config(bg=COLORS['primary'], fg=COLORS['text_white'])
            else:
                fg = '#a78bfa' if key == 'admin' else COLORS['text_white']
                btn.config(bg=COLORS['bg_sidebar'], fg=fg)

    # ── MÓDULOS ──────────────────────────────────────────

    def show_sales_module(self):
        self.clear_content_area()
        self.highlight_menu_button('sales')
        from modules.sales.sale_ui import SalesModule
        SalesModule(self.content_area, self.db)

    def show_credits_module(self):
        self.clear_content_area()
        self.highlight_menu_button('credits')
        from modules.credits.credit_ui import CreditsModule
        CreditsModule(self.content_area, self.db)

    def show_products_module(self):
        self.clear_content_area()
        self.highlight_menu_button('products')
        from modules.products.product_ui import ProductModule
        ProductModule(self.content_area, self.db)

    def show_customers_module(self):
        self.clear_content_area()
        self.highlight_menu_button('customers')
        from modules.customers.customer_ui import CustomerModule
        CustomerModule(self.content_area, self.db)

    def show_reports_module(self):
        self.clear_content_area()
        self.highlight_menu_button('reports')
        from modules.reports.report_ui import ReportsModule
        ReportsModule(self.content_area, self.db)

    def show_admin_module(self):
        """Módulo de administración — solo para Administradores."""
        self.clear_content_area()
        self.highlight_menu_button('admin')
        from modules.admin.admin_ui import AdminModule
        AdminModule(self.content_area, self.db, self.current_user)

    # ── LOGOUT ───────────────────────────────────────────
    def _logout(self):
        if messagebox.askyesno("Cerrar Sesión",
                               "¿Desea cerrar la sesión actual?"):
            self.root.destroy()
            main()  # Vuelve al login


# ════════════════════════════════════════════════════════
#  ENTRYPOINT
# ════════════════════════════════════════════════════════
def launch_pos(uid, nombre, rol):
    """Lanza la ventana principal tras autenticación."""
    root = tk.Tk()
    POSApp(root, current_user={"id": uid, "nombre": nombre, "rol": rol})
    root.mainloop()


def main():
    """Función principal — muestra login antes del POS."""
    root = tk.Tk()
    LoginWindow(root, on_success=launch_pos)
    root.mainloop()


if __name__ == "__main__":
    main()