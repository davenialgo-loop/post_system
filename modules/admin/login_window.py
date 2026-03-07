# -*- coding: utf-8 -*-
"""login_window.py  —  Venialgo Sistemas POS"""

import tkinter as tk
import sqlite3, hashlib, os, sys

try:
    from utils.window_icon import set_icon as _set_icon
except Exception:
    def _set_icon(w): pass

# ── Paleta ──────────────────────────────────────────────────────
DARK1  = "#0A1628"
DARK2  = "#0F2347"
WHITE  = "#FFFFFF"
BLUE   = "#1A4FCC"
BLUE_H = "#1340A8"
BORDER = "#D0DCF0"
TXT_D  = "#0F1E3A"
TXT_S  = "#6B7FA8"
TXT_W  = "#FFFFFF"
GREEN  = "#059669"
GREEN_H= "#047857"
RED    = "#E11D48"
FONT   = "Segoe UI"

FOOTER_INFO = {
    "email":    "davenialgo@proton.me",
    "whatsapp": "+595 994-686 493",
    "web":      "www.venialgosistemas.com",
}

# ── DB helpers ───────────────────────────────────────────────────
def _get_db():
    base = os.environ.get("APPDATA", os.path.expanduser("~")) if sys.platform == "win32" \
           else os.path.expanduser("~")
    d = os.path.join(base, "VenialgoPOS")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "pos_database.db")

def _sha256(text):
    return hashlib.sha256(text.encode()).hexdigest()

def verify_login(usuario, password):
    try:
        from modules.admin.admin_ui import _ensure_tables
        _ensure_tables()
    except Exception:
        pass
    try:
        conn = sqlite3.connect(_get_db())
        row = conn.execute(
            "SELECT id,nombre,rol FROM usuarios WHERE usuario=? AND password=? AND activo=1",
            (usuario, _sha256(password))).fetchone()
        conn.close()
        return row
    except Exception:
        return None

def get_security_question(usuario):
    """Devuelve (id, pregunta) o None."""
    try:
        conn = sqlite3.connect(_get_db())
        row = conn.execute(
            "SELECT id, pregunta_seguridad FROM usuarios WHERE usuario=? AND activo=1",
            (usuario,)).fetchone()
        conn.close()
        return row
    except Exception:
        return None

def verify_security_answer(uid, respuesta):
    try:
        conn = sqlite3.connect(_get_db())
        row = conn.execute(
            "SELECT respuesta_seguridad FROM usuarios WHERE id=?", (uid,)).fetchone()
        conn.close()
        if row and row[0]:
            return row[0] == _sha256(respuesta.strip().lower())
    except Exception:
        pass
    return False

def reset_password(uid, new_password):
    try:
        conn = sqlite3.connect(_get_db())
        conn.execute("UPDATE usuarios SET password=? WHERE id=?",
                     (_sha256(new_password), uid))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

# ── Dialogo de mensaje ───────────────────────────────────────────
def _dialog(parent, title, msg, kind="error"):
    KINDS = {"error": ("#E11D48","!"), "warning": ("#D97706","!"), "info": ("#059669","OK")}
    accent, _ = KINDS.get(kind, KINDS["error"])
    dlg = tk.Toplevel(parent)
    _set_icon(dlg)
    dlg.title(title)
    dlg.resizable(False, False)
    dlg.configure(bg=WHITE)
    dlg.transient(parent)
    dlg.grab_set()
    dlg.update_idletasks()
    w, h = 380, 170
    px = parent.winfo_rootx() + (parent.winfo_width()  - w) // 2
    py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
    dlg.geometry(f"{w}x{h}+{px}+{py}")
    tk.Frame(dlg, bg=accent, height=5).pack(fill="x")
    body = tk.Frame(dlg, bg=WHITE, padx=24, pady=18)
    body.pack(fill="both", expand=True)
    tk.Label(body, text=msg, font=(FONT, 10), bg=WHITE, fg=TXT_D,
             wraplength=300, justify="left").pack(anchor="w", pady=(0, 14))
    btn = tk.Label(body, text="  Aceptar  ", font=(FONT, 10, "bold"),
                   bg=accent, fg=WHITE, cursor="hand2", padx=16, pady=8)
    btn.pack(anchor="e")
    def _close():
        dlg.grab_release()
        dlg.destroy()
    btn.bind("<ButtonRelease-1>", lambda e: _close())
    dlg.bind("<Return>",  lambda e: _close())
    dlg.bind("<Escape>",  lambda e: _close())
    parent.wait_window(dlg)

