# -*- coding: utf-8 -*-
"""
login_window.py — Venialgo Sistemas POS
"""

import tkinter as tk
from tkinter import messagebox
import sqlite3, hashlib, os, sys

C = {
    "grad_top":   "#0D2255",
    "grad_bot":   "#2451B5",
    "card_bot":   "#F0F3FA",
    "input_bg":   "#FFFFFF",
    "input_brd":  "#D1D9EE",
    "input_foc":  "#3B6FE0",
    "btn_blue":   "#2F5FDB",
    "btn_hover":  "#2450C8",
    "btn_click":  "#1A3FA8",
    "text_white": "#FFFFFF",
    "text_sub":   "#A8BCD8",
    "text_dark":  "#1A2B4A",
    "text_label": "#4A5B7A",
    "text_hint":  "#8A9BBF",
    "footer_bg":  "#E4EAF5",
    "footer_txt": "#6B7FA8",
    "hdr_mid":    "#1A3A88",   # Color base widgets sobre gradiente
}
FONT = "Segoe UI"

def _get_db():
    base = os.environ.get("APPDATA", os.path.expanduser("~")) \
           if sys.platform == "win32" else os.path.expanduser("~")
    d = os.path.join(base, "VenialgoPOS")
    os.makedirs(d, exist_ok=True)
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
        c.execute("SELECT id,nombre,rol FROM usuarios "
                  "WHERE usuario=? AND password=? AND activo=1", (usuario, hpwd))
        row = c.fetchone()
        conn.close()
        return row
    except Exception:
        return None


class FlatEntry(tk.Frame):
    def __init__(self, parent, show=None, **kw):
        super().__init__(parent, bg=C["card_bot"], **kw)
        self._border = tk.Frame(self, bg=C["input_brd"])
        self._border.pack(fill='x', ipady=1)
        inner = tk.Frame(self._border, bg=C["input_bg"])
        inner.pack(fill='x', padx=1, pady=1)
        self._var = tk.StringVar()
        self._e = tk.Entry(inner, textvariable=self._var,
                           show=show or "",
                           font=(FONT, 11),
                           bg=C["input_bg"], fg=C["text_dark"],
                           relief='flat', bd=0,
                           insertbackground=C["btn_blue"])
        self._e.pack(fill='x', padx=14, pady=10)
        self._e.bind('<FocusIn>',  lambda _: self._border.config(bg=C["input_foc"]))
        self._e.bind('<FocusOut>', lambda _: self._border.config(bg=C["input_brd"]))

    def get(self):   return self._var.get()
    def focus(self): self._e.focus()


class BlueBtn(tk.Label):
    def __init__(self, parent, text, command, **kw):
        super().__init__(parent, text=text,
                         font=(FONT, 12, 'bold'),
                         bg=C["btn_blue"], fg=C["text_white"],
                         cursor='hand2', pady=14, **kw)
        self._cmd = command
        self.bind('<Enter>',           lambda _: self.config(bg=C["btn_hover"]))
        self.bind('<Leave>',           lambda _: self.config(bg=C["btn_blue"]))
        self.bind('<Button-1>',        lambda _: self.config(bg=C["btn_click"]))
        self.bind('<ButtonRelease-1>', lambda _: (self.config(bg=C["btn_hover"]), self._cmd()))


