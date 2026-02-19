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

DB_FILE = "pos_database.db"

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
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""SELECT id,nombre,rol FROM usuarios
                     WHERE usuario=? AND password=? AND activo=1""",
                  (usuario, hpwd))
        row = c.fetchone()
        conn.close()
        return row
    except Exception:
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

        self.root.title("Sistema POS — Iniciar Sesión")
        self.root.geometry("420x540")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS['bg_sidebar'])
        self._center()
        self._build()

    def _center(self):
        self.root.update_idletasks()
        w, h = 420, 540
        x = (self.root.winfo_screenwidth()  - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        # ── Encabezado azul ──────────────────────────
        top = tk.Frame(self.root, bg=COLORS['bg_sidebar'])
        top.pack(fill='x', pady=(40, 20))
        tk.Label(top, text="🏪",
                 font=(FONTS['family'], 52),
                 bg=COLORS['bg_sidebar'],
                 fg=COLORS['text_white']).pack()
        tk.Label(top, text="Sistema POS",
                 font=(FONTS['family'], FONTS['title'], 'bold'),
                 bg=COLORS['bg_sidebar'],
                 fg=COLORS['text_white']).pack()
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
            messagebox.showerror("Error",
                                 "Credenciales incorrectas o usuario inactivo.")