# ── Entry estilizado ─────────────────────────────────────────────
class StyledEntry(tk.Frame):
    def __init__(self, parent, show=None, **kw):
        super().__init__(parent, bg=WHITE, **kw)
        self._brd = tk.Frame(self, bg=BORDER)
        self._brd.pack(fill="x", ipady=1)
        inner = tk.Frame(self._brd, bg=WHITE)
        inner.pack(fill="x", padx=1, pady=1)
        self._var = tk.StringVar()
        self._ent = tk.Entry(inner, textvariable=self._var,
                             show=show or "", font=(FONT, 11),
                             bg=WHITE, fg=TXT_D, relief="flat", bd=0,
                             insertbackground=BLUE)
        self._ent.pack(fill="x", padx=12, ipady=10)
        self._ent.bind("<FocusIn>",  lambda e: self._brd.config(bg=BLUE))
        self._ent.bind("<FocusOut>", lambda e: self._brd.config(bg=BORDER))

    def get(self):      return self._var.get()
    def set(self, v):   self._var.set(v)
    def focus(self):    self._ent.focus_set()
    def bind_key(self, seq, fn): self._ent.bind(seq, fn)


# ══════════════════════════════════════════════════════════════════
#  DIALOGO: Recuperar contraseña (3 pasos)
# ══════════════════════════════════════════════════════════════════
class ForgotPasswordDialog:
    W, H = 480, 430

    def __init__(self, parent):
        self.parent    = parent
        self._uid      = None
        self._pregunta = ""

        self.win = tk.Toplevel(parent)
        _set_icon(self.win)
        self.win.title("Recuperar contraseña")
        self.win.resizable(False, False)
        self.win.configure(bg=WHITE)
        self.win.transient(parent)
        self.win.grab_set()
        self.win.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self.W) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.H) // 2
        self.win.geometry(f"{self.W}x{self.H}+{px}+{py}")
        self.win.protocol("WM_DELETE_WINDOW", self._cerrar)
        self._build_shell()
        self._show_step(1)
        self.win.bind("<Return>", lambda e: self._advance())

    # ── Cerrar / volver al login ──────────────────────────────────
    def _cerrar(self):
        self.win.grab_release()
        self.win.destroy()

    # ── Shell permanente ──────────────────────────────────────────
    def _build_shell(self):
        # Header
        hdr = tk.Frame(self.win, bg=DARK2, pady=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Recuperar contraseña",
                 font=(FONT, 13, "bold"), bg=DARK2, fg=WHITE).pack()

        # Barra de pasos
        steps_bar = tk.Frame(self.win, bg="#EBF2FF", pady=6)
        steps_bar.pack(fill="x")
        self._step_lbls = []
        for txt in ["1. Usuario", "2. Verificación", "3. Nueva clave"]:
            lbl = tk.Label(steps_bar, text=txt, font=(FONT, 8),
                           bg="#EBF2FF", fg=TXT_S, padx=10)
            lbl.pack(side="left", expand=True)
            self._step_lbls.append(lbl)

        # Zona de contenido dinamico
        self._body = tk.Frame(self.win, bg=WHITE, padx=32, pady=18)
        self._body.pack(fill="both", expand=True)

        # Barra de botones
        bf = tk.Frame(self.win, bg="#F9FAFB", pady=10, padx=20)
        bf.pack(fill="x")

        self._btn_cancel = tk.Label(bf, text="Volver al login",
                                    font=(FONT, 10, "bold"),
                                    bg="#E5E7EB", fg=TXT_D,
                                    cursor="hand2", padx=14, pady=8)
        self._btn_cancel.pack(side="left")
        self._btn_cancel.bind("<Enter>",
            lambda e: self._btn_cancel.config(bg="#D1D5DB"))
        self._btn_cancel.bind("<Leave>",
            lambda e: self._btn_cancel.config(bg="#E5E7EB"))
        # CORRECTO: bind separado, no encadenado
        self._btn_cancel.bind("<ButtonRelease-1>",
            lambda e: self._cerrar())

        self._btn_next = tk.Label(bf, text="Siguiente",
                                  font=(FONT, 10, "bold"),
                                  bg=BLUE, fg=WHITE,
                                  cursor="hand2", padx=14, pady=8)
        self._btn_next.pack(side="right")
        self._btn_next.bind("<Enter>",
            lambda e: self._btn_next.config(bg=self._next_hover))
        self._btn_next.bind("<Leave>",
            lambda e: self._btn_next.config(bg=self._next_bg))
        self._btn_next.bind("<ButtonRelease-1>",
            lambda e: self._advance())
        self._next_bg    = BLUE
        self._next_hover = BLUE_H

    def _set_next_btn(self, text, bg, hover):
        self._next_bg    = bg
        self._next_hover = hover
        self._btn_next.config(text=text, bg=bg)

    def _upd_steps(self, cur):
        for i, lbl in enumerate(self._step_lbls):
            if i + 1 < cur:
                lbl.config(fg="#059669", font=(FONT, 8, "bold"))
            elif i + 1 == cur:
                lbl.config(fg=BLUE, font=(FONT, 8, "bold"))
            else:
                lbl.config(fg=TXT_S, font=(FONT, 8))

    def _clear_body(self):
        for w in self._body.winfo_children():
            w.destroy()

    def _err_label(self):
        lbl = tk.Label(self._body, text="", font=(FONT, 9), bg=WHITE, fg=RED)
        lbl.pack(anchor="w", pady=(8, 0))
        return lbl

    # ── Paso 1: usuario ───────────────────────────────────────────
    def _show_step(self, n):
        self._step = n
        self._clear_body()
        self._upd_steps(n)
        if n == 1:
            self._build_s1()
        elif n == 2:
            self._build_s2()
        elif n == 3:
            self._build_s3()

    def _build_s1(self):
        tk.Label(self._body, text="Ingrese su nombre de usuario",
                 font=(FONT, 11, "bold"), bg=WHITE, fg=TXT_D).pack(anchor="w")
        tk.Label(self._body,
                 text="Le mostraremos su pregunta de seguridad configurada",
                 font=(FONT, 9), bg=WHITE, fg=TXT_S).pack(anchor="w", pady=(2, 14))
        tk.Label(self._body, text="Usuario:", font=(FONT, 9, "bold"),
                 bg=WHITE, fg=TXT_D).pack(anchor="w")
        self._e = StyledEntry(self._body)
        self._e.pack(fill="x", pady=(4, 0))
        self._e.focus()
        self._err = self._err_label()
        self._set_next_btn("Siguiente", BLUE, BLUE_H)

    def _build_s2(self):
        tk.Label(self._body, text="Responda la pregunta de seguridad",
                 font=(FONT, 11, "bold"), bg=WHITE, fg=TXT_D).pack(anchor="w")
        q_card = tk.Frame(self._body, bg="#FEF9C3",
                          highlightbackground="#FDE68A",
                          highlightthickness=1, padx=12, pady=10)
        q_card.pack(fill="x", pady=(10, 14))
        tk.Label(q_card, text=self._pregunta,
                 font=(FONT, 10), bg="#FEF9C3", fg="#92400E",
                 wraplength=380, justify="left").pack(anchor="w")
        tk.Label(self._body,
                 text="Respuesta (no distingue mayusculas):",
                 font=(FONT, 9, "bold"), bg=WHITE, fg=TXT_D).pack(anchor="w")
        self._e = StyledEntry(self._body)
        self._e.pack(fill="x", pady=(4, 0))
        self._e.focus()
        self._err = self._err_label()
        self._set_next_btn("Verificar", BLUE, BLUE_H)

    def _build_s3(self):
        ok = tk.Frame(self._body, bg="#ECFDF5",
                      highlightbackground="#A7F3D0",
                      highlightthickness=1, padx=12, pady=8)
        ok.pack(fill="x", pady=(0, 16))
        tk.Label(ok, text="Identidad verificada correctamente",
                 font=(FONT, 9, "bold"), bg="#ECFDF5", fg="#065F46").pack(anchor="w")
        tk.Label(self._body, text="Nueva contraseña (min. 6 caracteres):",
                 font=(FONT, 9, "bold"), bg=WHITE, fg=TXT_D).pack(anchor="w")
        self._e_nueva = StyledEntry(self._body, show="*")
        self._e_nueva.pack(fill="x", pady=(4, 10))
        tk.Label(self._body, text="Confirmar contraseña:",
                 font=(FONT, 9, "bold"), bg=WHITE, fg=TXT_D).pack(anchor="w")
        self._e_conf = StyledEntry(self._body, show="*")
        self._e_conf.pack(fill="x", pady=(4, 0))
        self._e_nueva.focus()
        self._err = self._err_label()
        self._set_next_btn("Guardar contraseña", GREEN, GREEN_H)

    # ── Logica de avance ──────────────────────────────────────────
    def _advance(self):
        if self._step == 1:
            usr = self._e.get().strip()
            if not usr:
                self._err.config(text="Ingrese su nombre de usuario")
                return
            result = get_security_question(usr)
            if not result:
                self._err.config(text="Usuario no encontrado")
                return
            uid, pregunta = result
            if not pregunta:
                _dialog(self.win, "Sin pregunta de seguridad",
                        "Este usuario no tiene pregunta de seguridad configurada.\n"
                        "Contacte al administrador del sistema.", "warning")
                return
            self._uid      = uid
            self._pregunta = pregunta
            self._show_step(2)

        elif self._step == 2:
            resp = self._e.get().strip()
            if not resp:
                self._err.config(text="Ingrese la respuesta")
                return
            if not verify_security_answer(self._uid, resp):
                self._err.config(text="Respuesta incorrecta. Intente nuevamente.")
                return
            self._show_step(3)

        elif self._step == 3:
            nueva = self._e_nueva.get()
            conf  = self._e_conf.get()
            if len(nueva) < 6:
                self._err.config(text="Minimo 6 caracteres")
                return
            if nueva != conf:
                self._err.config(text="Las contraseñas no coinciden")
                return
            if reset_password(self._uid, nueva):
                self._cerrar()
                _dialog(self.parent, "Contraseña actualizada",
                        "Su contraseña fue actualizada.\n"
                        "Inicie sesion con la nueva contraseña.", "info")
            else:
                self._err.config(text="Error al guardar. Intente nuevamente.")


