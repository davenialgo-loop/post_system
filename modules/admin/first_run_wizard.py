"""
first_run_wizard.py
Asistente de configuración inicial — Primera vez que se inicia el sistema.
Incluye creación de cuenta Administrador y pregunta de seguridad.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import sqlite3, shutil, os, sys, hashlib
from pathlib import Path

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ── Paleta consistente con el sistema ─────────────────────────
THEME = {
    "sb_bg":        "#0D1B4B",
    "sb_mid":       "#1A3A8F",
    "card_bg":      "#FFFFFF",
    "ct_bg":        "#F9FAFB",
    "acc_blue":     "#2563EB",
    "acc_blue_dk":  "#1D4ED8",
    "acc_green":    "#059669",
    "acc_green_dk": "#047857",
    "acc_rose":     "#E11D48",
    "acc_amber":    "#D97706",
    "txt_primary":  "#111827",
    "txt_secondary":"#6B7280",
    "txt_white":    "#FFFFFF",
    "border":       "#E5E7EB",
    "input_brd":    "#D1D5DB",
    "step_done":    "#ECFDF5",
    "step_done_fg": "#065F46",
    "step_bar":     "#E5E7EB",
    "footer_bg":    "#0F172A",
    "footer_fg":    "#64748B",
}
FONT = "Segoe UI"

FOOTER_INFO = {
    "empresa":  "Venialgo Sistemas",
    "email":    "davenialgo@proton.me",
    "whatsapp": "+595 994-686 493",
    "web":      "www.venialgosistemas.com",
}

SECURITY_QUESTIONS = [
    "¿Cuál es el nombre de tu primera mascota?",
    "¿En qué ciudad naciste?",
    "¿Cuál es el nombre de tu madre?",
    "¿Cuál fue el nombre de tu primera escuela?",
    "¿Cuál es tu película favorita?",
    "¿Cuál es el apodo de tu mejor amigo/a de infancia?",
]

# ── Rutas ──────────────────────────────────────────────────────
def _appdata_dir():
    base = os.environ.get("APPDATA", os.path.expanduser("~")) if sys.platform=="win32" \
           else os.path.expanduser("~")
    d = os.path.join(base, "VenialgoPOS")
    os.makedirs(d, exist_ok=True)
    return d

DB_FILE        = os.path.join(_appdata_dir(), "pos_database.db")
LOGO_DIR       = Path(_appdata_dir()) / "logos"
FIRST_RUN_FLAG = os.path.join(_appdata_dir(), ".first_run_done")


# ── Helpers ────────────────────────────────────────────────────

def _apply_icon(window):
    if getattr(sys, "frozen", False):
        start = os.path.dirname(sys.executable)
    else:
        start = os.path.dirname(os.path.abspath(__file__))
    cur = start
    for _ in range(4):
        for name in ["venialgosist.ico", "venialgo.ico", "app_icon.ico"]:
            p = os.path.join(cur, "assets", name)
            if os.path.isfile(p):
                try: window.iconbitmap(p); return
                except: pass
        cur = os.path.dirname(cur)


def _gradient_canvas(parent, w, h):
    canvas = tk.Canvas(parent, width=w, height=h, highlightthickness=0, bd=0)
    canvas.pack(fill="x")
    r1,g1,b1 = 0x0D,0x1B,0x4B
    r2,g2,b2 = 0x1A,0x3A,0x8F
    for i in range(h):
        t = i/h
        r=int(r1+(r2-r1)*t); g=int(g1+(g2-g1)*t); b=int(b1+(b2-b1)*t)
        canvas.create_line(0,i,w,i, fill=f"#{r:02x}{g:02x}{b:02x}")
    return canvas


def _styled_entry(parent, var, show=""):
    frm = tk.Frame(parent, bg=THEME["input_brd"], padx=1, pady=1)
    ent = tk.Entry(frm, textvariable=var, show=show,
                   font=(FONT, 11), relief="flat",
                   bg=THEME["card_bg"], fg=THEME["txt_primary"],
                   insertbackground=THEME["acc_blue"])
    ent.pack(fill="x", ipady=6, padx=1)
    ent.bind("<FocusIn>",  lambda e: frm.config(bg=THEME["acc_blue"]))
    ent.bind("<FocusOut>", lambda e: frm.config(bg=THEME["input_brd"]))
    return frm, ent


def _label_btn(parent, text, cmd, bg, hover=None, width=None):
    hover = hover or bg
    kw = {"padx": 18, "pady": 10}
    if width: kw["width"] = width
    lbl = tk.Label(parent, text=text, font=(FONT, 10, "bold"),
                   bg=bg, fg=THEME["txt_white"], cursor="hand2", **kw)
    lbl.bind("<Enter>",           lambda e: lbl.config(bg=hover))
    lbl.bind("<Leave>",           lambda e: lbl.config(bg=bg))
    lbl.bind("<ButtonRelease-1>", lambda e: cmd())
    return lbl


# ── BD helpers ────────────────────────────────────────────────

def is_first_run() -> bool:
    """True si no hay empresa configurada O no hay ningún usuario administrador."""
    if os.path.exists(FIRST_RUN_FLAG):
        # Verificar también que exista al menos un admin en la BD
        try:
            conn = sqlite3.connect(DB_FILE)
            row = conn.execute(
                "SELECT COUNT(*) FROM usuarios WHERE rol='Administrador' AND activo=1"
            ).fetchone()
            conn.close()
            if row and row[0] > 0:
                return False
        except Exception:
            pass
        return True
    try:
        conn = sqlite3.connect(DB_FILE)
        empresa = conn.execute(
            "SELECT razon_social FROM empresa WHERE id=1").fetchone()
        admin = conn.execute(
            "SELECT COUNT(*) FROM usuarios WHERE rol='Administrador' AND activo=1"
        ).fetchone()
        conn.close()
        if empresa and empresa[0] and admin and admin[0] > 0:
            return False
    except Exception:
        pass
    return True


def _mark_done():
    try:
        with open(FIRST_RUN_FLAG, "w") as f:
            f.write("done")
    except Exception:
        pass


def save_company_data(data: dict) -> bool:
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS empresa (
            id INTEGER PRIMARY KEY, razon_social TEXT DEFAULT '',
            ruc TEXT DEFAULT '', telefono TEXT DEFAULT '',
            direccion TEXT DEFAULT '', correo TEXT DEFAULT '',
            logo_path TEXT DEFAULT '')""")
        for col in ["logo_path", "ciudad", "web", "email"]:
            try: c.execute(f"ALTER TABLE empresa ADD COLUMN {col} TEXT DEFAULT ''")
            except: pass
        c.execute("SELECT COUNT(*) FROM empresa WHERE id=1")
        if c.fetchone()[0]:
            c.execute("""UPDATE empresa SET razon_social=?,ruc=?,telefono=?,
                direccion=?,correo=?,logo_path=? WHERE id=1""",
                (data.get("razon_social",""), data.get("ruc",""),
                 data.get("telefono",""), data.get("direccion",""),
                 data.get("correo",""), data.get("logo_path","")))
        else:
            c.execute("""INSERT INTO empresa
                (id,razon_social,ruc,telefono,direccion,correo,logo_path)
                VALUES (1,?,?,?,?,?,?)""",
                (data.get("razon_social",""), data.get("ruc",""),
                 data.get("telefono",""), data.get("direccion",""),
                 data.get("correo",""), data.get("logo_path","")))
        conn.commit(); conn.close()
        return True
    except Exception as e:
        print(f"[save_company_data] {e}")
        return False


