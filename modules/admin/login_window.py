# -*- coding: utf-8 -*-
"""
login_window.py — Venialgo Sistemas POS
Diseño tipo imagen 2: tarjeta bicolor, header azul + cuerpo gris claro
"""

import tkinter as tk
from tkinter import messagebox
import sqlite3, hashlib, os, sys

# ── Paleta ─────────────────────────────────────────────────────────────────
C = {
    "bg_outer":   "#0B1A3B",   # Fondo exterior azul muy oscuro
    "card_top":   "#1A3468",   # Header de la tarjeta azul medio
    "card_top2":  "#1E3A72",   # Gradiente header
    "card_bot":   "#F0F3FA",   # Cuerpo gris azulado claro
    "input_bg":   "#FFFFFF",
    "input_brd":  "#D1D9EE",
    "input_foc":  "#3B6FE0",
    "btn_blue":   "#2F5FDB",
    "btn_hover":  "#2450C8",
    "btn_click":  "#1A3FA8",
    "text_white": "#FFFFFF",
    "text_sub":   "#A8BCD8",   # Subtítulo en header
    "text_dark":  "#1A2B4A",
    "text_label": "#4A5B7A",
    "text_hint":  "#8A9BBF",
    "footer_bg":  "#E4EAF5",
    "footer_txt": "#6B7FA8",
    "green_icon": "#2ECC40",
}
FONT = "Segoe UI"

# ── DB helpers ──────────────────────────────────────────────────────────────
def _get_db():
    base = os.environ.get("APPDATA", os.path.expanduser("~")) \
           if sys.platform == "win32" else os.path.expanduser("~")
    d = os.path.join(base, "VenialgoPOS")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "pos_database.db")

FOOTER_INFO = {
    "email":    "davenialgo@proton.me",
    "whatsapp": "+595 994-686 493",
}

def verify_login(usuario, password):
    hpwd = hashlib.sha256(password.encode()).hexdigest()
    try:
        from modules.admin.admin_ui import _ensure_tables
        _ensure_tables()
    except Exception:
        pass
    try:
        conn = sqlite3.connect(_get_db())
        c = conn.cursor()
        c.execute("SELECT id,nombre,rol FROM usuarios "
                  "WHERE usuario=? AND password=? AND activo=1", (usuario, hpwd))
        row = c.fetchone()
        conn.close()
        return row
    except Exception:
        return None

# ── Input moderno ──────────────────────────────────────────────────────────
class FlatEntry(tk.Frame):
    def __init__(self, parent, show=None, **kw):
        super().__init__(parent, bg=C["card_bot"], **kw)
        self._border = tk.Frame(self, bg=C["input_brd"])
        self._border.pack(fill='x', ipady=1)
        inner = tk.Frame(self._border, bg=C["input_bg"])
        inner.pack(fill='x', padx=1, pady=1)
        self._show = show
        self._var  = tk.StringVar()
        self._e = tk.Entry(inner, textvariable=self._var,
                           show=show or "",
                           font=(FONT, 11),
                           bg=C["input_bg"],
                           fg=C["text_dark"],
                           relief='flat', bd=0,
                           insertbackground=C["btn_blue"])
        self._e.pack(fill='x', padx=14, pady=10)
        self._e.bind('<FocusIn>',  lambda _: self._border.config(bg=C["input_foc"]))
        self._e.bind('<FocusOut>', lambda _: self._border.config(bg=C["input_brd"]))

    def get(self):     return self._var.get()
    def focus(self):   self._e.focus()

# ── Botón hover ────────────────────────────────────────────────────────────
class BlueBtn(tk.Label):
    def __init__(self, parent, text, command, **kw):
        super().__init__(parent, text=text,
                         font=(FONT, 12, 'bold'),
                         bg=C["btn_blue"], fg=C["text_white"],
                         cursor='hand2', pady=14, **kw)
        self._cmd = command
        self.bind('<Enter>',          lambda _: self.config(bg=C["btn_hover"]))
        self.bind('<Leave>',          lambda _: self.config(bg=C["btn_blue"]))
        self.bind('<Button-1>',       lambda _: self.config(bg=C["btn_click"]))
        self.bind('<ButtonRelease-1>',lambda _: (self.config(bg=C["btn_hover"]), self._cmd()))

