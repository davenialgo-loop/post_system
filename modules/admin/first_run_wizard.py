"""
first_run_wizard.py
Asistente de configuración inicial — Primera vez que se inicia el sistema.
Diseño moderno consistente con el sistema POS.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import sqlite3, shutil, os, sys
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
    """Canvas con degradado #0D1B4B → #1A3A8F."""
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
    """Entry con borde que cambia al hacer foco."""
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
    if os.path.exists(FIRST_RUN_FLAG):
        return False
    try:
        conn = sqlite3.connect(DB_FILE)
        row  = conn.execute(
            "SELECT razon_social FROM empresa WHERE id=1").fetchone()
        conn.close()
        if row and row[0]:
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
        _mark_done()
        return True
    except Exception as e:
        print(f"[save_company_data] {e}")
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
        ("🏢", "Datos Empresa"),
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
            "Puede omitir los campos opcionales, pero Razón Social y RUC son obligatorios.",
            parent=self.win)

    def _init_vars(self):
        self.vars = {k: tk.StringVar() for k in
                     ["razon_social","ruc","telefono","correo","direccion"]}

    # ── Shell ──────────────────────────────────────────────────
    def _build_shell(self):
        W = 720

        # ── Header degradado ──────────────────────────────────
        hdr_canvas = _gradient_canvas(self.win, W, 80)
        hdr_canvas.create_text(W//2, 32, text="⚙️  Configuración Inicial del Sistema",
                                font=(FONT, 14, "bold"), fill=THEME["txt_white"], anchor="center")
        hdr_canvas.create_text(W//2, 56, text="Complete los datos de su empresa antes de comenzar",
                                font=(FONT, 9), fill="#9DB4E0", anchor="center")

        # ── Barra de pasos ────────────────────────────────────
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

        # ── Contenido ─────────────────────────────────────────
        self.frm_content = tk.Frame(self.win, bg=THEME["card_bg"], width=W)
        self.frm_content.pack(fill="both", expand=True)

        # ── Barra de navegación ───────────────────────────────
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

        # Footer info centrado
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

        # Botón back
        state = "normal" if n > 0 else "disabled"
        self._btn_back.config(state=state,
                              bg="#E5E7EB" if n > 0 else "#F3F4F6",
                              fg=THEME["txt_primary"] if n > 0 else THEME["txt_secondary"],
                              cursor="hand2" if n > 0 else "arrow")

        # Botón next — último paso cambia a Guardar
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
         self._paso_logo, self._paso_confirmacion][n]()

    def _next(self):
        if self._paso_actual == 1 and not self._validar_datos():
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

        # Intentar mostrar logo Venialgo
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

        # Cards de pasos
        for icon, titulo, desc in [
            ("🏢", "Datos de la empresa",
             "Razón social, RUC, teléfono y dirección"),
            ("🖼",  "Logo de la empresa",
             "Se mostrará en el sidebar y en los tickets"),
            ("✅", "Confirmación",
             "Revisión final antes de comenzar"),
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

        # Dos columnas
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

    # ── PASO 2: Logo ───────────────────────────────────────────
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

        # Preview + controles en fila
        row = tk.Frame(pad, bg=THEME["card_bg"])
        row.pack(fill="x")

        # Preview box
        preview_outer = tk.Frame(row, bg=THEME["border"], padx=1, pady=1)
        preview_outer.pack(side="left", padx=(0,20))
        preview_box = tk.Frame(preview_outer, bg=THEME["ct_bg"], width=150, height=110)
        preview_box.pack()
        preview_box.pack_propagate(False)
        self._lbl_preview = tk.Label(preview_box, text="Sin logo\nseleccionado",
                                     font=(FONT, 8), bg=THEME["ct_bg"],
                                     fg=THEME["txt_secondary"], justify="center")
        self._lbl_preview.pack(expand=True)

        # Controles
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

        # Si ya hay logo, mostrarlo
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

    # ── PASO 3: Confirmación ───────────────────────────────────
    def _paso_confirmacion(self):
        pad = tk.Frame(self.frm_content, bg=THEME["card_bg"], padx=56, pady=24)
        pad.pack(fill="both", expand=True)

        tk.Label(pad, text="✅  Revisión Final",
                 font=(FONT, 14, "bold"),
                 bg=THEME["card_bg"], fg=THEME["txt_primary"]).pack(anchor="w")
        tk.Label(pad, text="Verifique que los datos sean correctos antes de guardar",
                 font=(FONT, 8), bg=THEME["card_bg"],
                 fg=THEME["txt_secondary"]).pack(anchor="w", pady=(2, 16))
        tk.Frame(pad, bg=THEME["border"], height=1).pack(fill="x", pady=(0,16))

        # Card resumen
        card = tk.Frame(pad, bg="#EFF6FF",
                        highlightbackground="#BFDBFE",
                        highlightthickness=1, padx=20, pady=16)
        card.pack(fill="x", pady=(0,16))

        resumen = [
            ("🏢  Razón Social",  self.vars["razon_social"].get() or "—"),
            ("🔢  RUC / NIT",     self.vars["ruc"].get() or "—"),
            ("📞  Teléfono",      self.vars["telefono"].get() or "(no ingresado)"),
            ("✉   Correo",        self.vars["correo"].get() or "(no ingresado)"),
            ("📍  Dirección",     self.vars["direccion"].get() or "(no ingresado)"),
            ("🖼   Logo",         os.path.basename(self._logo_src) if self._logo_src else "(sin logo)"),
        ]
        for lbl, val in resumen:
            row = tk.Frame(card, bg="#EFF6FF")
            row.pack(fill="x", pady=3)
            tk.Label(row, text=lbl, font=(FONT, 9, "bold"),
                     bg="#EFF6FF", fg="#1E40AF",
                     width=18, anchor="w").pack(side="left")
            is_missing = val in ["(no ingresado)", "(sin logo)", "—"]
            tk.Label(row, text=val, font=(FONT, 9),
                     bg="#EFF6FF",
                     fg=THEME["txt_secondary"] if is_missing else THEME["txt_primary"],
                     anchor="w").pack(side="left", padx=6)

        tk.Label(pad,
                 text="💡 Puede modificar estos datos en cualquier momento desde\n"
                      "   Configuración → Empresa",
                 font=(FONT, 8), bg=THEME["card_bg"],
                 fg=THEME["txt_secondary"], justify="left").pack(anchor="w")

    # ── Guardar ────────────────────────────────────────────────
    def _guardar(self):
        logo_dest = copy_logo(self._logo_src) if self._logo_src else ""
        data = {
            "razon_social": self.vars["razon_social"].get().strip(),
            "ruc":          self.vars["ruc"].get().strip(),
            "telefono":     self.vars["telefono"].get().strip(),
            "direccion":    self.vars["direccion"].get().strip(),
            "correo":       self.vars["correo"].get().strip(),
            "logo_path":    logo_dest,
        }
        if save_company_data(data):
            messagebox.showinfo("✅ Configuración guardada",
                "Los datos de la empresa han sido guardados.\n"
                "¡El sistema está listo para usar!",
                parent=self.win)
            self.win.destroy()
            self.on_complete()
        else:
            log = os.path.join(os.path.dirname(DB_FILE), "error_log.txt")
            messagebox.showerror("Error al guardar",
                f"No se pudieron guardar los datos.\nRevise el archivo de log:\n{log}",
                parent=self.win)