def create_admin_user(nombre, usuario, password,
                      pregunta, respuesta) -> bool:
    """Crea el usuario administrador inicial con pregunta de seguridad."""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        # Ensure usuarios table exists with security columns
        c.execute("""CREATE TABLE IF NOT EXISTS usuarios (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT NOT NULL,
            usuario   TEXT UNIQUE NOT NULL,
            password  TEXT NOT NULL,
            rol       TEXT DEFAULT 'Cajero',
            activo    INTEGER DEFAULT 1,
            creado_en TEXT
        )""")
        for col_def in [
            "pregunta_seguridad TEXT DEFAULT ''",
            "respuesta_seguridad   TEXT DEFAULT ''",
        ]:
            try: c.execute(f"ALTER TABLE usuarios ADD COLUMN {col_def}")
            except: pass

        from datetime import datetime
        hpwd  = hashlib.sha256(password.encode()).hexdigest()
        hresp = hashlib.sha256(respuesta.strip().lower().encode()).hexdigest()
        c.execute(
            """INSERT INTO usuarios
               (nombre, usuario, password, rol, activo, creado_en,
                pregunta_seguridad, respuesta_seguridad)
               VALUES (?,?,?,?,1,?,?,?)""",
            (nombre, usuario, hpwd, "Administrador",
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             pregunta, hresp)
        )
        conn.commit(); conn.close()
        return True
    except Exception as e:
        print(f"[create_admin_user] {e}")
        return False


