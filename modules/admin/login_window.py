"""
Ventana de Login para el Sistema POS
"""

import tkinter as tk
from tkinter import messagebox
import sqlite3
import hashlib

try:
    from config.settings import COLORS, FONTS, SPACING
except ImportError:
    COLORS  = {'primary': '#2563eb', 'bg_card': '#ffffff',
               'bg_main': '#f1f5f9', 'bg_sidebar': '#1e293b',
               'text_white': '#ffffff', 'text_secondary': '#64748b',
               'success': '#16a34a', 'danger': '#dc2626'}
    FONTS   = {'family': 'Segoe UI', 'title': 16, 'subtitle': 13,
               'body': 10, 'small': 9}
    SPACING = {'xs': 4, 'sm': 8, 'md': 12, 'lg': 16, 'xl': 24}

import os as _os, sys as _sys
def _get_db_file():
    if _sys.platform == "win32":
        base = _os.environ.get("APPDATA", _os.path.expanduser("~"))
    else:
        base = _os.path.expanduser("~")
    d = _os.path.join(base, "VenialgoPOS")
    _os.makedirs(d, exist_ok=True)
    return _os.path.join(d, "pos_database.db")
DB_FILE = _get_db_file()

FOOTER_INFO = {
    "empresa":  "Venialgo Sistemas",
    "email":    "davenialgo@proton.me",
    "whatsapp": "+595 994-686 493",
    "web":      "www.venialgosistemas.com",   # Actualizar cuando esté disponible
}


def add_footer(window, bg_override=None):
    """
    Agrega el footer de Venialgo Sistemas a cualquier ventana.
    Llámalo con: add_footer(self.root)
    """
    bg = bg_override or "#1e293b"
    bar = tk.Frame(window, bg=bg, height=26)
    bar.pack(side='bottom', fill='x')
    bar.pack_propagate(False)
    txt = (
        f"  ★ {FOOTER_INFO['empresa']}  │  "
        f"✉ {FOOTER_INFO['email']}  │  "
        f"📱 WhatsApp: {FOOTER_INFO['whatsapp']}  │  "
        f"🌐 {FOOTER_INFO['web']}  "
    )
    tk.Label(bar, text=txt, bg=bg, fg='#94a3b8',
             font=(FONTS['family'], FONTS['small'])).pack(side='left')
    return bar


