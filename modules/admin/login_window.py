"""
Ventana de Login — Venialgo Sistemas POS
"""

import tkinter as tk
from tkinter import messagebox
import sqlite3, hashlib, os, sys
from datetime import datetime

FONT    = "Segoe UI"
DB_FILE = "pos_database.db"

# Colores
C_HEADER_TOP = "#0D1B4B"   # azul muy oscuro arriba
C_HEADER_BOT = "#1A3A8F"   # azul medio abajo del header
C_FORM_BG    = "#EFF3F8"   # gris azulado claro
C_WHITE      = "#FFFFFF"
C_BLUE_BTN   = "#2D55CC"
C_BLUE_HOV   = "#1D45BC"
C_BORDER     = "#C8D4E8"
C_TXT_MAIN   = "#1A1A2E"
C_TXT_MUTED  = "#7A8BAA"
C_FOOTER_BG  = "#0D1B4B"
C_FOOTER_FG  = "#7A8BAA"

FOOTER_INFO = {
    "email":    "davenialgo@proton.me",
    "whatsapp": "+595 994-686 493",
    "web":      "www.venialgosistemas.com",
}


def _find_asset(filename):
    if getattr(sys, "frozen", False):
        start = os.path.dirname(sys.executable)
    else:
        start = os.path.dirname(os.path.abspath(__file__))
    cur = start
    for _ in range(4):
        candidate = os.path.join(cur, "assets", filename)
        if os.path.isfile(candidate):
            return candidate
        cur = os.path.dirname(cur)
    return None