def get_company_data() -> dict:
    try:
        conn = sqlite3.connect(DB_FILE)
        row = conn.execute(
            "SELECT razon_social,ruc,telefono,direccion,correo,logo_path FROM empresa WHERE id=1"
        ).fetchone()
        conn.close()
        if row:
            return {"razon_social": row[0] or "", "ruc": row[1] or "",
                    "telefono": row[2] or "", "direccion": row[3] or "",
                    "correo": row[4] or "", "logo_path": row[5] or ""}
    except Exception:
        pass
    return {}


def copy_logo(src_path: str) -> str:
    if not src_path or not os.path.exists(src_path):
        return ""
    try:
        LOGO_DIR.mkdir(parents=True, exist_ok=True)
        dest = LOGO_DIR / "company_logo.png"
        if PIL_AVAILABLE:
            img = Image.open(src_path).convert("RGBA")
            img.thumbnail((400, 200), Image.LANCZOS)
            img.save(str(dest), "PNG")
            return str(dest)
        else:
            shutil.copy2(src_path, str(dest))
            return str(dest)
    except Exception:
        return src_path


# ════════════════════════════════════════════════════════════
#  WIZARD
# ════════════════════════════════════════════════════════════

class FirstRunWizard:
    PASOS = [
        ("🏠", "Bienvenida"),
        ("🏢", "Empresa"),
        ("👤", "Cuenta Admin"),
        ("🖼",  "Logo"),
        ("✅", "Confirmación"),
    ]

    def __init__(self, root, on_complete):
        self.root        = root
        self.on_complete = on_complete
        self._paso_actual = 0
        self._logo_src    = ""

        self.win = root
        self.win.title("Configuración Inicial — Venialgo Sistemas POS")
        self.win.configure(bg=THEME["ct_bg"])
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self._on_close_attempt)
        _apply_icon(self.win)
        self._init_vars()
        self._build_shell()
        self._show_paso(0)
        self._center()

    def _center(self):
        self.win.update_idletasks()
        w = self.win.winfo_reqwidth()
        h = self.win.winfo_reqheight()
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        self.win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _on_close_attempt(self):
        messagebox.showwarning("Configuración requerida",
            "Debe completar la configuración inicial para usar el sistema.\n"
            "Puede omitir los campos opcionales, pero los marcados con * son obligatorios.",
            parent=self.win)

    def _init_vars(self):
        # Empresa
        self.vars = {k: tk.StringVar() for k in
                     ["razon_social","ruc","telefono","correo","direccion"]}
        # Admin account
        self.admin_vars = {k: tk.StringVar() for k in
                           ["nombre","usuario","password","password2"]}
        self.admin_vars["pregunta"] = tk.StringVar(value=SECURITY_QUESTIONS[0])
        self.admin_vars["respuesta"] = tk.StringVar()

    # ── Shell ──────────────────────────────────────────────────
    def _build_shell(self):
        W = 740

        hdr_canvas = _gradient_canvas(self.win, W, 80)
        hdr_canvas.create_text(W//2, 32, text="⚙️  Configuración Inicial del Sistema",
                                font=(FONT, 14, "bold"), fill=THEME["txt_white"], anchor="center")
        hdr_canvas.create_text(W//2, 56, text="Complete los datos antes de comenzar",
                                font=(FONT, 9), fill="#9DB4E0", anchor="center")

        steps_row = tk.Frame(self.win, bg=THEME["step_bar"], height=48)
        steps_row.pack(fill="x")
        steps_row.pack_propagate(False)
        self._step_frames = []
        self._step_labels = []
        for i, (icon, nombre) in enumerate(self.PASOS):
            cell = tk.Frame(steps_row, bg=THEME["step_bar"])
            cell.pack(side="left", expand=True, fill="both")
            lbl = tk.Label(cell, text=f"{icon}  {nombre}",
                           font=(FONT, 9), bg=THEME["step_bar"],
                           fg=THEME["txt_secondary"], pady=13)
            lbl.pack(expand=True)
            self._step_frames.append(cell)
            self._step_labels.append(lbl)

        self.frm_content = tk.Frame(self.win, bg=THEME["card_bg"], width=W)
        self.frm_content.pack(fill="both", expand=True)

        nav_sep = tk.Frame(self.win, bg=THEME["border"], height=1)
        nav_sep.pack(fill="x")

        nav = tk.Frame(self.win, bg=THEME["ct_bg"], pady=12)
        nav.pack(fill="x")

        self._btn_back = _label_btn(nav, "← Anterior", self._prev,
                                    "#E5E7EB", "#D1D5DB", width=14)
        self._btn_back.pack(side="left", padx=20)

        self._btn_next = _label_btn(nav, "Siguiente →", self._next,
                                    THEME["acc_blue"], THEME["acc_blue_dk"], width=18)
        self._btn_next.pack(side="right", padx=20)

        tk.Label(nav,
                 text=f"{FOOTER_INFO['empresa']}  |  {FOOTER_INFO['email']}  |  {FOOTER_INFO['whatsapp']}",
                 font=(FONT, 7), bg=THEME["ct_bg"],
                 fg=THEME["txt_secondary"]).pack()

    # ── Pasos ──────────────────────────────────────────────────
    def _update_steps(self, paso):
        for i, (cell, lbl) in enumerate(zip(self._step_frames, self._step_labels)):
            icon, nombre = self.PASOS[i]
            if i < paso:
                cell.config(bg=THEME["step_done"])
                lbl.config(text=f"✓  {nombre}", bg=THEME["step_done"],
                           fg=THEME["step_done_fg"], font=(FONT, 9, "bold"))
            elif i == paso:
                cell.config(bg=THEME["acc_blue"])
                lbl.config(text=f"{icon}  {nombre}", bg=THEME["acc_blue"],
                           fg=THEME["txt_white"], font=(FONT, 9, "bold"))
            else:
                cell.config(bg=THEME["step_bar"])
                lbl.config(text=f"{icon}  {nombre}", bg=THEME["step_bar"],
                           fg=THEME["txt_secondary"], font=(FONT, 9))

    def _show_paso(self, n):
        self._paso_actual = n
        for w in self.frm_content.winfo_children():
            w.destroy()
        self._update_steps(n)

        state = "normal" if n > 0 else "disabled"
        self._btn_back.config(state=state,
                              bg="#E5E7EB" if n > 0 else "#F3F4F6",
                              fg=THEME["txt_primary"] if n > 0 else THEME["txt_secondary"],
                              cursor="hand2" if n > 0 else "arrow")

        if n == len(self.PASOS) - 1:
            self._btn_next.config(text="💾  Guardar y Comenzar",
                                  bg=THEME["acc_green"])
            self._btn_next.bind("<Enter>", lambda e: self._btn_next.config(bg=THEME["acc_green_dk"]))
            self._btn_next.bind("<Leave>", lambda e: self._btn_next.config(bg=THEME["acc_green"]))
        else:
            self._btn_next.config(text="Siguiente →", bg=THEME["acc_blue"])
            self._btn_next.bind("<Enter>", lambda e: self._btn_next.config(bg=THEME["acc_blue_dk"]))
            self._btn_next.bind("<Leave>", lambda e: self._btn_next.config(bg=THEME["acc_blue"]))

        [self._paso_bienvenida, self._paso_datos,
         self._paso_admin, self._paso_logo,
         self._paso_confirmacion][n]()

    def _next(self):
        if self._paso_actual == 1 and not self._validar_datos():
            return
        if self._paso_actual == 2 and not self._validar_admin():
            return
        if self._paso_actual == len(self.PASOS) - 1:
            self._guardar()
        else:
            self._show_paso(self._paso_actual + 1)

    def _prev(self):
        if self._paso_actual > 0:
            self._show_paso(self._paso_actual - 1)

    # ── PASO 0: Bienvenida ─────────────────────────────────────
    def _paso_bienvenida(self):
        pad = tk.Frame(self.frm_content, bg=THEME["card_bg"], padx=56, pady=28)
        pad.pack(fill="both", expand=True)

        _logo_shown = False
        try:
            cur = os.path.dirname(os.path.abspath(__file__))
            for _ in range(4):
                p = os.path.join(cur, "assets", "VenialgoSistemasLogo.png")
                if os.path.isfile(p):
                    img = Image.open(p).convert("RGBA")
                    pixels = img.load()
                    for y in range(img.height):
                        for x in range(img.width):
                            r,g,b,a = pixels[x,y]
                            if r<30 and g<30 and b<30: pixels[x,y]=(r,g,b,0)
                    img = img.crop(img.getbbox())
                    img.thumbnail((80,80), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    lbl = tk.Label(pad, image=photo, bg=THEME["card_bg"])
                    lbl.image = photo
                    lbl.pack(pady=(0,8))
                    _logo_shown = True
                    break
                cur = os.path.dirname(cur)
        except Exception:
            pass
        if not _logo_shown:
            tk.Label(pad, text="🏪", font=(FONT, 52),
                     bg=THEME["card_bg"]).pack(pady=(0,8))

        tk.Label(pad, text="¡Bienvenido al Sistema POS!",
                 font=(FONT, 17, "bold"),
                 bg=THEME["card_bg"], fg=THEME["acc_blue"]).pack()
        tk.Label(pad, text="Este asistente lo guiará en la configuración inicial.",
                 font=(FONT, 10), bg=THEME["card_bg"],
                 fg=THEME["txt_secondary"]).pack(pady=(4, 20))

        for icon, titulo, desc in [
            ("🏢", "Datos de la empresa",   "Razón social, RUC, teléfono y dirección"),
            ("👤", "Cuenta Administrador",  "Usuario y contraseña para ingresar al sistema"),
            ("🖼",  "Logo de la empresa",   "Se mostrará en el sidebar y en los tickets"),
            ("✅", "Confirmación",           "Revisión final antes de comenzar"),
        ]:
            row = tk.Frame(pad, bg="#EFF6FF",
                           highlightbackground="#BFDBFE",
                           highlightthickness=1, padx=14, pady=10)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=icon, font=(FONT, 18),
                     bg="#EFF6FF").pack(side="left", padx=(0,12))
            col = tk.Frame(row, bg="#EFF6FF")
            col.pack(side="left")
            tk.Label(col, text=titulo, font=(FONT, 10, "bold"),
                     bg="#EFF6FF", fg=THEME["txt_primary"],
                     anchor="w").pack(anchor="w")
            tk.Label(col, text=desc, font=(FONT, 8),
                     bg="#EFF6FF", fg=THEME["txt_secondary"],
                     anchor="w").pack(anchor="w")

    # ── PASO 1: Datos empresa ──────────────────────────────────
    def _paso_datos(self):
        pad = tk.Frame(self.frm_content, bg=THEME["card_bg"], padx=56, pady=24)
        pad.pack(fill="both", expand=True)

        tk.Label(pad, text="🏢  Datos de la Empresa",
                 font=(FONT, 14, "bold"),
                 bg=THEME["card_bg"], fg=THEME["txt_primary"]).pack(anchor="w")
        tk.Label(pad, text="Los campos marcados con * son obligatorios",
                 font=(FONT, 8), bg=THEME["card_bg"],
                 fg=THEME["txt_secondary"]).pack(anchor="w", pady=(2, 16))
        tk.Frame(pad, bg=THEME["border"], height=1).pack(fill="x", pady=(0,16))

        campos = [
            ("Razón Social / Nombre *", "razon_social"),
            ("RUC / NIT *",             "ruc"),
            ("Teléfono",                "telefono"),
            ("Correo electrónico",      "correo"),
            ("Dirección",               "direccion"),
        ]

        grid = tk.Frame(pad, bg=THEME["card_bg"])
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        for i, (label, key) in enumerate(campos):
            row, col = divmod(i, 2)
            cell = tk.Frame(grid, bg=THEME["card_bg"], padx=6, pady=4)
            cell.grid(row=row, column=col, sticky="ew")
            tk.Label(cell, text=label, font=(FONT, 9, "bold"),
                     bg=THEME["card_bg"], fg=THEME["txt_primary"]).pack(anchor="w", pady=(0,3))
            frm, _ = _styled_entry(cell, self.vars[key])
            frm.pack(fill="x")

    def _validar_datos(self) -> bool:
        if not self.vars["razon_social"].get().strip():
            messagebox.showwarning("Campo requerido",
                "La Razón Social es obligatoria.", parent=self.win)
            return False
        if not self.vars["ruc"].get().strip():
            messagebox.showwarning("Campo requerido",
                "El RUC es obligatorio.", parent=self.win)
            return False
        return True

    # ── PASO 2: Cuenta Administrador ──────────────────────────
    def _paso_admin(self):
        pad = tk.Frame(self.frm_content, bg=THEME["card_bg"], padx=56, pady=20)
        pad.pack(fill="both", expand=True)

        tk.Label(pad, text="👤  Cuenta Administrador",
                 font=(FONT, 14, "bold"),
                 bg=THEME["card_bg"], fg=THEME["txt_primary"]).pack(anchor="w")
        tk.Label(pad,
                 text="Cree el usuario principal para ingresar al sistema. Todos los campos son obligatorios.",
                 font=(FONT, 8), bg=THEME["card_bg"],
                 fg=THEME["txt_secondary"]).pack(anchor="w", pady=(2, 12))
        tk.Frame(pad, bg=THEME["border"], height=1).pack(fill="x", pady=(0,14))

        grid = tk.Frame(pad, bg=THEME["card_bg"])
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        # Nombre completo y usuario en primera fila
        for col_i, (label, key, show) in enumerate([
            ("Nombre completo *",  "nombre",   ""),
            ("Usuario (login) *",  "usuario",  ""),
        ]):
            cell = tk.Frame(grid, bg=THEME["card_bg"], padx=6, pady=4)
            cell.grid(row=0, column=col_i, sticky="ew")
            tk.Label(cell, text=label, font=(FONT, 9, "bold"),
                     bg=THEME["card_bg"], fg=THEME["txt_primary"]).pack(anchor="w", pady=(0,3))
            frm, _ = _styled_entry(cell, self.admin_vars[key], show=show)
            frm.pack(fill="x")

        # Contraseña y confirmar
        for col_i, (label, key) in enumerate([
            ("Contraseña *",         "password"),
            ("Confirmar contraseña *","password2"),
        ]):
            cell = tk.Frame(grid, bg=THEME["card_bg"], padx=6, pady=4)
            cell.grid(row=1, column=col_i, sticky="ew")
            tk.Label(cell, text=label, font=(FONT, 9, "bold"),
                     bg=THEME["card_bg"], fg=THEME["txt_primary"]).pack(anchor="w", pady=(0,3))
            frm, _ = _styled_entry(cell, self.admin_vars[key], show="●")
            frm.pack(fill="x")

        # Sección pregunta de seguridad
        sec_card = tk.Frame(pad, bg="#FFFBEB",
                            highlightbackground="#FDE68A",
                            highlightthickness=1, padx=16, pady=12)
        sec_card.pack(fill="x", pady=(12,0))

        hdr_row = tk.Frame(sec_card, bg="#FFFBEB")
        hdr_row.pack(fill="x", pady=(0,8))
        tk.Label(hdr_row, text="🔐", font=(FONT, 16), bg="#FFFBEB").pack(side="left", padx=(0,8))
        col2 = tk.Frame(hdr_row, bg="#FFFBEB")
        col2.pack(side="left")
        tk.Label(col2, text="Pregunta de seguridad",
                 font=(FONT, 10, "bold"), bg="#FFFBEB",
                 fg=THEME["txt_primary"]).pack(anchor="w")
        tk.Label(col2, text="Se usará para recuperar su contraseña si la olvida",
                 font=(FONT, 8), bg="#FFFBEB",
                 fg="#92400E").pack(anchor="w")

        tk.Frame(sec_card, bg="#FDE68A", height=1).pack(fill="x", pady=(0,10))

        # Dropdown pregunta
        tk.Label(sec_card, text="Pregunta *", font=(FONT, 9, "bold"),
                 bg="#FFFBEB", fg=THEME["txt_primary"]).pack(anchor="w", pady=(0,3))
        opt = tk.OptionMenu(sec_card, self.admin_vars["pregunta"], *SECURITY_QUESTIONS)
        opt.config(font=(FONT, 9), bg=THEME["card_bg"], fg=THEME["txt_primary"],
                   relief="flat", bd=1, highlightbackground=THEME["input_brd"],
                   activebackground="#EFF6FF", cursor="hand2")
        opt["menu"].config(font=(FONT, 9))
        opt.pack(fill="x", pady=(0,8))

        # Respuesta
        tk.Label(sec_card, text="Respuesta *", font=(FONT, 9, "bold"),
                 bg="#FFFBEB", fg=THEME["txt_primary"]).pack(anchor="w", pady=(0,3))
        frm_r, _ = _styled_entry(sec_card, self.admin_vars["respuesta"])
        frm_r.pack(fill="x")
        tk.Label(sec_card,
                 text="⚠  Guarde esta respuesta, la necesitará para recuperar acceso",
                 font=(FONT, 8), bg="#FFFBEB", fg="#B45309").pack(anchor="w", pady=(6,0))

    def _validar_admin(self) -> bool:
        v = self.admin_vars
        nombre   = v["nombre"].get().strip()
        usuario  = v["usuario"].get().strip()
        password = v["password"].get()
        password2= v["password2"].get()
        respuesta= v["respuesta"].get().strip()

        if not nombre:
            messagebox.showwarning("Campo requerido", "El nombre completo es obligatorio.", parent=self.win)
            return False
        if not usuario:
            messagebox.showwarning("Campo requerido", "El nombre de usuario es obligatorio.", parent=self.win)
            return False
        if len(usuario) < 3:
            messagebox.showwarning("Usuario inválido", "El usuario debe tener al menos 3 caracteres.", parent=self.win)
            return False
        if not password:
            messagebox.showwarning("Campo requerido", "La contraseña es obligatoria.", parent=self.win)
            return False
        if len(password) < 6:
            messagebox.showwarning("Contraseña débil", "La contraseña debe tener al menos 6 caracteres.", parent=self.win)
            return False
        if password != password2:
            messagebox.showwarning("Error", "Las contraseñas no coinciden.", parent=self.win)
            return False
        if not respuesta:
            messagebox.showwarning("Campo requerido", "La respuesta de seguridad es obligatoria.", parent=self.win)
            return False
        return True

    # ── PASO 3: Logo ───────────────────────────────────────────
    def _paso_logo(self):
        pad = tk.Frame(self.frm_content, bg=THEME["card_bg"], padx=56, pady=24)
        pad.pack(fill="both", expand=True)

        tk.Label(pad, text="🖼  Logo de la Empresa",
                 font=(FONT, 14, "bold"),
                 bg=THEME["card_bg"], fg=THEME["txt_primary"]).pack(anchor="w")
        tk.Label(pad, text="Se mostrará en el sidebar y en los tickets. Formatos: PNG, JPG, WEBP (opcional)",
                 font=(FONT, 8), bg=THEME["card_bg"],
                 fg=THEME["txt_secondary"]).pack(anchor="w", pady=(2, 16))
        tk.Frame(pad, bg=THEME["border"], height=1).pack(fill="x", pady=(0,16))

        row = tk.Frame(pad, bg=THEME["card_bg"])
        row.pack(fill="x")

        preview_outer = tk.Frame(row, bg=THEME["border"], padx=1, pady=1)
        preview_outer.pack(side="left", padx=(0,20))
        preview_box = tk.Frame(preview_outer, bg=THEME["ct_bg"], width=150, height=110)
        preview_box.pack()
        preview_box.pack_propagate(False)
        self._lbl_preview = tk.Label(preview_box, text="Sin logo\nseleccionado",
                                     font=(FONT, 8), bg=THEME["ct_bg"],
                                     fg=THEME["txt_secondary"], justify="center")
        self._lbl_preview.pack(expand=True)

        right = tk.Frame(row, bg=THEME["card_bg"])
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text="Recomendado: fondo transparente (PNG)",
                 font=(FONT, 9, "bold"), bg=THEME["card_bg"],
                 fg=THEME["txt_primary"]).pack(anchor="w")
        tk.Label(right, text="Tamaño sugerido: 200×100 px o mayor",
                 font=(FONT, 8), bg=THEME["card_bg"],
                 fg=THEME["txt_secondary"]).pack(anchor="w", pady=(2,12))

        self._lbl_ruta = tk.Label(right,
                                  text="📄  " + os.path.basename(self._logo_src) if self._logo_src
                                  else "Ningún archivo seleccionado",
                                  font=(FONT, 8), bg=THEME["card_bg"],
                                  fg=THEME["acc_blue"], wraplength=280, justify="left")
        self._lbl_ruta.pack(anchor="w", pady=(0,10))

        btn_row = tk.Frame(right, bg=THEME["card_bg"])
        btn_row.pack(anchor="w")
        _label_btn(btn_row, "🖼  Seleccionar Logo",
                   self._select_logo, THEME["acc_blue"], THEME["acc_blue_dk"]).pack(side="left", padx=(0,8))
        _label_btn(btn_row, "✕  Quitar",
                   self._clear_logo, "#6B7280", "#4B5563").pack(side="left")

        if self._logo_src:
            self._preview_logo(self._logo_src)

    def _select_logo(self):
        path = filedialog.askopenfilename(
            title="Seleccionar logo de la empresa",
            filetypes=[("Imágenes","*.png *.jpg *.jpeg *.bmp *.gif *.webp *.ico"),
                       ("Todos","*.*")],
            parent=self.win)
        if path:
            self._logo_src = path
            self._lbl_ruta.config(text=f"📄  {os.path.basename(path)}")
            self._preview_logo(path)

    def _clear_logo(self):
        self._logo_src = ""
        self._lbl_preview.config(image="", text="Sin logo\nseleccionado")
        self._lbl_preview.image = None
        if hasattr(self, "_lbl_ruta"):
            self._lbl_ruta.config(text="Ningún archivo seleccionado")

    def _preview_logo(self, path):
        if not PIL_AVAILABLE or not os.path.isfile(path):
            self._lbl_preview.config(text=f"✅\n{os.path.basename(path)}")
            return
        try:
            img = Image.open(path).convert("RGBA")
            img.thumbnail((148, 108), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._lbl_preview.config(image=photo, text="", bg=THEME["ct_bg"])
            self._lbl_preview.image = photo
        except Exception:
            self._lbl_preview.config(text=f"✅\n{os.path.basename(path)}")

    # ── PASO 4: Confirmación ───────────────────────────────────
    def _paso_confirmacion(self):
        pad = tk.Frame(self.frm_content, bg=THEME["card_bg"], padx=56, pady=24)
        pad.pack(fill="both", expand=True)

        tk.Label(pad, text="✅  Revisión Final",
                 font=(FONT, 14, "bold"),
                 bg=THEME["card_bg"], fg=THEME["txt_primary"]).pack(anchor="w")
        tk.Label(pad, text="Verifique que los datos sean correctos antes de guardar",
                 font=(FONT, 8), bg=THEME["card_bg"],
                 fg=THEME["txt_secondary"]).pack(anchor="w", pady=(2, 12))
        tk.Frame(pad, bg=THEME["border"], height=1).pack(fill="x", pady=(0,12))

        # Empresa
        self._resumen_card(pad, "🏢  Empresa", [
            ("Razón Social",  self.vars["razon_social"].get() or "—"),
            ("RUC / NIT",     self.vars["ruc"].get() or "—"),
            ("Teléfono",      self.vars["telefono"].get() or "(no ingresado)"),
            ("Correo",        self.vars["correo"].get() or "(no ingresado)"),
            ("Dirección",     self.vars["direccion"].get() or "(no ingresado)"),
            ("Logo",          os.path.basename(self._logo_src) if self._logo_src else "(sin logo)"),
        ])

        # Admin
        self._resumen_card(pad, "👤  Cuenta Administrador", [
            ("Nombre",   self.admin_vars["nombre"].get() or "—"),
            ("Usuario",  self.admin_vars["usuario"].get() or "—"),
            ("Contraseña", "●●●●●●●●"),
            ("Pregunta", self.admin_vars["pregunta"].get()[:48] + "…"
                         if len(self.admin_vars["pregunta"].get()) > 48
                         else self.admin_vars["pregunta"].get()),
        ], bg="#F0FDF4", border="#A7F3D0", lbl_fg="#065F46")

        tk.Label(pad,
                 text="💡 Puede modificar estos datos en cualquier momento desde Configuración",
                 font=(FONT, 8), bg=THEME["card_bg"],
                 fg=THEME["txt_secondary"], justify="left").pack(anchor="w", pady=(8,0))

    def _resumen_card(self, parent, titulo, filas, bg="#EFF6FF",
                      border="#BFDBFE", lbl_fg="#1E40AF"):
        card = tk.Frame(parent, bg=bg,
                        highlightbackground=border,
                        highlightthickness=1, padx=20, pady=12)
        card.pack(fill="x", pady=(0,10))
        tk.Label(card, text=titulo, font=(FONT, 10, "bold"),
                 bg=bg, fg=lbl_fg).pack(anchor="w", pady=(0,6))
        for lbl, val in filas:
            row = tk.Frame(card, bg=bg)
            row.pack(fill="x", pady=2)
            is_missing = val in ["(no ingresado)", "(sin logo)", "—"]
            tk.Label(row, text=lbl, font=(FONT, 9, "bold"),
                     bg=bg, fg=lbl_fg, width=14, anchor="w").pack(side="left")
            tk.Label(row, text=val, font=(FONT, 9),
                     bg=bg,
                     fg=THEME["txt_secondary"] if is_missing else THEME["txt_primary"],
                     anchor="w").pack(side="left", padx=6)

    # ── Guardar ────────────────────────────────────────────────
    def _guardar(self):
        logo_dest = copy_logo(self._logo_src) if self._logo_src else ""
        company_data = {
            "razon_social": self.vars["razon_social"].get().strip(),
            "ruc":          self.vars["ruc"].get().strip(),
            "telefono":     self.vars["telefono"].get().strip(),
            "direccion":    self.vars["direccion"].get().strip(),
            "correo":       self.vars["correo"].get().strip(),
            "logo_path":    logo_dest,
        }

        ok_empresa = save_company_data(company_data)
        ok_admin   = create_admin_user(
            nombre   = self.admin_vars["nombre"].get().strip(),
            usuario  = self.admin_vars["usuario"].get().strip(),
            password = self.admin_vars["password"].get(),
            pregunta = self.admin_vars["pregunta"].get(),
            respuesta= self.admin_vars["respuesta"].get().strip(),
        )

        if ok_empresa and ok_admin:
            _mark_done()
            messagebox.showinfo("✅ Configuración guardada",
                f"¡El sistema está listo para usar!\n\n"
                f"Usuario: {self.admin_vars['usuario'].get().strip()}\n"
                f"Use la contraseña que acaba de crear para ingresar.",
                parent=self.win)
            self.win.destroy()
            self.on_complete()
        else:
            log = os.path.join(os.path.dirname(DB_FILE), "error_log.txt")
            messagebox.showerror("Error al guardar",
                f"No se pudieron guardar los datos.\nRevise: {log}",
                parent=self.win)