# ══════════════════════════════════════════════════════════════════════════════
class LoginWindow:
    W, H = 440, 600

    def __init__(self, root, on_success):
        self.root       = root
        self.on_success = on_success
        self.root.title("Venialgo Sistemas POS")
        self.root.resizable(False, False)
        self.root.configure(bg=C["bg_outer"])
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self._center()
        self._build()

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()  - self.W) // 2
        y = (self.root.winfo_screenheight() - self.H) // 2
        self.root.geometry(f"{self.W}x{self.H}+{x}+{y}")

    def _build(self):
        # Tarjeta ocupa toda la ventana
        self.root.configure(bg=C["card_top"])
        card = tk.Frame(self.root, bg=C["card_top"])
        card.pack(fill='both', expand=True)

        self._build_header(card)
        self._build_body(card)
        self.root.bind('<Return>', lambda e: self._login())

    def _build_header(self, card):
        """Sección azul oscura con logo y título."""
        top = tk.Frame(card, bg=C["card_top"])
        top.pack(fill='x')

        # Logo
        logo_frame = tk.Frame(top, bg=C["card_top"])
        logo_frame.pack(pady=(28, 8))

        self._logo_img = None
        logo_path = self._find_logo()
        logo_ok = False

        if logo_path:
            try:
                from PIL import Image, ImageTk
                img = Image.open(logo_path).convert("RGBA")
                img.thumbnail((110, 110), Image.LANCZOS)
                bg_img = Image.new("RGBA", img.size,
                                   tuple(int(C["card_top"].lstrip('#')[i:i+2],16)
                                         for i in (0,2,4)) + (255,))
                bg_img.paste(img, mask=img.split()[3])
                self._logo_img = ImageTk.PhotoImage(bg_img.convert("RGB"))
                tk.Label(logo_frame, image=self._logo_img,
                         bg=C["card_top"]).pack()
                logo_ok = True
            except Exception:
                try:
                    self._logo_img = tk.PhotoImage(file=logo_path)
                    w = self._logo_img.width()
                    if w > 110:
                        f = max(1, w // 110)
                        self._logo_img = self._logo_img.subsample(f, f)
                    tk.Label(logo_frame, image=self._logo_img,
                             bg=C["card_top"]).pack()
                    logo_ok = True
                except Exception:
                    pass

        if not logo_ok:
            tk.Label(logo_frame, text="V",
                     font=(FONT, 32, 'bold'),
                     bg="#2451B5", fg="white",
                     width=3, pady=10).pack()

        # Nombre app
        tk.Label(top, text="Venialgo Sistemas POS",
                 font=(FONT, 14, 'bold'),
                 bg=C["card_top"], fg=C["text_white"]).pack(pady=(8, 3))
        tk.Label(top, text="Inicie sesión para continuar",
                 font=(FONT, 9),
                 bg=C["card_top"], fg=C["text_sub"]).pack(pady=(0, 24))

    def _build_body(self, card):
        """Sección gris clara con formulario."""
        body = tk.Frame(card, bg=C["card_bot"])
        body.pack(fill='both', expand=True)

        form = tk.Frame(body, bg=C["card_bot"], padx=36)
        form.pack(fill='x', pady=(28, 0))

        # ── Usuario ───────────────────────────────────────────
        row_u = tk.Frame(form, bg=C["card_bot"])
        row_u.pack(fill='x', pady=(0, 4))
        tk.Label(row_u, text="👤", bg=C["card_bot"],
                 font=(FONT, 11)).pack(side='left', padx=(0,6))
        tk.Label(row_u, text="Usuario",
                 font=(FONT, 10, 'bold'),
                 bg=C["card_bot"], fg=C["text_label"]).pack(side='left')

        self._entry_usr = FlatEntry(form)
        self._entry_usr.pack(fill='x', pady=(0, 18))
        self._entry_usr.focus()

        # ── Contraseña ────────────────────────────────────────
        row_p = tk.Frame(form, bg=C["card_bot"])
        row_p.pack(fill='x', pady=(0, 4))
        tk.Label(row_p, text="🔒", bg=C["card_bot"],
                 font=(FONT, 11)).pack(side='left', padx=(0,6))
        tk.Label(row_p, text="Contraseña",
                 font=(FONT, 10, 'bold'),
                 bg=C["card_bot"], fg=C["text_label"]).pack(side='left')

        self._entry_pwd = FlatEntry(form, show="●")
        self._entry_pwd.pack(fill='x', pady=(0, 22))

        # ── Botón ─────────────────────────────────────────────
        BlueBtn(form, text="✅  INGRESAR",
                command=self._login).pack(fill='x')

        # ── Hint ──────────────────────────────────────────────
        tk.Label(body,
                 text="Usuario por defecto:  admin  /  admin123",
                 font=(FONT, 8), bg=C["card_bot"],
                 fg=C["text_hint"]).pack(pady=(14, 0))

        # ── Footer dentro de tarjeta ──────────────────────────
        footer = tk.Frame(body, bg=C["footer_bg"])
        footer.pack(fill='x', side='bottom', pady=(18, 0))
        tk.Frame(body, bg="#C8D4EE", height=1).pack(fill='x', side='bottom')

        txt = (f"  ✉  {FOOTER_INFO['email']}"
               f"   |   📱  WhatsApp: {FOOTER_INFO['whatsapp']}  ")
        tk.Label(footer, text=txt,
                 font=(FONT, 8), bg=C["footer_bg"],
                 fg=C["footer_txt"]).pack(pady=8)

    def _find_logo(self):
        paths = [
            os.path.join(os.path.dirname(sys.executable), "assets", "VenialgoSistemasLogo.png"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "VenialgoSistemasLogo.png"),
            "assets/VenialgoSistemasLogo.png",
            "VenialgoSistemasLogo.png",
        ]
        for p in paths:
            try:
                if os.path.exists(p): return p
            except Exception: pass
        return None

    def _login(self):
        usr = self._entry_usr.get().strip()
        pwd = self._entry_pwd.get().strip()
        if not usr or not pwd:
            self._shake(); return
        result = verify_login(usr, pwd)
        if result:
            uid, nombre, rol = result
            self.root.destroy()
            self.on_success(uid, nombre, rol)
        else:
            self._shake()
            messagebox.showerror("Acceso denegado",
                "Usuario o contraseña incorrectos.\n\n"
                "Por defecto:  admin  /  admin123",
                parent=self.root)

    def _shake(self):
        ox = self.root.winfo_x()
        oy = self.root.winfo_y()
        for d in [10,-10,8,-8,5,-5,3,-3,0]:
            self.root.geometry(f"{self.W}x{self.H}+{ox+d}+{oy}")
            self.root.update()
            self.root.after(20)
