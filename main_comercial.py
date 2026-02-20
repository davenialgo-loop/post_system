# -*- coding: utf-8 -*-
"""
main_comercial.py
Sistema de Punto de Venta (POS) v1.1
Venialgo Sistemas
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os, sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config.settings import COLORS, FONTS, WINDOW, SPACING, BUTTON_STYLES
from database.db_manager import DatabaseManager
from license.license_manager import is_licensed
from backup.backup_manager import backup_service
from modules.admin.admin_ui import _ensure_tables
from modules.admin.license_ui import eula_accepted, EULAWindow, ActivationWindow
from modules.admin.login_window import LoginWindow
from modules.admin.first_run_wizard import is_first_run, FirstRunWizard
from utils.company_header import CompanyHeaderWidget, add_footer, get_company

APP_VERSION = "1.1"
_ensure_tables()


# ================================================================
#  FLUJO DE ARRANQUE — maquina de estados secuencial
# ================================================================

class AppStarter:
    """
    Maneja la secuencia de arranque usando un unico root Tk
    y callbacks encadenados. Evita el problema de destroy.
    """

    STEP_EULA      = "eula"
    STEP_LICENSE   = "license"
    STEP_LOGIN     = "login"
    STEP_WIZARD    = "wizard"
    STEP_MAIN      = "main"

    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("Sistema POS - Venialgo Sistemas")
        self.user_data = None

    def start(self):
        # Root siempre oculto hasta la ventana principal
        self.root.withdraw()
        # Decidir primer paso
        if not eula_accepted():
            self._step_eula()
        elif not is_licensed():
            self._step_license()
        else:
            self._step_login()
        self.root.mainloop()

    # ── PASO 1: EULA ─────────────────────────────────────────
    def _step_eula(self):
        def on_accept():
            # Continuar al siguiente paso desde el event loop
            self.root.after(100, self._after_eula)

        def on_reject():
            self.root.quit()
            self.root.destroy()
            sys.exit(0)

        EULAWindow(self.root, on_accept=on_accept, on_reject=on_reject)

    def _after_eula(self):
        if not is_licensed():
            self._step_license()
        else:
            self._step_login()

    # ── PASO 2: LICENCIA ─────────────────────────────────────
    def _step_license(self):
        def on_success():
            self.root.after(100, self._step_login)

        def on_cancel():
            # Permitir continuar sin licencia (modo demo)
            self.root.after(100, self._step_login)

        win = tk.Toplevel(self.root)
        win.withdraw()
        ActivationWindow(win, on_success=on_success, on_cancel=on_cancel)
        win.deiconify()

    # ── PASO 3: LOGIN ─────────────────────────────────────────
    def _step_login(self):
        def on_login(uid, nombre, rol):
            self.user_data = {"id": uid, "nombre": nombre, "rol": rol}
            self.root.after(100, self._after_login)

        win = tk.Toplevel(self.root)
        win.withdraw()
        LoginWindow(win, on_success=on_login)
        win.deiconify()

    def _after_login(self):
        if not self.user_data:
            self.root.quit()
            return
        if is_first_run():
            self._step_wizard()
        else:
            self._step_main()

    # ── PASO 4: WIZARD PRIMERA VEZ ───────────────────────────
    def _step_wizard(self):
        def on_complete():
            self.root.after(100, self._step_main)

        win = tk.Toplevel(self.root)
        win.withdraw()
        FirstRunWizard(win, on_complete=on_complete)
        win.deiconify()

    # ── PASO 5: VENTANA PRINCIPAL ─────────────────────────────
    def _step_main(self):
        if not self.user_data:
            self.root.quit()
            return
        self.root.deiconify()
        POSApp(self.root, current_user=self.user_data)


def startup_flow():
    starter = AppStarter()
    starter.start()


# ================================================================
#  APLICACION PRINCIPAL
# ================================================================

class POSApp:
    def __init__(self, root, current_user=None):
        self.root = root
        self.current_user = current_user or {
            "id": 0, "nombre": "Sistema", "rol": "Administrador"
        }

        co = get_company()
        nombre_emp = co.get("razon_social") or "Venialgo Sistemas"

        self.root.title(
            f"{nombre_emp} - POS v{APP_VERSION} | "
            f"{self.current_user['nombre']} [{self.current_user['rol']}]"
        )
        self.root.geometry(f"{WINDOW['main_width']}x{WINDOW['main_height']}")
        self.root.minsize(WINDOW['min_width'], WINDOW['min_height'])
        self.root.configure(bg=COLORS['bg_main'])

        self.db = DatabaseManager()
        backup_service.start()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.setup_styles()
        try:
            self.create_layout()
        except Exception as e:
            import traceback
            err = traceback.format_exc()
            tk.Label(self.root, text=f"ERROR en layout:\n{err}",
                     bg="white", fg="red", justify="left",
                     font=("Courier New", 9),
                     wraplength=900).pack(padx=20, pady=20)
            return
        try:
            self.show_sales_module()
        except Exception as e:
            import traceback
            err = traceback.format_exc()
            tk.Label(self.root, text=f"ERROR en modulo ventas:\n{err}",
                     bg="white", fg="red", justify="left",
                     font=("Courier New", 9),
                     wraplength=900).pack(padx=20, pady=20)

    # ── Estilos ───────────────────────────────────────────────
    def setup_styles(self):
        style = ttk.Style()
        try: style.theme_use('clam')
        except: pass
        style.configure("Treeview",
            background="white", foreground="black",
            rowheight=30, fieldbackground="white", borderwidth=1)
        style.configure("Treeview.Heading",
            background="#1e293b", foreground="white",
            relief="flat", borderwidth=1,
            font=(FONTS['family'], FONTS['body'], 'bold'))
        style.map('Treeview.Heading',
            background=[('active','#2563eb')], foreground=[('active','white')])
        style.map('Treeview',
            background=[('selected','#2563eb')], foreground=[('selected','white')])

    # ── Layout ────────────────────────────────────────────────
    def create_layout(self):
        self._build_header()
        main = tk.Frame(self.root, bg=COLORS['bg_main'])
        main.pack(fill='both', expand=True)
        self._build_sidebar(main)
        self.content_area = tk.Frame(main, bg=COLORS['bg_main'])
        self.content_area.pack(fill='both', expand=True, side='left')
        add_footer(self.root)

    def _build_header(self):
        outer = tk.Frame(self.root, bg=COLORS['bg_card'])
        outer.pack(fill='x', side='top')

        self.company_widget = CompanyHeaderWidget(
            outer, height=64, bg=COLORS['bg_card'])
        self.company_widget.pack(side='left', fill='both', expand=True)

        frm_right = tk.Frame(outer, bg=COLORS['bg_card'])
        frm_right.pack(side='right', padx=16, fill='y')

        rol    = self.current_user.get('rol', '')
        nombre = self.current_user.get('nombre', '')
        rol_colors = {
            'Administrador': '#7c3aed',
            'Supervisor':    '#0891b2',
            'Cajero':        '#16a34a',
        }
        tk.Label(frm_right, text=f" v{APP_VERSION} ",
            font=(FONTS['family'], FONTS['small'], 'bold'),
            bg='#334155', fg='white', padx=6, pady=2).pack(pady=(14,2))

        lic_ok = is_licensed()
        tk.Label(frm_right,
            text=" Licenciado " if lic_ok else " Sin licencia ",
            font=(FONTS['family'], FONTS['small'], 'bold'),
            bg='#16a34a' if lic_ok else '#dc2626',
            fg='white', padx=6, pady=2).pack(pady=2)

        tk.Label(frm_right, text=f" {rol} ",
            font=(FONTS['family'], FONTS['small'], 'bold'),
            bg=rol_colors.get(rol, COLORS['primary']),
            fg='white', padx=6, pady=2).pack(pady=2)

        tk.Label(frm_right, text=f"Usuario: {nombre}",
            font=(FONTS['family'], FONTS['small']),
            bg=COLORS['bg_card'],
            fg=COLORS['text_secondary']).pack(pady=(2,0))

    def _build_sidebar(self, container):
        self.sidebar = tk.Frame(
            container, bg=COLORS['bg_sidebar'], width=220)
        self.sidebar.pack(fill='y', side='left')
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="MENU PRINCIPAL",
            font=(FONTS['family'], FONTS['body'], 'bold'),
            bg=COLORS['bg_sidebar'], fg=COLORS['text_white'],
            pady=SPACING['lg']).pack(fill='x', padx=SPACING['md'])

        self.menu_buttons = {}
        menu_items = [
            ("Punto de Venta",  self.show_sales_module,    "sales",
             ["Administrador","Supervisor","Cajero"]),
            ("Creditos",        self.show_credits_module,  "credits",
             ["Administrador","Supervisor","Cajero"]),
            ("Productos",       self.show_products_module, "products",
             ["Administrador","Supervisor"]),
            ("Clientes",        self.show_customers_module,"customers",
             ["Administrador","Supervisor"]),
            ("Reportes",        self.show_reports_module,  "reports",
             ["Administrador","Supervisor"]),
        ]

        rol = self.current_user.get('rol','')
        for text, cmd, key, roles in menu_items:
            if rol not in roles:
                continue
            btn = tk.Button(self.sidebar, text=text, command=cmd,
                bg=COLORS['bg_sidebar'], fg=COLORS['text_white'],
                font=(FONTS['family'], FONTS['body']),
                relief='flat', cursor='hand2',
                anchor='w', padx=SPACING['lg'], pady=SPACING['md'])
            btn.pack(fill='x', padx=SPACING['sm'], pady=2)
            self.menu_buttons[key] = btn
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg=COLORS['primary']))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg=COLORS['bg_sidebar']))

        if rol == 'Administrador':
            ttk.Separator(self.sidebar).pack(fill='x', padx=SPACING['md'], pady=8)
            btn_adm = tk.Button(self.sidebar, text="Administracion",
                command=self.show_admin_module,
                bg=COLORS['bg_sidebar'], fg='#a78bfa',
                font=(FONTS['family'], FONTS['body'], 'bold'),
                relief='flat', cursor='hand2',
                anchor='w', padx=SPACING['lg'], pady=SPACING['md'])
            btn_adm.pack(fill='x', padx=SPACING['sm'], pady=2)
            self.menu_buttons['admin'] = btn_adm
            btn_adm.bind('<Enter>', lambda e: btn_adm.config(bg='#4c1d95'))
            btn_adm.bind('<Leave>', lambda e: btn_adm.config(bg=COLORS['bg_sidebar']))

        # Espacio flexible
        tk.Frame(self.sidebar, bg=COLORS['bg_sidebar']).pack(
            fill='both', expand=True)

        # Backup status
        self._lbl_backup = tk.Label(self.sidebar,
            text="Backup: " + backup_service.last_backup_str,
            font=(FONTS['family'], 7),
            bg=COLORS['bg_sidebar'], fg='#475569',
            wraplength=190, justify='left')
        self._lbl_backup.pack(fill='x', padx=SPACING['lg'], pady=2)

        tk.Button(self.sidebar, text="Backup ahora",
            command=self._manual_backup,
            bg='#0f2d0f', fg='#4ade80',
            font=(FONTS['family'], FONTS['small']),
            relief='flat', cursor='hand2', pady=4).pack(
            fill='x', padx=SPACING['sm'], pady=2)

        # Logout
        btn_lo = tk.Button(self.sidebar, text="Cerrar Sesion",
            command=self._logout,
            bg='#7f1d1d', fg=COLORS['text_white'],
            font=(FONTS['family'], FONTS['body'], 'bold'),
            relief='flat', cursor='hand2', pady=SPACING['md'])
        btn_lo.pack(fill='x', padx=SPACING['sm'], pady=(0, SPACING['sm']))
        btn_lo.bind('<Enter>', lambda e: btn_lo.config(bg='#dc2626'))
        btn_lo.bind('<Leave>', lambda e: btn_lo.config(bg='#7f1d1d'))

    # ── Modulos ───────────────────────────────────────────────
    def clear_content_area(self):
        for w in self.content_area.winfo_children():
            w.destroy()

    def highlight_menu_button(self, active_key):
        for key, btn in self.menu_buttons.items():
            if key == active_key:
                btn.config(bg=COLORS['primary'], fg=COLORS['text_white'])
            else:
                fg = '#a78bfa' if key == 'admin' else COLORS['text_white']
                btn.config(bg=COLORS['bg_sidebar'], fg=fg)

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
        self.clear_content_area()
        self.highlight_menu_button('admin')
        from modules.admin.admin_ui import AdminModule
        AdminModule(self.content_area, self.db, self.current_user,
                    on_company_saved=self._refresh_header)

    def _refresh_header(self):
        self.company_widget.refresh()
        co = get_company()
        nombre_emp = co.get("razon_social") or "Venialgo Sistemas"
        self.root.title(
            f"{nombre_emp} - POS v{APP_VERSION} | "
            f"{self.current_user['nombre']} [{self.current_user['rol']}]"
        )

    # ── Backup / Logout / Close ───────────────────────────────
    def _manual_backup(self):
        ok, msg = backup_service.force_backup()
        self._lbl_backup.config(
            text="Backup: " + backup_service.last_backup_str)
        if ok:
            messagebox.showinfo("Backup OK", f"Backup creado.\n{msg}")
        else:
            messagebox.showerror("Error backup", f"Error:\n{msg}")

    def _on_close(self):
        try: backup_service.stop()
        except: pass
        self.root.destroy()

    def _logout(self):
        if messagebox.askyesno("Cerrar Sesion", "Desea cerrar la sesion?"):
            try: backup_service.stop()
            except: pass
            # Reiniciar aplicacion
            self.root.destroy()
            startup_flow()


def main():
    startup_flow()

if __name__ == "__main__":
    main()
