"""
first_run_wizard.py
Asistente de configuración inicial — Primera vez que se inicia el sistema.
Recopila datos de la empresa y logo antes de acceder al POS.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import shutil
import os
from pathlib import Path

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from config.settings import COLORS, FONTS, SPACING
except ImportError:
    COLORS  = {'primary': '#2563eb', 'bg_card': '#ffffff', 'bg_main': '#f1f5f9',
               'bg_sidebar': '#1e293b', 'text_white': '#ffffff',
               'text_secondary': '#64748b', 'success': '#16a34a',
               'danger': '#dc2626', 'warning': '#d97706'}
    FONTS   = {'family': 'Segoe UI', 'title': 16, 'subtitle': 13, 'body': 10, 'small': 9}
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
def _get_logo_dir():
    import sys
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.path.expanduser("~")
    d = os.path.join(base, "VenialgoPOS", "logos")
    os.makedirs(d, exist_ok=True)
    return d
LOGO_DIR = Path(_get_logo_dir())
def _get_first_run_flag():
    import sys
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.path.expanduser("~")
    return os.path.join(base, "VenialgoPOS", ".first_run_done")
FIRST_RUN_FLAG = _get_first_run_flag()

FOOTER_INFO = {
    "empresa":  "Venialgo Sistemas",
    "email":    "davenialgo@proton.me",
    "whatsapp": "+595 994-686 493",
    "web":      "www.venialgosistemas.com",
}


# ════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════

def is_first_run() -> bool:
    """Retorna True si es la primera vez que se ejecuta el sistema."""
    if os.path.exists(FIRST_RUN_FLAG):
        return False
    # También verificar si ya hay datos de empresa cargados
    try:
        conn = sqlite3.connect(DB_FILE)
        row  = conn.execute(
            "SELECT razon_social FROM empresa WHERE id=1"
        ).fetchone()
        conn.close()
        if row and row[0] and row[0].strip():
            # Ya tiene datos → marcar como completado
            _mark_done()
            return False
    except Exception:
        pass
    return True


def _mark_done():
    try:
        os.makedirs(os.path.dirname(FIRST_RUN_FLAG), exist_ok=True)
        with open(FIRST_RUN_FLAG, 'w') as f:
            f.write("done")
    except Exception as e:
        print(f"Aviso _mark_done: {e}")


def save_company_data(data: dict) -> bool:
    """
    Guarda datos de empresa en la BD (AppData/VenialgoPOS/pos_database.db)
    """
    import traceback
    try:
        # Asegurar que el directorio existe
        db_dir = os.path.dirname(DB_FILE)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        conn = sqlite3.connect(DB_FILE)
        c    = conn.cursor()

        # Eliminar y recrear tabla empresa con todas las columnas
        c.execute("""
            CREATE TABLE IF NOT EXISTS empresa (
                id           INTEGER PRIMARY KEY,
                razon_social TEXT DEFAULT '',
                ruc          TEXT DEFAULT '',
                telefono     TEXT DEFAULT '',
                direccion    TEXT DEFAULT '',
                correo       TEXT DEFAULT '',
                logo_path    TEXT DEFAULT ''
            )
        """)

        # Agregar columna logo_path si no existe
        try:
            c.execute("ALTER TABLE empresa ADD COLUMN logo_path TEXT DEFAULT ''")
        except Exception:
            pass  # Ya existe, ignorar

        # Verificar si existe registro id=1
        c.execute("SELECT COUNT(*) FROM empresa WHERE id=1")
        existe = c.fetchone()[0] > 0

        vals = (
            data.get("razon_social", ""),
            data.get("ruc", ""),
            data.get("telefono", ""),
            data.get("direccion", ""),
            data.get("correo", ""),
            data.get("logo_path", ""),
        )

        if existe:
            c.execute("""
                UPDATE empresa
                SET razon_social=?, ruc=?, telefono=?,
                    direccion=?, correo=?, logo_path=?
                WHERE id=1
            """, vals)
        else:
            c.execute("""
                INSERT INTO empresa
                    (id, razon_social, ruc, telefono, direccion, correo, logo_path)
                VALUES (1, ?, ?, ?, ?, ?, ?)
            """, vals)

        conn.commit()
        conn.close()
        _mark_done()  # No bloquea aunque falle (tiene try/except interno)
        return True

    except Exception as e:
        err = traceback.format_exc()
        print(f"[ERROR save_company_data]\n{err}")
        # Guardar log para diagnostico
        try:
            log_path = os.path.join(os.path.dirname(DB_FILE), "error_log.txt")
            with open(log_path, "a", encoding="utf-8") as lf:
                lf.write(f"\n--- save_company_data error ---\n{err}\n")
                lf.write(f"DB_FILE = {DB_FILE}\n")
                lf.write(f"data = {data}\n")
        except Exception:
            pass
        return False


def get_company_data() -> dict:
    """Carga datos de empresa desde la BD."""
    try:
        conn = sqlite3.connect(DB_FILE)
        c    = conn.cursor()
        c.execute("SELECT razon_social, ruc, telefono, direccion, correo, logo_path FROM empresa WHERE id=1")
        row = c.fetchone()
        conn.close()
        if row:
            return {
                "razon_social": row[0] or "",
                "ruc":          row[1] or "",
                "telefono":     row[2] or "",
                "direccion":    row[3] or "",
                "correo":       row[4] or "",
                "logo_path":    row[5] or "",
            }
    except Exception:
        pass
    return {}


def copy_logo(src_path: str) -> str:
    """
    Copia el logo a AppData/VenialgoPOS/logos/ y lo convierte a PNG.
    Retorna la ruta del logo guardado, o la ruta original si falla.
    """
    if not src_path or not os.path.exists(src_path):
        return ""

    try:
        LOGO_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    dest = LOGO_DIR / "company_logo.png"

    try:
        if PIL_AVAILABLE:
            img = Image.open(src_path).convert("RGBA")
            img.thumbnail((400, 200), Image.LANCZOS)
            img.save(str(dest), "PNG")
            return str(dest)
        else:
            shutil.copy2(src_path, str(dest))
            return str(dest)
    except Exception as e:
        print(f"Aviso logo: {e}")
        # Si no se puede copiar, usar la ruta original directamente
        return src_path


def load_logo_tk(size: tuple = (120, 60)) -> "ImageTk.PhotoImage | None":
    """Carga el logo como PhotoImage para Tkinter."""
    if not PIL_AVAILABLE:
        return None
    data = get_company_data()
    logo_path = data.get("logo_path", "")
    if not logo_path or not os.path.exists(logo_path):
        return None
    try:
        img = Image.open(logo_path).convert("RGBA")
        img.thumbnail(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


# ════════════════════════════════════════════════════════════
#  WIZARD UI
# ════════════════════════════════════════════════════════════

class FirstRunWizard:
    """
    Asistente de primera configuración.
    Bloquea el sistema hasta completar los datos obligatorios.

    Uso:
        wizard = FirstRunWizard(root, on_complete=callback)
        # on_complete() se llama cuando el usuario guarda los datos.
    """

    PASOS = ["Bienvenida", "Datos Empresa", "Logo", "Confirmación"]

    def __init__(self, root, on_complete):
        self.root        = root
        self.on_complete = on_complete
        self._paso_actual = 0
        self._logo_src    = ""   # ruta original seleccionada

        self.win = root
        self.win.title("Configuracion inicial - Venialgo Sistemas POS")
        self.win.geometry("700x600")
        self.win.configure(bg=COLORS['bg_card'])
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self._on_close_attempt)
        self._center()
        self._init_vars()
        self._build_shell()
        self._show_paso(0)

    def _center(self):
        self.win.update_idletasks()
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        x  = (sw - 700) // 2
        y  = (sh - 560) // 2
        self.win.geometry(f"700x600+{x}+{y}")

    def _on_close_attempt(self):
        messagebox.showwarning(
            "Configuración requerida",
            "Debe completar la configuración inicial para usar el sistema.\n"
            "Puede omitir los campos opcionales, pero Razón Social y RUC son obligatorios.",
            parent=self.win
        )

    def _init_vars(self):
        self.vars = {
            "razon_social": tk.StringVar(),
            "ruc":          tk.StringVar(),
            "telefono":     tk.StringVar(),
            "direccion":    tk.StringVar(),
            "correo":       tk.StringVar(),
        }

    # ── Shell (partes fijas) ──────────────────────────────────
    def _build_shell(self):
        # ── Header azul ──────────────────────────────────────
        self.frm_header = tk.Frame(self.win, bg=COLORS['bg_sidebar'], height=70)
        self.frm_header.pack(fill='x')
        self.frm_header.pack_propagate(False)

        tk.Label(self.frm_header,
                 text="⚙️  Configuración Inicial del Sistema",
                 font=(FONTS['family'], 14, 'bold'),
                 bg=COLORS['bg_sidebar'], fg='white').pack(pady=(12,2))
        tk.Label(self.frm_header,
                 text="Complete los datos de su empresa antes de comenzar",
                 font=(FONTS['family'], FONTS['small']),
                 bg=COLORS['bg_sidebar'], fg='#94a3b8').pack()

        # ── Barra de pasos ────────────────────────────────────
        self.frm_steps = tk.Frame(self.win, bg='#e2e8f0', height=44)
        self.frm_steps.pack(fill='x')
        self.frm_steps.pack_propagate(False)
        self._step_labels = []
        for i, nombre in enumerate(self.PASOS):
            frm = tk.Frame(self.frm_steps, bg='#e2e8f0')
            frm.pack(side='left', expand=True, fill='both')
            lbl = tk.Label(frm,
                           text=f"{'●' if i==0 else '○'}  {nombre}",
                           font=(FONTS['family'], FONTS['small']),
                           bg='#e2e8f0', fg='#94a3b8', pady=10)
            lbl.pack(expand=True)
            self._step_labels.append(lbl)

        # ── Barra inferior (botones) - ANTES del content para reservar espacio
        ttk.Separator(self.win).pack(fill='x', side='bottom')
        frm_nav = tk.Frame(self.win, bg='#f8fafc', pady=10)
        frm_nav.pack(fill='x', side='bottom')

        self.btn_back = tk.Button(frm_nav, text="< Anterior",
                                  command=self._prev,
                                  bg='#e2e8f0', fg='#374151',
                                  font=(FONTS['family'], FONTS['body']),
                                  relief='flat', padx=16, pady=8,
                                  cursor='hand2', width=14)
        self.btn_back.pack(side='left', padx=20)

        self.btn_next = tk.Button(frm_nav, text="Siguiente >",
                                  command=self._next,
                                  bg=COLORS['primary'], fg='white',
                                  font=(FONTS['family'], FONTS['body'], 'bold'),
                                  relief='flat', padx=16, pady=8,
                                  cursor='hand2', width=14)
        self.btn_next.pack(side='right', padx=20)

        tk.Label(frm_nav,
                 text=f"{FOOTER_INFO['empresa']}  |  {FOOTER_INFO['email']}  |  {FOOTER_INFO['whatsapp']}",
                 font=(FONTS['family'], 7),
                 bg='#f8fafc', fg='#cbd5e1').pack()

        # ── Area de contenido - DESPUES para que ocupe el espacio restante
        self.frm_content = tk.Frame(self.win, bg=COLORS['bg_card'])
        self.frm_content.pack(fill='both', expand=True, padx=0, pady=0)

    def _update_steps(self, paso):
        for i, lbl in enumerate(self._step_labels):
            if i < paso:
                lbl.config(text=f"✓  {self.PASOS[i]}",
                           bg='#dcfce7', fg='#16a34a')
                lbl.master.config(bg='#dcfce7')
            elif i == paso:
                lbl.config(text=f"●  {self.PASOS[i]}",
                           bg=COLORS['primary'], fg='white')
                lbl.master.config(bg=COLORS['primary'])
            else:
                lbl.config(text=f"○  {self.PASOS[i]}",
                           bg='#e2e8f0', fg='#94a3b8')
                lbl.master.config(bg='#e2e8f0')

    # ── Navegación ────────────────────────────────────────────
    def _show_paso(self, n):
        self._paso_actual = n
        for w in self.frm_content.winfo_children():
            w.destroy()
        self._update_steps(n)

        # Mostrar/ocultar botón Anterior
        self.btn_back.config(state='normal' if n > 0 else 'disabled')

        # Último paso
        if n == len(self.PASOS) - 1:
            self.btn_next.config(text="✅  Guardar y Comenzar",
                                 bg=COLORS['success'])
        else:
            self.btn_next.config(text="Siguiente →",
                                 bg=COLORS['primary'])

        pasos = [self._paso_bienvenida,
                 self._paso_datos,
                 self._paso_logo,
                 self._paso_confirmacion]
        pasos[n]()

    def _next(self):
        if self._paso_actual == 1:
            if not self._validar_datos():
                return
        if self._paso_actual == len(self.PASOS) - 1:
            self._guardar()
        else:
            self._show_paso(self._paso_actual + 1)

    def _prev(self):
        if self._paso_actual > 0:
            self._show_paso(self._paso_actual - 1)

    # ── PASO 0: Bienvenida ────────────────────────────────────
    def _paso_bienvenida(self):
        frm = tk.Frame(self.frm_content, bg=COLORS['bg_card'], padx=50, pady=30)
        frm.pack(fill='both', expand=True)

        tk.Label(frm, text="🏪", font=(FONTS['family'], 56),
                 bg=COLORS['bg_card']).pack(pady=(10,8))
        tk.Label(frm,
                 text="¡Bienvenido al Sistema POS!",
                 font=(FONTS['family'], 16, 'bold'),
                 bg=COLORS['bg_card'], fg=COLORS['primary']).pack()
        tk.Label(frm,
                 text="Este asistente lo guiará en la configuración inicial.\nSolo tomará unos minutos.",
                 font=(FONTS['family'], FONTS['body']),
                 bg=COLORS['bg_card'], fg=COLORS['text_secondary'],
                 justify='center').pack(pady=(8,20))

        # Qué se configura
        pasos_info = [
            ("📋", "Datos de la empresa",  "Razón social, RUC, teléfono, dirección"),
            ("🖼️", "Logo de la empresa",   "Se mostrará en el header y en los tickets"),
            ("✅", "Confirmación",          "Revisión final antes de comenzar"),
        ]
        for ico, titulo, desc in pasos_info:
            r = tk.Frame(frm, bg='#f0f9ff', padx=14, pady=8,
                         relief='flat', bd=0)
            r.pack(fill='x', pady=3)
            tk.Label(r, text=ico, font=(FONTS['family'], 16),
                     bg='#f0f9ff').pack(side='left', padx=(0,10))
            c = tk.Frame(r, bg='#f0f9ff')
            c.pack(side='left', fill='x', expand=True)
            tk.Label(c, text=titulo,
                     font=(FONTS['family'], FONTS['body'], 'bold'),
                     bg='#f0f9ff', fg='#1e293b',
                     anchor='w').pack(fill='x')
            tk.Label(c, text=desc,
                     font=(FONTS['family'], FONTS['small']),
                     bg='#f0f9ff', fg='#64748b',
                     anchor='w').pack(fill='x')

    # ── PASO 1: Datos empresa ─────────────────────────────────
    def _paso_datos(self):
        frm = tk.Frame(self.frm_content, bg=COLORS['bg_card'], padx=50, pady=20)
        frm.pack(fill='both', expand=True)

        tk.Label(frm, text="📋  Datos de la Empresa",
                 font=(FONTS['family'], FONTS['subtitle'], 'bold'),
                 bg=COLORS['bg_card'], fg=COLORS['primary']).pack(anchor='w', pady=(0,4))
        tk.Label(frm, text="Los campos con * son obligatorios",
                 font=(FONTS['family'], FONTS['small']),
                 bg=COLORS['bg_card'], fg='#94a3b8').pack(anchor='w', pady=(0,12))
        ttk.Separator(frm).pack(fill='x', pady=(0,14))

        campos = [
            ("Razón Social *",     "razon_social", False),
            ("RUC / NIT *",        "ruc",          False),
            ("Teléfono",           "telefono",     False),
            ("Correo electrónico", "correo",       False),
            ("Dirección",          "direccion",    False),
        ]

        for label, key, _ in campos:
            rf = tk.Frame(frm, bg=COLORS['bg_card'])
            rf.pack(fill='x', pady=5)
            tk.Label(rf, text=label,
                     font=(FONTS['family'], FONTS['small'], 'bold'),
                     bg=COLORS['bg_card'], fg='#374151',
                     width=20, anchor='w').pack(side='left')
            e = tk.Entry(rf, textvariable=self.vars[key],
                         font=(FONTS['family'], FONTS['body']),
                         relief='solid', bd=1, width=36)
            e.pack(side='left', padx=(6,0))

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

    # ── PASO 2: Logo ──────────────────────────────────────────
    def _paso_logo(self):
        frm = tk.Frame(self.frm_content, bg=COLORS['bg_card'], padx=50, pady=20)
        frm.pack(fill='both', expand=True)

        tk.Label(frm, text="🖼️  Logo de la Empresa",
                 font=(FONTS['family'], FONTS['subtitle'], 'bold'),
                 bg=COLORS['bg_card'], fg=COLORS['primary']).pack(anchor='w', pady=(0,4))
        tk.Label(frm,
                 text="El logo se mostrará en el header del sistema y en todos los tickets/facturas.\n"
                      "Formatos aceptados: PNG, JPG, JPEG, BMP, GIF, WEBP, ICO  (este paso es opcional)",
                 font=(FONTS['family'], FONTS['small']),
                 bg=COLORS['bg_card'], fg='#64748b', justify='left').pack(anchor='w', pady=(0,14))
        ttk.Separator(frm).pack(fill='x', pady=(0,16))

        # Área de previsualización
        self.frm_preview = tk.Frame(frm, bg='#f8fafc', width=300, height=140,
                                    relief='solid', bd=1)
        self.frm_preview.pack(pady=(0,16))
        self.frm_preview.pack_propagate(False)
        self._lbl_preview = tk.Label(self.frm_preview,
                                     text="Sin logo seleccionado\n\nHaga clic en 'Seleccionar Logo'",
                                     font=(FONTS['family'], FONTS['small']),
                                     bg='#f8fafc', fg='#94a3b8', justify='center')
        self._lbl_preview.pack(expand=True)

        # Si ya hay logo seleccionado, mostrarlo
        if self._logo_src:
            self._preview_logo(self._logo_src)

        # Botones
        frm_btns = tk.Frame(frm, bg=COLORS['bg_card'])
        frm_btns.pack()
        tk.Button(frm_btns, text="📁  Seleccionar Logo",
                  command=self._select_logo,
                  bg=COLORS['primary'], fg='white',
                  font=(FONTS['family'], FONTS['body'], 'bold'),
                  relief='flat', padx=14, pady=8, cursor='hand2',
                  width=20).pack(side='left', padx=(0,10))
        tk.Button(frm_btns, text="🗑️  Quitar logo",
                  command=self._clear_logo,
                  bg='#e2e8f0', fg='#374151',
                  font=(FONTS['family'], FONTS['body']),
                  relief='flat', padx=14, pady=8, cursor='hand2',
                  width=14).pack(side='left')

        # Ruta seleccionada
        self._lbl_ruta = tk.Label(frm,
                                  text=f"📄 {self._logo_src}" if self._logo_src else "Ningún archivo seleccionado",
                                  font=(FONTS['family'], FONTS['small']),
                                  bg=COLORS['bg_card'], fg='#64748b',
                                  wraplength=500)
        self._lbl_ruta.pack(pady=(10,0))

    def _select_logo(self):
        path = filedialog.askopenfilename(
            title="Seleccionar logo de la empresa",
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif *.webp *.ico *.tiff"),
                ("PNG",  "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("Todos los archivos", "*.*"),
            ],
            parent=self.win
        )
        if path:
            self._logo_src = path
            self._lbl_ruta.config(text=f"📄 {path}")
            self._preview_logo(path)

    def _clear_logo(self):
        self._logo_src = ""
        self._lbl_preview.config(image="", text="Sin logo seleccionado\n\nHaga clic en 'Seleccionar Logo'")
        self._lbl_preview.image = None
        if hasattr(self, '_lbl_ruta'):
            self._lbl_ruta.config(text="Ningún archivo seleccionado")

    def _preview_logo(self, path):
        if not PIL_AVAILABLE or not os.path.exists(path):
            self._lbl_preview.config(text=f"Logo seleccionado:\n{os.path.basename(path)}")
            return
        try:
            img = Image.open(path).convert("RGBA")
            img.thumbnail((290, 130), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._lbl_preview.config(image=photo, text="",
                                     bg='#f8fafc')
            self._lbl_preview.image = photo   # evitar GC
        except Exception as e:
            self._lbl_preview.config(text=f"Vista previa no disponible\n{os.path.basename(path)}")

    # ── PASO 3: Confirmación ──────────────────────────────────
    def _paso_confirmacion(self):
        frm = tk.Frame(self.frm_content, bg=COLORS['bg_card'], padx=50, pady=16)
        frm.pack(fill='both', expand=True)

        tk.Label(frm, text="✅  Confirmación de datos",
                 font=(FONTS['family'], FONTS['subtitle'], 'bold'),
                 bg=COLORS['bg_card'], fg=COLORS['primary']).pack(anchor='w', pady=(0,4))
        tk.Label(frm, text="Verifique que los datos sean correctos antes de guardar",
                 font=(FONTS['family'], FONTS['small']),
                 bg=COLORS['bg_card'], fg='#94a3b8').pack(anchor='w', pady=(0,10))
        ttk.Separator(frm).pack(fill='x', pady=(0,12))

        # Mostrar resumen
        card = tk.Frame(frm, bg='#f0f9ff', padx=20, pady=16,
                        relief='solid', bd=1)
        card.pack(fill='x')

        campos = [
            ("📋 Razón Social",  self.vars["razon_social"].get()),
            ("🔢 RUC / NIT",     self.vars["ruc"].get()),
            ("📞 Teléfono",      self.vars["telefono"].get() or "(no ingresado)"),
            ("✉️ Correo",        self.vars["correo"].get()   or "(no ingresado)"),
            ("📍 Dirección",     self.vars["direccion"].get() or "(no ingresado)"),
            ("🖼️ Logo",          os.path.basename(self._logo_src) if self._logo_src else "(sin logo)"),
        ]

        for lbl, val in campos:
            rf = tk.Frame(card, bg='#f0f9ff')
            rf.pack(fill='x', pady=3)
            tk.Label(rf, text=lbl,
                     font=(FONTS['family'], FONTS['small'], 'bold'),
                     bg='#f0f9ff', fg='#374151',
                     width=18, anchor='w').pack(side='left')
            tk.Label(rf, text=val,
                     font=(FONTS['family'], FONTS['small']),
                     bg='#f0f9ff',
                     fg=COLORS['primary'] if val not in ["(no ingresado)", "(sin logo)"] else '#94a3b8',
                     anchor='w').pack(side='left', padx=8)

        tk.Label(frm,
                 text="💡 Puede modificar estos datos en cualquier momento desde\n"
                      "Administración → Datos de Empresa",
                 font=(FONTS['family'], FONTS['small']),
                 bg=COLORS['bg_card'], fg='#64748b', justify='left').pack(
            anchor='w', pady=(16,0))

    # ── Guardar ───────────────────────────────────────────────
    def _guardar(self):
        # Copiar logo si se selecciono
        logo_dest = ""
        if self._logo_src:
            logo_dest = copy_logo(self._logo_src)
            # No mostrar advertencia si falla - continuar igual

        data = {
            "razon_social": self.vars["razon_social"].get().strip(),
            "ruc":          self.vars["ruc"].get().strip(),
            "telefono":     self.vars["telefono"].get().strip(),
            "direccion":    self.vars["direccion"].get().strip(),
            "correo":       self.vars["correo"].get().strip(),
            "logo_path":    logo_dest,
        }

        if save_company_data(data):
            messagebox.showinfo("Configuracion guardada",
                "Los datos de la empresa han sido guardados.\n"
                "El sistema esta listo para usar!",
                parent=self.win)
            self.win.destroy()
            self.on_complete()
        else:
            # Mostrar ruta del log para diagnostico
            import os as _os2
            log = _os2.path.join(_os2.path.dirname(DB_FILE), "error_log.txt")
            messagebox.showerror("Error al guardar",
                f"No se pudieron guardar los datos.\n\n"
                f"Revise el archivo de log:\n{log}",
                parent=self.win)