class LoginWindow:
    W, H    = 440, 600
    HDR_H   = 250   # Altura fija del header

    def __init__(self, root, on_success):
        self.root       = root
        self.on_success = on_success
        self._gradient_drawn = False

        self.root.title("Venialgo Sistemas POS")
        self.root.resizable(False, False)
        self.root.configure(bg=C["grad_top"])
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self._center()
        self._build()

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()  - self.W) // 2
        y = (self.root.winfo_screenheight() - self.H) // 2
        self.root.geometry(f"{self.W}x{self.H}+{x}+{y}")

    def _build(self):
        # ── Header: Canvas con degradado ───────────────────────
        self._cv = tk.Canvas(self.root, width=self.W, height=self.HDR_H,
                             highlightthickness=0, bd=0)
        self._cv.pack(fill='x')

        # Dibujar gradiente UNA sola vez con after
        self.root.after(10, self._draw_gradient)

        # Widgets del header SOBRE el canvas
        self._build_header_widgets()

        # ── Cuerpo gris ─────────────────────────────────────────
        body = tk.Frame(self.root, bg=C["card_bot"])
        body.pack(fill='both', expand=True)
        self._build_body(body)

        self.root.bind('<Return>', lambda e: self._login())

    def _draw_gradient(self):
        """Dibuja el degradado vertical en el canvas del header."""
        w = self.W
        h = self.HDR_H
        r1, g1, b1 = 0x0D, 0x22, 0x55   # grad_top
        r2, g2, b2 = 0x24, 0x51, 0xB5   # grad_bot
        for i in range(h):
            t = i / h
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            self._cv.create_line(0, i, w, i, fill=f'#{r:02x}{g:02x}{b:02x}')
        # Elevar el frame de widgets sobre las líneas del canvas
        self._hdr_frame.lift()

    def _build_header_widgets(self):
        """Frame de widgets flotando sobre el canvas."""
        MID = C["hdr_mid"]
        frm = tk.Frame(self._cv, bg=MID, bd=0, highlightthickness=0)
        frm.place(x=0, y=0, width=self.W, height=self.HDR_H)
        self._hdr_frame = frm

        # Logo
        logo_frame = tk.Frame(frm, bg=MID)
        logo_frame.pack(pady=(22, 6))

        logo_ok   = False
        logo_path = self._find_logo()

        if logo_path:
            try:
                from PIL import Image, ImageTk
                img = Image.open(logo_path).convert("RGBA")
                img.thumbnail((100, 100), Image.LANCZOS)
                bg_img = Image.new("RGBA", img.size, (0x1A, 0x3A, 0x88, 255))
                bg_img.paste(img, mask=img.split()[3])
                self._logo_img = ImageTk.PhotoImage(bg_img.convert("RGB"))
                tk.Label(logo_frame, image=self._logo_img, bg=MID).pack()
                logo_ok = True
            except ImportError:
                try:
                    self._logo_img = tk.PhotoImage(file=logo_path)
                    w = self._logo_img.width()
                    if w > 100:
                        f = max(1, w // 100)
                        self._logo_img = self._logo_img.subsample(f, f)
                    tk.Label(logo_frame, image=self._logo_img, bg=MID).pack()
                    logo_ok = True
                except Exception:
                    pass
            except Exception:
                pass

        if not logo_ok:
            tk.Label(logo_frame, text="V", font=(FONT, 28, 'bold'),
                     bg=C["btn_blue"], fg="white",
                     width=3, pady=8).pack()

        tk.Label(frm, text="Venialgo Sistemas POS",
                 font=(FONT, 14, 'bold'),
                 bg=MID, fg=C["text_white"]).pack(pady=(6, 2))
        tk.Label(frm, text="Inicie sesión para continuar",
                 font=(FONT, 9),
                 bg=MID, fg=C["text_sub"]).pack()

    def _build_body(self, body):
        form = tk.Frame(body, bg=C["card_bot"], padx=36)
        form.pack(fill='x', pady=(24, 0))

        # Usuario
        row_u = tk.Frame(form, bg=C["card_bot"])
        row_u.pack(fill='x', pady=(0, 5))
        tk.Label(row_u, text="👤", bg=C["card_bot"], font=(FONT, 11)).pack(side='left', padx=(0, 6))
        tk.Label(row_u, text="Usuario", font=(FONT, 10, 'bold'),
                 bg=C["card_bot"], fg=C["text_label"]).pack(side='left')
        self._entry_usr = FlatEntry(form)
        self._entry_usr.pack(fill='x', pady=(0, 16))
        self._entry_usr.focus()

        # Contraseña
        row_p = tk.Frame(form, bg=C["card_bot"])
        row_p.pack(fill='x', pady=(0, 5))
        tk.Label(row_p, text="🔒", bg=C["card_bot"], font=(FONT, 11)).pack(side='left', padx=(0, 6))
        tk.Label(row_p, text="Contraseña", font=(FONT, 10, 'bold'),
                 bg=C["card_bot"], fg=C["text_label"]).pack(side='left')
        self._entry_pwd = FlatEntry(form, show="●")
        self._entry_pwd.pack(fill='x', pady=(0, 20))

        # Botón
        BlueBtn(form, text="☑  INGRESAR", command=self._login).pack(fill='x')

        # Hint
        tk.Label(body, text="Usuario por defecto:  admin  /  admin123",
                 font=(FONT, 8), bg=C["card_bot"], fg=C["text_hint"]).pack(pady=(12, 0))

        # Footer
        tk.Frame(body, bg="#C8D4EE", height=1).pack(fill='x', side='bottom')
        footer = tk.Frame(body, bg=C["footer_bg"])
        footer.pack(fill='x', side='bottom')
        tk.Label(footer,
                 text=f"  ✉  davenialgo@proton.me   |   📱  WhatsApp: +595 994-686 493  ",
                 font=(FONT, 8), bg=C["footer_bg"], fg=C["footer_txt"]).pack(pady=7)

    def _find_logo(self):
        paths = [
            os.path.join(os.path.dirname(sys.executable), "assets", "VenialgoSistemasLogo.png"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "VenialgoSistemasLogo.png"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "VenialgoSistemasLogo.png"),
            "assets/VenialgoSistemasLogo.png",
            "VenialgoSistemasLogo.png",
        ]
        for p in paths:
            try:
                if os.path.exists(p):
                    return p
            except Exception:
                pass
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
        ox, oy = self.root.winfo_x(), self.root.winfo_y()
        for d in [10, -10, 8, -8, 5, -5, 2, -2, 0]:
            self.root.geometry(f"{self.W}x{self.H}+{ox+d}+{oy}")
            self.root.update()
            self.root.after(18)