def _apply_icon(window):
    for name in ["venialgosist.ico", "app_icon.ico"]:
        path = _find_asset(name)
        if path:
            try:
                window.iconbitmap(path)
                return
            except Exception:
                pass
    path = _find_asset("VenialgoSistemasLogo.png")
    if path:
        try:
            from PIL import Image, ImageTk
            img   = Image.open(path).resize((32, 32), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            window.iconphoto(True, photo)
            window._icon_ref = photo
        except Exception:
            pass


def _load_logo(size=110):
    path = _find_asset("VenialgoSistemasLogo.png")
    if not path:
        return None
    try:
        from PIL import Image, ImageTk
        img = Image.open(path).convert("RGBA")
        # Eliminar fondo negro pixel a pixel sin numpy
        pixels = img.load()
        w_, h_ = img.size
        for y in range(h_):
            for x in range(w_):
                r, g, b, a = pixels[x, y]
                if r < 30 and g < 30 and b < 30:
                    pixels[x, y] = (r, g, b, 0)
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
        img.thumbnail((size, size), Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


def verify_login(usuario, password):
    hpwd = hashlib.sha256(password.encode()).hexdigest()
    try:
        conn = sqlite3.connect(DB_FILE)
        c    = conn.cursor()
        c.execute("""SELECT id,nombre,rol FROM usuarios
                     WHERE usuario=? AND password=? AND activo=1""",
                  (usuario, hpwd))
        row  = c.fetchone()
        conn.close()
        return row
    except Exception:
        return None


class LoginWindow:
    def __init__(self, root, on_success):
        self.root       = root
        self.on_success = on_success
        self.root.title("Sistema POS — Iniciar Sesión")
        self.root.resizable(False, False)
        self.root.configure(bg=C_HEADER_TOP)
        _apply_icon(self.root)
        self._build()
        self._center()

    def _center(self):
        self.root.update_idletasks()
        w = self.root.winfo_reqwidth()
        h = self.root.winfo_reqheight()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        W = 400   # ancho fijo de la ventana

        # ══════════════════════════════════════════
        # HEADER — fondo degradado simulado con canvas
        # ══════════════════════════════════════════
        hdr_h = 230
        canvas = tk.Canvas(self.root, width=W, height=hdr_h,
                           highlightthickness=0, bd=0)
        canvas.pack(fill="x")

        # Degradado vertical: dibujar líneas horizontales de C_HEADER_TOP → C_HEADER_BOT
        def hex_to_rgb(h):
            h = h.lstrip("#")
            return tuple(int(h[i:i+2],16) for i in (0,2,4))

        r1,g1,b1 = hex_to_rgb(C_HEADER_TOP)
        r2,g2,b2 = hex_to_rgb(C_HEADER_BOT)
        for i in range(hdr_h):
            t  = i / hdr_h
            r  = int(r1 + (r2-r1)*t)
            g  = int(g1 + (g2-g1)*t)
            b  = int(b1 + (b2-b1)*t)
            color = f"#{r:02x}{g:02x}{b:02x}"
            canvas.create_line(0, i, W, i, fill=color)

        # Logo — guardar en self para evitar que el GC lo destruya
        self._logo_photo = _load_logo(size=110)
        if self._logo_photo:
            canvas.create_image(W//2, 85, image=self._logo_photo, anchor="center")
        else:
            canvas.create_text(W//2, 80, text="🏪",
                               font=(FONT, 48), fill=C_WHITE, anchor="center")

        # Texto VENIALGO SISTEMAS (simulamos con dos labels sobre el canvas)
        # usamos create_text con fuentes grandes
        canvas.create_text(W//2, 155, text="Venialgo Sistemas POS",
                           font=(FONT, 16, "bold"), fill=C_WHITE, anchor="center")
        canvas.create_text(W//2, 178, text="Inicie sesión para continuar",
                           font=(FONT, 9), fill="#9DB4E0", anchor="center")

        # ══════════════════════════════════════════
        # FORMULARIO — panel blanco/gris
        # ══════════════════════════════════════════
        form = tk.Frame(self.root, bg=C_FORM_BG, padx=32, pady=28)
        form.pack(fill="x")

        # ── Campo Usuario ──────────────────────────
        row_u = tk.Frame(form, bg=C_FORM_BG)
        row_u.pack(fill="x", pady=(0, 4))
        tk.Label(row_u, text="👤  Usuario",
                 font=(FONT, 10, "bold"), bg=C_FORM_BG,
                 fg=C_TXT_MAIN).pack(anchor="w")

        self._var_usr = tk.StringVar()
        frm_u = tk.Frame(form, bg=C_BORDER, padx=1, pady=1)
        frm_u.pack(fill="x", pady=(0, 16))
        self._ent_usr = tk.Entry(frm_u, textvariable=self._var_usr,
                                 font=(FONT, 11), relief="flat",
                                 bg=C_WHITE, fg=C_TXT_MAIN,
                                 insertbackground=C_BLUE_BTN)
        self._ent_usr.pack(fill="x", ipady=8, padx=2)
        self._ent_usr.bind("<FocusIn>",  lambda e: frm_u.config(bg=C_BLUE_BTN))
        self._ent_usr.bind("<FocusOut>", lambda e: frm_u.config(bg=C_BORDER))

        # ── Campo Contraseña ───────────────────────
        tk.Label(form, text="🔒  Contraseña",
                 font=(FONT, 10, "bold"), bg=C_FORM_BG,
                 fg=C_TXT_MAIN).pack(anchor="w", pady=(0, 4))

        self._var_pwd = tk.StringVar()
        frm_p = tk.Frame(form, bg=C_BORDER, padx=1, pady=1)
        frm_p.pack(fill="x", pady=(0, 22))
        self._ent_pwd = tk.Entry(frm_p, textvariable=self._var_pwd,
                                 show="•", font=(FONT, 11), relief="flat",
                                 bg=C_WHITE, fg=C_TXT_MAIN,
                                 insertbackground=C_BLUE_BTN)
        self._ent_pwd.pack(fill="x", ipady=8, padx=2)
        self._ent_pwd.bind("<FocusIn>",  lambda e: frm_p.config(bg=C_BLUE_BTN))
        self._ent_pwd.bind("<FocusOut>", lambda e: frm_p.config(bg=C_BORDER))

        # ── Botón Ingresar ─────────────────────────
        btn = tk.Label(form, text="  ✅  INGRESAR",
                       font=(FONT, 12, "bold"),
                       bg=C_BLUE_BTN, fg=C_WHITE,
                       cursor="hand2", pady=13)
        btn.pack(fill="x")
        btn.bind("<Enter>",           lambda e: btn.config(bg=C_BLUE_HOV))
        btn.bind("<Leave>",           lambda e: btn.config(bg=C_BLUE_BTN))
        btn.bind("<ButtonRelease-1>", lambda e: self._login())

        # ── Hint ──────────────────────────────────
        tk.Label(form, text="Usuario por defecto: admin / admin123",
                 font=(FONT, 8), bg=C_FORM_BG,
                 fg=C_TXT_MUTED).pack(pady=(12, 0))

        # ══════════════════════════════════════════
        # FOOTER
        # ══════════════════════════════════════════
        footer = tk.Frame(self.root, bg=C_FOOTER_BG)
        footer.pack(fill="x")
        tk.Label(footer,
                 text=f"  ✉ {FOOTER_INFO['email']}   |   "
                      f"📱 WhatsApp: {FOOTER_INFO['whatsapp']}   |   "
                      f"🌐 {FOOTER_INFO['web']}  ",
                 font=(FONT, 7), bg=C_FOOTER_BG,
                 fg=C_FOOTER_FG, pady=7).pack()

        # Binds
        self.root.bind("<Return>", lambda e: self._login())
        self._ent_usr.focus_set()

    def _login(self):
        usr = self._var_usr.get().strip()
        pwd = self._var_pwd.get().strip()
        if not usr or not pwd:
            messagebox.showwarning("Atención", "Complete usuario y contraseña.")
            return
        result = verify_login(usr, pwd)
        if result:
            uid, nombre, rol = result
            self.root.destroy()
            self.on_success(uid, nombre, rol)
        else:
            messagebox.showerror("Error",
                                 "Credenciales incorrectas o usuario inactivo.")
