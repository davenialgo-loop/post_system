# -*- coding: utf-8 -*-
"""
login_window.py  —  Venialgo Sistemas POS
Diseño tipo imagen de referencia: header oscuro + card blanca
"""

import tkinter as tk
from tkinter import messagebox
import sqlite3, hashlib, os, sys

try:
    from utils.window_icon import set_icon as _set_icon
except Exception:
    def _set_icon(w): pass

# ── Paleta ─────────────────────────────────────────────────────────────────
DARK1  = "#0A1628"   # azul muy oscuro top
DARK2  = "#0F2347"   # azul oscuro mid
DARK3  = "#1A3A7A"   # azul header bottom
WHITE  = "#FFFFFF"
CARD   = "#F4F7FF"   # fondo card ligeramente azulado
BLUE   = "#1A4FCC"   # botón principal
BLUE_H = "#1340A8"   # hover botón
BORDER = "#D0DCF0"
TXT_D  = "#0F1E3A"
TXT_S  = "#6B7FA8"
TXT_W  = "#FFFFFF"
FONT   = "Segoe UI"

FOOTER_INFO = {
    "email":    "davenialgo@proton.me",
    "whatsapp": "+595 994-686 493",
    "web":      "www.venialgosistemas.com",
}

# ── DB ─────────────────────────────────────────────────────────────────────
def _get_db():
    base = os.environ.get("APPDATA", os.path.expanduser("~")) if sys.platform == "win32" else os.path.expanduser("~")
    d = os.path.join(base, "VenialgoPOS"); os.makedirs(d, exist_ok=True)
    return os.path.join(d, "pos_database.db")

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
        c.execute("SELECT id,nombre,rol FROM usuarios WHERE usuario=? AND password=? AND activo=1", (usuario, hpwd))
        row = c.fetchone(); conn.close(); return row
    except Exception:
        return None

# ── Diálogo personalizado ──────────────────────────────────────────────────
def _dialog(parent, title, msg, kind="error"):
    KINDS = {"error": ("#E11D48","✖"), "warning": ("#D97706","⚠"), "info": ("#059669","✔")}
    accent, icon_ch = KINDS.get(kind, KINDS["error"])
    dlg = tk.Toplevel(parent); _set_icon(dlg)
    dlg.title(title); dlg.resizable(False, False)
    dlg.configure(bg=WHITE); dlg.transient(parent); dlg.grab_set()
    dlg.update_idletasks()
    w, h = 380, 170
    px = parent.winfo_rootx() + (parent.winfo_width()  - w) // 2
    py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
    dlg.geometry(f"{w}x{h}+{px}+{py}")
    tk.Frame(dlg, bg=accent, height=5).pack(fill='x')
    body = tk.Frame(dlg, bg=WHITE, padx=24, pady=18); body.pack(fill='both', expand=True)
    row = tk.Frame(body, bg=WHITE); row.pack(fill='x', pady=(0,14))
    tk.Label(row, text=icon_ch, font=(FONT,20,"bold"), bg=WHITE, fg=accent).pack(side='left', padx=(0,14))
    tk.Label(row, text=msg, font=(FONT,10), bg=WHITE, fg=TXT_D, wraplength=270, justify='left').pack(side='left', anchor='w')
    def _close(): dlg.grab_release(); dlg.destroy()
    btn = tk.Label(body, text="  Aceptar  ", font=(FONT,10,"bold"), bg=accent, fg=WHITE, cursor="hand2", padx=16, pady=8)
    btn.pack(anchor='e')
    btn.bind("<ButtonRelease-1>", lambda e: _close())
    dlg.bind("<Return>", lambda e: _close()); dlg.bind("<Escape>", lambda e: _close())
    parent.wait_window(dlg)