# ══════════════════════════════════════════════════════════════════
#  VENTANA LOGIN
# ══════════════════════════════════════════════════════════════════
class LoginWindow:
    W, H = 440, 600

    def __init__(self, root, on_success):
        self.root       = root
        self.on_success = on_success
        self.root.title("Venialgo Sistemas POS — Iniciar Sesion")
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
        self._build_footer()
        self._build_header()
        self._build_card()
        self.root.bind("<Return>", lambda e: self._login())

    def _build_footer(self):
        bar = tk.Frame(self.root, bg="#0A1628", height=36)
        bar.pack(side="bottom", fill="x")
        bar.pack_propagate(False)
        inner = tk.Frame(bar, bg="#0A1628")
        inner.place(relx=0.5, rely=0.5, anchor="center")
        items = [
            (f"  {FOOTER_INFO['email']}",    "#7EB8F7"),
            ("  |  ",                           "#2A4A6A"),
            (f"  {FOOTER_INFO['whatsapp']}",  "#7EB8F7"),
            ("  |  ",                           "#2A4A6A"),
            (f"  {FOOTER_INFO['web']}",       "#7EB8F7"),
        ]
        for txt, fg in items:
            tk.Label(inner, text=txt, bg="#0A1628", fg=fg,
                     font=(FONT, 7)).pack(side="left")

    def _build_header(self):
        HDR_H = 210
        canvas = tk.Canvas(self.root, width=self.W, height=HDR_H,
                           highlightthickness=0, bd=0)
        canvas.pack(fill="x")
        r1, g1, b1 = 0x0A, 0x16, 0x28
        r2, g2, b2 = 0x1A, 0x3A, 0x7A
        for i in range(HDR_H):
            t = i / HDR_H
            r = int(r1 + (r2-r1)*t)
            g = int(g1 + (g2-g1)*t)
            b = int(b1 + (b2-b1)*t)
            canvas.create_line(0, i, self.W, i, fill=f"#{r:02x}{g:02x}{b:02x}")
        canvas.create_oval(300, -30, 500, 170, fill="", outline="#1E3A6E", width=1)
        logo_path = self._find_logo()
        self._logo_img = None
        logo_y = 50
        if logo_path:
            try:
                from PIL import Image, ImageTk
                img = Image.open(logo_path).convert("RGBA")
                img.thumbnail((90, 90), Image.LANCZOS)
                bg_img = Image.new("RGBA", img.size, (0, 0, 0, 0))
                bg_img.paste(img, mask=img.split()[3])
                self._logo_img = ImageTk.PhotoImage(bg_img)
                canvas.create_image(self.W // 2, logo_y + 45, image=self._logo_img)
                logo_y += 100
            except Exception:
                canvas.create_text(self.W // 2, logo_y + 30,
                    text="", font=(FONT, 42), fill=TXT_W)
                logo_y += 72
        else:
            canvas.create_text(self.W // 2, logo_y + 30,
                text="", font=(FONT, 42), fill=TXT_W)
            logo_y += 72
        canvas.create_text(self.W // 2, logo_y + 8,
            text="Venialgo Sistemas POS",
            font=(FONT, 15, "bold"), fill=TXT_W)
        canvas.create_text(self.W // 2, logo_y + 30,
            text="Inicie sesion para continuar",
            font=(FONT, 9), fill="#8AABD4")

    def _build_card(self):
        card = tk.Frame(self.root, bg=WHITE)
        card.pack(fill="both", expand=True)
        tk.Frame(card, bg="#C8D8F0", height=2).pack(fill="x")
        inner = tk.Frame(card, bg=WHITE, padx=40, pady=22)
        inner.pack(fill="both", expand=True)

        # Campo usuario
        tk.Label(inner, text="Usuario", font=(FONT, 10, "bold"),
                 bg=WHITE, fg=TXT_D).pack(anchor="w")
        self._entry_usr = StyledEntry(inner)
        self._entry_usr.pack(fill="x", pady=(4, 14))

        # Campo contraseña
        tk.Label(inner, text="Contraseña", font=(FONT, 10, "bold"),
                 bg=WHITE, fg=TXT_D).pack(anchor="w")
        self._entry_pwd = StyledEntry(inner, show="*")
        self._entry_pwd.pack(fill="x", pady=(4, 6))

        # Olvide mi contraseña
        forgot = tk.Label(inner, text="Olvide mi contraseña",
                          font=(FONT, 9), bg=WHITE, fg=BLUE, cursor="hand2")
        forgot.pack(anchor="e", pady=(0, 22))
        forgot.bind("<Enter>",
            lambda e: forgot.config(fg=BLUE_H, font=(FONT, 9, "underline")))
        forgot.bind("<Leave>",
            lambda e: forgot.config(fg=BLUE, font=(FONT, 9)))
        # CORRECTO: bind separado en su propia linea
        forgot.bind("<ButtonRelease-1>",
            lambda e: ForgotPasswordDialog(self.root))

        # Boton INGRESAR
        self._btn = tk.Label(inner, text="  INGRESAR  ",
                             font=(FONT, 12, "bold"), bg=BLUE, fg=TXT_W,
                             cursor="hand2", pady=13, anchor="center")
        self._btn.pack(fill="x")
        self._btn.bind("<Enter>",
            lambda e: self._btn.config(bg=BLUE_H))
        self._btn.bind("<Leave>",
            lambda e: self._btn.config(bg=BLUE))
        self._btn.bind("<Button-1>",
            lambda e: self._btn.config(bg="#0F3288"))
        self._btn.bind("<ButtonRelease-1>",
            lambda e: (self._btn.config(bg=BLUE_H), self._login()))

        # Version badge
        tk.Label(inner, text=" v1.1 ", font=(FONT, 7, "bold"),
                 bg="#EBF2FF", fg=BLUE, padx=6, pady=2).pack(pady=(16, 0))

        self._entry_usr.focus()

    def _find_logo(self):
        paths = [
            os.path.join(os.path.dirname(sys.executable), "assets", "VenialgoSistemasLogo.png"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "..", "assets", "VenialgoSistemasLogo.png"),
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
        pwd = self._entry_pwd.get()
        if not usr or not pwd:
            self._shake()
            _dialog(self.root, "Atencion",
                    "Complete el usuario y la contraseña.", "warning")
            return
        result = verify_login(usr, pwd)
        if result:
            uid, nombre, rol = result
            self.root.destroy()
            self.on_success(uid, nombre, rol)
        else:
            self._shake()
            _dialog(self.root, "Acceso denegado",
                    "Usuario o contraseña incorrectos, o usuario inactivo.",
                    "error")

    def _shake(self):
        ox, oy = self.root.winfo_x(), self.root.winfo_y()
        for d in [8, -8, 6, -6, 4, -4, 2, -2, 0]:
            self.root.geometry(f"{self.W}x{self.H}+{ox+d}+{oy}")
            self.root.update()
            self.root.after(18)


# Alias para compatibilidad con versiones anteriores
ForgotPasswordWindow = ForgotPasswordDialog