def verify_login(usuario, password):
    """Verifica credenciales. Retorna (id, nombre, rol) o None."""
    hpwd = hashlib.sha256(password.encode()).hexdigest()
    try:
        # Asegurar que las tablas existen antes de consultar
        from modules.admin.admin_ui import _ensure_tables
        _ensure_tables()
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""SELECT id,nombre,rol FROM usuarios
                     WHERE usuario=? AND password=? AND activo=1""",
                  (usuario, hpwd))
        row = c.fetchone()
        conn.close()
        return row
    except Exception as e:
        print(f"Error login: {e}")
        return None


class LoginWindow:
    """
    Ventana de inicio de sesión.
    Uso:
        root = tk.Tk()
        app  = LoginWindow(root, on_success_callback)
        root.mainloop()

    on_success_callback(uid, nombre, rol) se llama al autenticar.
    """

    def __init__(self, root, on_success):
        self.root       = root
        self.on_success = on_success

        self.root.title("Sistema POS - Iniciar Sesion")
        self.root.geometry("420x580")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS['bg_sidebar'])
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._center()
        self._build()

    def _on_close(self):
        self.root.destroy()

    def _center(self):
        self.root.update_idletasks()
        w, h = 420, 580
        x = (self.root.winfo_screenwidth()  - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _load_logo(self):
        """Carga el logo desde assets o ruta del ejecutable."""
        import os, sys
        logo_paths = [
            os.path.join(os.path.dirname(sys.executable), "assets", "VenialgoSistemasLogo.png"),
            os.path.join(os.path.dirname(__file__), "..", "..", "assets", "VenialgoSistemasLogo.png"),
            os.path.join(os.path.dirname(__file__), "VenialgoSistemasLogo.png"),
            "assets/VenialgoSistemasLogo.png",
            "VenialgoSistemasLogo.png",
        ]
        for path in logo_paths:
            if os.path.exists(path):
                return path
        return None

    def _build(self):
        # ── Encabezado con logo ───────────────────────
        top = tk.Frame(self.root, bg=COLORS['bg_sidebar'])
        top.pack(fill='x', pady=(24, 12))

        # Intentar cargar imagen del logo
        logo_path = self._load_logo()
        logo_loaded = False
        if logo_path:
            try:
                from PIL import Image, ImageTk
                img = Image.open(logo_path).convert("RGBA")
                # Redimensionar manteniendo proporción, máx 120x120
                img.thumbnail((120, 120), Image.LANCZOS)
                # Fondo transparente → color del sidebar
                bg_img = Image.new("RGBA", img.size, (30, 41, 59, 255))
                bg_img.paste(img, mask=img.split()[3])
                self._logo_img = ImageTk.PhotoImage(bg_img.convert("RGB"))
                tk.Label(top, image=self._logo_img,
                         bg=COLORS['bg_sidebar']).pack()
                logo_loaded = True
            except ImportError:
                # PIL no disponible, usar tkinter PhotoImage para PNG
                try:
                    self._logo_img = tk.PhotoImage(file=logo_path)
                    # Escalar si es muy grande
                    orig_w = self._logo_img.width()
                    if orig_w > 120:
                        factor = orig_w // 120 + 1
                        self._logo_img = self._logo_img.subsample(factor, factor)
                    tk.Label(top, image=self._logo_img,
                             bg=COLORS['bg_sidebar']).pack()
                    logo_loaded = True
                except Exception:
                    pass
            except Exception:
                pass

        if not logo_loaded:
            # Fallback: texto si no hay imagen
            tk.Label(top, text="🏪",
                     font=(FONTS['family'], 48),
                     bg=COLORS['bg_sidebar'],
                     fg=COLORS['text_white']).pack()

        tk.Label(top, text="Venialgo Sistemas POS",
                 font=(FONTS['family'], FONTS['body'], 'bold'),
                 bg=COLORS['bg_sidebar'],
                 fg=COLORS['text_white']).pack(pady=(6, 0))
        tk.Label(top, text="Inicie sesión para continuar",
                 font=(FONTS['family'], FONTS['small']),
                 bg=COLORS['bg_sidebar'],
                 fg='#94a3b8').pack()

        # ── Card blanca ──────────────────────────────
        card = tk.Frame(self.root, bg=COLORS['bg_card'],
                        padx=32, pady=28)
        card.pack(fill='both', expand=True, padx=28, pady=8)

        # Usuario
        tk.Label(card, text="Usuario",
                 font=(FONTS['family'], FONTS['body'], 'bold'),
                 bg=COLORS['bg_card'], fg='#374151').pack(anchor='w')
        self._var_usr = tk.StringVar()
        tk.Entry(card, textvariable=self._var_usr,
                 font=(FONTS['family'], 11),
                 relief='solid', bd=1).pack(fill='x', pady=(3,14))

        # Contraseña
        tk.Label(card, text="Contraseña",
                 font=(FONTS['family'], FONTS['body'], 'bold'),
                 bg=COLORS['bg_card'], fg='#374151').pack(anchor='w')
        self._var_pwd = tk.StringVar()
        tk.Entry(card, textvariable=self._var_pwd,
                 show='●', font=(FONTS['family'], 11),
                 relief='solid', bd=1).pack(fill='x', pady=(3,22))

        # Botón
        btn = tk.Button(card, text="INGRESAR",
                        command=self._login,
                        bg=COLORS['primary'],
                        fg=COLORS['text_white'],
                        font=(FONTS['family'], 11, 'bold'),
                        relief='flat', pady=10, cursor='hand2')
        btn.pack(fill='x')

        tk.Label(card,
                 text="Usuario por defecto: admin / admin123",
                 font=(FONTS['family'], FONTS['small']),
                 bg=COLORS['bg_card'], fg='#cbd5e1').pack(pady=(12,0))

        # Footer
        add_footer(self.root)
        self.root.bind('<Return>', lambda e: self._login())

    def _login(self):
        usr = self._var_usr.get().strip()
        pwd = self._var_pwd.get().strip()
        if not usr or not pwd:
            messagebox.showwarning("Atención",
                                   "Complete usuario y contraseña.")
            return
        result = verify_login(usr, pwd)
        if result:
            uid, nombre, rol = result
            self.root.destroy()
            self.on_success(uid, nombre, rol)
        else:
            messagebox.showerror("Error de acceso",
                "Credenciales incorrectas o usuario inactivo.\n\n"
                "Usuario por defecto: admin\n"
                "Contrasena por defecto: admin123",
                parent=self.root)