# ══════════════════════════════════════════════════════════════════════════
#  WIDGET: Entrada estilizada
# ══════════════════════════════════════════════════════════════════════════
class StyledEntry(tk.Frame):
    def __init__(self, parent, show=None, **kw):
        super().__init__(parent, bg=WHITE, **kw)
        self._border = tk.Frame(self, bg=BORDER)
        self._border.pack(fill='x', ipady=1)
        inner = tk.Frame(self._border, bg=WHITE)
        inner.pack(fill='x', padx=1, pady=1)
        self._var = tk.StringVar()
        self._entry = tk.Entry(inner, textvariable=self._var,
            show=show or "", font=(FONT, 11), bg=WHITE, fg=TXT_D,
            relief='flat', bd=0, insertbackground=BLUE)
        self._entry.pack(fill='x', padx=12, ipady=10)
        self._entry.bind('<FocusIn>',  lambda e: self._border.config(bg=BLUE))
        self._entry.bind('<FocusOut>', lambda e: self._border.config(bg=BORDER))

    def get(self):
        return self._var.get()

    def focus(self):
        self._entry.focus()

# ══════════════════════════════════════════════════════════════════════════
#  VENTANA LOGIN
# ══════════════════════════════════════════════════════════════════════════
class LoginWindow:

    W, H = 440, 640

    def __init__(self, root, on_success):
        self.root = root
        self.on_success = on_success
        self.root.title("Venialgo Sistemas POS — Iniciar Sesión")
        self.root.geometry(f"{self.W}x{self.H}")
        self.root.resizable(False, False)
        self.root.configure(bg=DARK1)
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        _set_icon(self.root)
        self._center()
        self._build()

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()  - self.W) // 2
        y = (self.root.winfo_screenheight() - self.H) // 2
        self.root.geometry(f"{self.W}x{self.H}+{x}+{y}")

    def _build(self):
        # ── Footer PRIMERO (regla tkinter side=bottom antes que side=left) ──
        self._build_footer()
        # ── Header oscuro con logo ──
        self._build_header()
        # ── Card blanca con formulario ──
        self._build_card()
        self.root.bind('<Return>', lambda e: self._login())

    def _build_footer(self):
        bar = tk.Frame(self.root, bg=DARK1, height=28)
        bar.pack(side='bottom', fill='x')
        bar.pack_propagate(False)
        txt = f"  ✉ {FOOTER_INFO['email']}   │   📱 {FOOTER_INFO['whatsapp']}   │   🌐 {FOOTER_INFO['web']}  "
        tk.Label(bar, text=txt, bg=DARK1, fg="#4A6080", font=(FONT, 8)).pack(side='left', pady=6)

    def _build_header(self):
        """Header azul oscuro degradado con logo y texto."""
        # Canvas para degradado
        HDR_H = 220
        canvas = tk.Canvas(self.root, width=self.W, height=HDR_H,
                           highlightthickness=0, bd=0)
        canvas.pack(fill='x')

        # Degradado de arriba a abajo
        steps = HDR_H
        r1,g1,b1 = 0x0A,0x16,0x28
        r2,g2,b2 = 0x1A,0x3A,0x7A
        for i in range(steps):
            t = i / steps
            r = int(r1 + (r2-r1)*t)
            g = int(g1 + (g2-g1)*t)
            b = int(b1 + (b2-b1)*t)
            canvas.create_line(0, i, self.W, i, fill=f"#{r:02x}{g:02x}{b:02x}")

        # Círculos decorativos
        canvas.create_oval(300, -30, 500, 170, fill="", outline="#1E3A6E", width=1)
        canvas.create_oval(320, -10, 480, 150, fill="", outline="#162C56", width=1)

        # Logo
        logo_path = self._find_logo()
        self._logo_img = None
        logo_y = 50
        if logo_path:
            try:
                from PIL import Image, ImageTk
                img = Image.open(logo_path).convert("RGBA")
                img.thumbnail((90, 90), Image.LANCZOS)
                # Fondo transparente sobre el canvas
                bg_img = Image.new("RGBA", img.size, (0,0,0,0))
                bg_img.paste(img, mask=img.split()[3])
                self._logo_img = ImageTk.PhotoImage(bg_img)
                canvas.create_image(self.W//2, logo_y + 45, image=self._logo_img)
                logo_y += 100
            except Exception:
                logo_y = 30
                canvas.create_text(self.W//2, logo_y + 30,
                    text="🏪", font=(FONT, 42), fill=TXT_W)
                logo_y += 72
        else:
            canvas.create_text(self.W//2, logo_y + 30,
                text="🏪", font=(FONT, 42), fill=TXT_W)
            logo_y += 72

        # Texto "Venialgo Sistemas POS"
        canvas.create_text(self.W//2, logo_y + 8,
            text="Venialgo Sistemas POS",
            font=(FONT, 15, 'bold'), fill=TXT_W)
        canvas.create_text(self.W//2, logo_y + 32,
            text="Inicie sesión para continuar",
            font=(FONT, 9), fill="#8AABD4")

    def _build_card(self):
        """Tarjeta blanca con el formulario de login."""
        card = tk.Frame(self.root, bg=WHITE)
        card.pack(fill='both', expand=True)

        # Sombra superior simulada
        tk.Frame(card, bg="#C8D8F0", height=2).pack(fill='x')

        inner = tk.Frame(card, bg=WHITE, padx=40, pady=28)
        inner.pack(fill='both', expand=True)

        # ── Campo usuario ──
        usr_row = tk.Frame(inner, bg=WHITE); usr_row.pack(fill='x', pady=(0,4))
        tk.Label(usr_row, text="👤  Usuario", font=(FONT,10,'bold'),
                 bg=WHITE, fg=TXT_D).pack(anchor='w')
        self._entry_usr = StyledEntry(inner)
        self._entry_usr.pack(fill='x', pady=(4,16))

        # ── Campo contraseña ──
        pwd_row = tk.Frame(inner, bg=WHITE); pwd_row.pack(fill='x', pady=(0,4))
        tk.Label(pwd_row, text="🔒  Contraseña", font=(FONT,10,'bold'),
                 bg=WHITE, fg=TXT_D).pack(anchor='w')
        self._entry_pwd = StyledEntry(inner, show="●")
        self._entry_pwd.pack(fill='x', pady=(4,28))

        # ── Botón INGRESAR ──
        self._btn = tk.Label(inner, text="  ✅  INGRESAR  ",
            font=(FONT, 12, 'bold'), bg=BLUE, fg=TXT_W,
            cursor='hand2', pady=13, anchor='center')
        self._btn.pack(fill='x')
        self._btn.bind('<Enter>',           lambda e: self._btn.config(bg=BLUE_H))
        self._btn.bind('<Leave>',           lambda e: self._btn.config(bg=BLUE))
        self._btn.bind('<Button-1>',        lambda e: self._btn.config(bg="#0F3288"))
        self._btn.bind('<ButtonRelease-1>', lambda e: (self._btn.config(bg=BLUE_H), self._login()))

        # ── Hint credenciales ──
        tk.Label(inner, text="Usuario por defecto: admin / admin123",
                 font=(FONT, 8), bg=WHITE, fg=TXT_S).pack(pady=(16,0))

        # ── Version badge ──
        tk.Label(inner, text=" v1.1 ", font=(FONT, 7, 'bold'),
                 bg="#EBF2FF", fg=BLUE, padx=6, pady=2).pack(pady=(8,0))

        self._entry_usr.focus()

    def _find_logo(self):
        paths = [
            os.path.join(os.path.dirname(sys.executable), "assets", "VenialgoSistemasLogo.png"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "VenialgoSistemasLogo.png"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "VenialgoSistemasLogo.png"),
            "assets/VenialgoSistemasLogo.png",
            "VenialgoSistemasLogo.png",
        ]
        for p in paths:
            try:
                if os.path.exists(p): return p
            except Exception:
                pass
        return None

    def _login(self):
        usr = self._entry_usr.get().strip()
        pwd = self._entry_pwd.get().strip()
        if not usr or not pwd:
            self._shake()
            _dialog(self.root, "Atención", "Complete usuario y contraseña.", "warning")
            return
        result = verify_login(usr, pwd)
        if result:
            uid, nombre, rol = result
            self.root.destroy()
            self.on_success(uid, nombre, rol)
        else:
            self._shake()
            _dialog(self.root, "Acceso denegado",
                "Credenciales incorrectas o usuario inactivo.\n\n"
                "Por defecto: admin / admin123", "error")

    def _shake(self):
        ox, oy = self.root.winfo_x(), self.root.winfo_y()
        for d in [8,-8,6,-6,4,-4,2,-2,0]:
            self.root.geometry(f"{self.W}x{self.H}+{ox+d}+{oy}")
            self.root.update(); self.root.after(18)
