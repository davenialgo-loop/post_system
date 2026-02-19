"""
Módulo de Administración del Sistema POS
Gestión de usuarios, empresa e impresoras
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import hashlib
from datetime import datetime

# ─── Importar configuración del proyecto ────────────────
try:
    from config.settings import COLORS, FONTS, SPACING
except ImportError:
    # Fallback si se ejecuta en modo standalone
    COLORS = {
        'primary': '#2563eb', 'bg_main': '#f1f5f9',
        'bg_card': '#ffffff', 'bg_sidebar': '#1e293b',
        'text_white': '#ffffff', 'text_secondary': '#64748b',
        'success': '#16a34a', 'danger': '#dc2626',
        'warning': '#d97706', 'border': '#e2e8f0',
    }
    FONTS  = {'family': 'Segoe UI', 'title': 16, 'subtitle': 13,
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
ROLES   = ["Administrador", "Supervisor", "Cajero"]

# ════════════════════════════════════════════════════════
#  DB helpers
# ════════════════════════════════════════════════════════
def _ensure_tables():
    """Crea tablas nuevas si no existen (migración no destructiva)."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS empresa (
            id           INTEGER PRIMARY KEY,
            razon_social TEXT DEFAULT '',
            ruc          TEXT DEFAULT '',
            telefono     TEXT DEFAULT '',
            direccion    TEXT DEFAULT '',
            correo       TEXT DEFAULT ''
        )
    """)
    c.execute("SELECT COUNT(*) FROM empresa")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO empresa VALUES (1,'','','','','')")

    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre     TEXT NOT NULL,
            usuario    TEXT UNIQUE NOT NULL,
            password   TEXT NOT NULL,
            rol        TEXT NOT NULL,
            activo     INTEGER DEFAULT 1,
            creado_en  TEXT
        )
    """)
    c.execute("SELECT COUNT(*) FROM usuarios")
    if c.fetchone()[0] == 0:
        pwd = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("""INSERT INTO usuarios (nombre,usuario,password,rol,activo,creado_en)
                     VALUES (?,?,?,?,?,?)""",
                  ("Administrador","admin", pwd,"Administrador",1,
                   datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    c.execute("""
        CREATE TABLE IF NOT EXISTS impresoras (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre         TEXT NOT NULL,
            tipo           TEXT DEFAULT 'Térmica',
            puerto         TEXT DEFAULT '',
            predeterminada INTEGER DEFAULT 0,
            ancho_papel    INTEGER DEFAULT 80
        )
    """)
    conn.commit()
    conn.close()


def _get_empresa():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id,razon_social,ruc,telefono,direccion,correo FROM empresa WHERE id=1")
    row = c.fetchone()
    conn.close()
    if row:
        return dict(zip(["id","razon_social","ruc","telefono","direccion","correo"], row))
    return {}


def _save_empresa(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""UPDATE empresa SET razon_social=?,ruc=?,telefono=?,direccion=?,correo=?
                 WHERE id=1""",
              (data["razon_social"],data["ruc"],data["telefono"],
               data["direccion"],data["correo"]))
    conn.commit()
    conn.close()


def _get_usuarios():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id,nombre,usuario,rol,activo,creado_en FROM usuarios ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows


def _save_usuario(data, uid=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if uid:
        if data.get("password"):
            pwd = hashlib.sha256(data["password"].encode()).hexdigest()
            c.execute("""UPDATE usuarios SET nombre=?,usuario=?,password=?,rol=?,activo=?
                         WHERE id=?""",
                      (data["nombre"],data["usuario"],pwd,data["rol"],data["activo"],uid))
        else:
            c.execute("""UPDATE usuarios SET nombre=?,usuario=?,rol=?,activo=?
                         WHERE id=?""",
                      (data["nombre"],data["usuario"],data["rol"],data["activo"],uid))
    else:
        pwd = hashlib.sha256(data["password"].encode()).hexdigest()
        c.execute("""INSERT INTO usuarios (nombre,usuario,password,rol,activo,creado_en)
                     VALUES (?,?,?,?,?,?)""",
                  (data["nombre"],data["usuario"],pwd,data["rol"],1,
                   datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()


def _delete_usuario(uid):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM usuarios WHERE id=?", (uid,))
    conn.commit()
    conn.close()


def _get_impresoras():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id,nombre,tipo,puerto,predeterminada,ancho_papel FROM impresoras ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows


def _save_impresora(data, iid=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if data.get("predeterminada"):
        c.execute("UPDATE impresoras SET predeterminada=0")
    if iid:
        c.execute("""UPDATE impresoras SET nombre=?,tipo=?,puerto=?,predeterminada=?,ancho_papel=?
                     WHERE id=?""",
                  (data["nombre"],data["tipo"],data["puerto"],
                   data["predeterminada"],data["ancho_papel"],iid))
    else:
        c.execute("""INSERT INTO impresoras (nombre,tipo,puerto,predeterminada,ancho_papel)
                     VALUES (?,?,?,?,?)""",
                  (data["nombre"],data["tipo"],data["puerto"],
                   data["predeterminada"],data["ancho_papel"]))
    conn.commit()
    conn.close()


def _delete_impresora(iid):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM impresoras WHERE id=?", (iid,))
    conn.commit()
    conn.close()


# ════════════════════════════════════════════════════════
#  Helpers UI
# ════════════════════════════════════════════════════════
def _btn(parent, text, cmd, bg=None, fg=None, width=16):
    bg = bg or COLORS['primary']
    fg = fg or COLORS['text_white']
    b = tk.Button(parent, text=text, command=cmd,
                  bg=bg, fg=fg, relief='flat',
                  font=(FONTS['family'], FONTS['body'], 'bold'),
                  padx=10, pady=7, cursor='hand2', width=width)
    orig = bg
    b.bind('<Enter>', lambda e: b.config(bg=_light(orig)))
    b.bind('<Leave>', lambda e: b.config(bg=orig))
    return b


def _light(hex_c):
    r = min(255, int(hex_c[1:3],16)+28)
    g = min(255, int(hex_c[3:5],16)+28)
    b = min(255, int(hex_c[5:7],16)+28)
    return f"#{r:02x}{g:02x}{b:02x}"


def _lbl_entry(parent, label, row, col=0, show=None, width=30):
    tk.Label(parent, text=label,
             bg=COLORS['bg_card'],
             font=(FONTS['family'], FONTS['body']),
             fg='#374151').grid(row=row, column=col,
                                sticky='w', pady=5, padx=6)
    var = tk.StringVar()
    e = tk.Entry(parent, textvariable=var,
                 font=(FONTS['family'], FONTS['body']),
                 width=width, relief='solid', bd=1,
                 show=show or '')
    e.grid(row=row, column=col+1, pady=5, padx=6)
    return var


# ════════════════════════════════════════════════════════
#  MÓDULO PRINCIPAL
# ════════════════════════════════════════════════════════
class AdminModule:
    """
    Módulo de Administración.
    Se instancia igual que los demás módulos del POS:
        AdminModule(content_area, db, current_user)
    current_user = dict con keys: id, nombre, rol
    """

    def __init__(self, parent, db, current_user=None):
        self.parent = parent
        self.db     = db
        self.current_user = current_user or {"id": 0, "nombre": "Admin", "rol": "Administrador"}

        _ensure_tables()
        self._build()

    # ── Estructura principal ──────────────────────────
    def _build(self):
        self.frame = tk.Frame(self.parent, bg=COLORS['bg_main'])
        self.frame.pack(fill='both', expand=True)

        # Header del módulo
        hdr = tk.Frame(self.frame, bg=COLORS['bg_card'], pady=14)
        hdr.pack(fill='x', padx=0)
        tk.Label(hdr, text="⚙️  Panel de Administración",
                 font=(FONTS['family'], FONTS['title'], 'bold'),
                 bg=COLORS['bg_card'], fg=COLORS['primary']).pack(side='left', padx=20)
        tk.Label(hdr, text=f"Usuario: {self.current_user['nombre']}  |  Rol: {self.current_user['rol']}",
                 font=(FONTS['family'], FONTS['small']),
                 bg=COLORS['bg_card'], fg=COLORS['text_secondary']).pack(side='right', padx=20)

        # Notebook con las 3 secciones
        nb = ttk.Notebook(self.frame)
        nb.pack(fill='both', expand=True, padx=16, pady=12)

        self._tab_empresa(nb)
        self._tab_usuarios(nb)
        self._tab_impresoras(nb)

    # ════════════════════════════════════════════════════
    #  TAB 1 — DATOS DE EMPRESA
    # ════════════════════════════════════════════════════
    def _tab_empresa(self, nb):
        outer = tk.Frame(nb, bg=COLORS['bg_main'])
        nb.add(outer, text="  🏢  Empresa  ")

        card = tk.Frame(outer, bg=COLORS['bg_card'],
                        padx=30, pady=24, relief='flat', bd=0)
        card.pack(padx=30, pady=24, anchor='nw')

        tk.Label(card, text="Datos de la Empresa",
                 font=(FONTS['family'], FONTS['subtitle'], 'bold'),
                 bg=COLORS['bg_card'], fg=COLORS['primary']).grid(
            row=0, column=0, columnspan=2, sticky='w', pady=(0,16))
        ttk.Separator(card, orient='horizontal').grid(
            row=1, column=0, columnspan=2, sticky='ew', pady=(0,14))

        empresa = _get_empresa()
        campos = [
            ("Razón Social *",        "razon_social"),
            ("RUC / NIT *",           "ruc"),
            ("Teléfono",              "telefono"),
            ("Dirección",             "direccion"),
            ("Correo electrónico",    "correo"),
        ]
        self._emp_vars = {}
        for i, (lbl, key) in enumerate(campos):
            tk.Label(card, text=lbl,
                     font=(FONTS['family'], FONTS['body'], 'bold'),
                     bg=COLORS['bg_card'], fg='#374151').grid(
                row=i+2, column=0, sticky='w', pady=6, padx=(0,20))
            var = tk.StringVar(value=empresa.get(key,''))
            tk.Entry(card, textvariable=var,
                     font=(FONTS['family'], FONTS['body']),
                     width=40, relief='solid', bd=1).grid(
                row=i+2, column=1, sticky='w', pady=6)
            self._emp_vars[key] = var

        frm_btn = tk.Frame(card, bg=COLORS['bg_card'])
        frm_btn.grid(row=len(campos)+2, column=0, columnspan=2,
                     sticky='w', pady=(20,0))
        _btn(frm_btn, "💾  Guardar", self._save_empresa,
             bg=COLORS['success'], width=18).pack(side='left', padx=(0,10))

    def _save_empresa(self):
        data = {k: v.get().strip() for k,v in self._emp_vars.items()}
        if not data['razon_social'] or not data['ruc']:
            messagebox.showwarning("Atención",
                                   "Razón Social y RUC son obligatorios.")
            return
        _save_empresa(data)
        messagebox.showinfo("✅ Guardado",
                            "Datos de empresa guardados correctamente.")

    # ════════════════════════════════════════════════════
    #  TAB 2 — USUARIOS
    # ════════════════════════════════════════════════════
    def _tab_usuarios(self, nb):
        frm = tk.Frame(nb, bg=COLORS['bg_main'])
        nb.add(frm, text="  👥  Usuarios  ")

        # Toolbar
        tb = tk.Frame(frm, bg=COLORS['bg_card'], pady=10)
        tb.pack(fill='x', padx=0)
        _btn(tb, "➕  Nuevo",   self._new_usuario,
             bg=COLORS['success'],  width=14).pack(side='left', padx=(16,6))
        _btn(tb, "✏️  Editar",  self._edit_usuario,
             bg=COLORS['warning'],  width=14).pack(side='left', padx=6)
        _btn(tb, "🗑️  Eliminar", self._del_usuario,
             bg=COLORS['danger'],   width=14).pack(side='left', padx=6)
        _btn(tb, "🔄  Actualizar", lambda: self._load_usuarios(),
             bg=COLORS['primary'],  width=14).pack(side='left', padx=6)

        # Tabla
        cols = ("ID","Nombre","Usuario","Rol","Estado","Creado")
        self._tree_usr = ttk.Treeview(frm, columns=cols,
                                       show='headings', height=18)
        for col, w in zip(cols, [45,180,130,130,90,150]):
            self._tree_usr.heading(col, text=col)
            self._tree_usr.column(col, width=w, anchor='center')

        sb = ttk.Scrollbar(frm, orient='vertical',
                           command=self._tree_usr.yview)
        self._tree_usr.configure(yscrollcommand=sb.set)
        self._tree_usr.pack(side='left', fill='both',
                             expand=True, padx=(16,0), pady=12)
        sb.pack(side='left', fill='y', pady=12, padx=(0,8))

        self._load_usuarios()

    def _load_usuarios(self):
        for r in self._tree_usr.get_children():
            self._tree_usr.delete(r)
        for u in _get_usuarios():
            estado = "✅ Activo" if u[4] else "❌ Inactivo"
            self._tree_usr.insert('', 'end',
                values=(u[0], u[1], u[2], u[3], estado, u[5] or ''))

    def _sel_uid(self):
        sel = self._tree_usr.selection()
        if not sel:
            messagebox.showinfo("Seleccione",
                                "Seleccione un usuario de la lista.")
            return None
        return self._tree_usr.item(sel[0])['values'][0]

    def _new_usuario(self):   self._usuario_dialog()
    def _edit_usuario(self):
        uid = self._sel_uid()
        if uid: self._usuario_dialog(uid)

    def _del_usuario(self):
        uid = self._sel_uid()
        if not uid: return
        if uid == self.current_user.get('id'):
            messagebox.showerror("Error",
                                 "No puede eliminar su propio usuario.")
            return
        if messagebox.askyesno("Confirmar",
                               f"¿Eliminar usuario ID {uid}?"):
            _delete_usuario(uid)
            self._load_usuarios()

    def _usuario_dialog(self, uid=None):
        win = tk.Toplevel(self.parent)
        win.title("Nuevo Usuario" if not uid else "Editar Usuario")
        win.geometry("440x470")
        win.configure(bg=COLORS['bg_card'])
        win.grab_set()
        win.resizable(False, False)

        tk.Label(win,
                 text="👤  " + ("Nuevo Usuario" if not uid else "Editar Usuario"),
                 font=(FONTS['family'], FONTS['subtitle'], 'bold'),
                 bg=COLORS['bg_card'], fg=COLORS['primary']).pack(pady=(20,4))
        ttk.Separator(win).pack(fill='x', padx=20, pady=(0,10))

        frm = tk.Frame(win, bg=COLORS['bg_card'], padx=30)
        frm.pack()

        v_nom  = _lbl_entry(frm, "Nombre completo",    0)
        v_usr  = _lbl_entry(frm, "Usuario (login)",    1)
        v_pwd  = _lbl_entry(frm, "Contraseña",         2, show='●')
        v_pwd2 = _lbl_entry(frm, "Repetir contraseña", 3, show='●')

        tk.Label(frm, text="Rol", bg=COLORS['bg_card'],
                 font=(FONTS['family'], FONTS['body'])).grid(
            row=4, column=0, sticky='w', pady=5, padx=6)
        v_rol = tk.StringVar(value='Cajero')
        ttk.Combobox(frm, textvariable=v_rol, values=ROLES,
                     state='readonly', width=28).grid(
            row=4, column=1, pady=5, padx=6)

        v_activo = tk.IntVar(value=1)
        tk.Checkbutton(frm, text="Usuario activo",
                       variable=v_activo,
                       bg=COLORS['bg_card'],
                       font=(FONTS['family'], FONTS['body'])).grid(
            row=5, column=1, sticky='w', pady=5, padx=6)

        if uid:
            conn = sqlite3.connect(DB_FILE)
            row = conn.execute(
                "SELECT nombre,usuario,rol,activo FROM usuarios WHERE id=?",
                (uid,)).fetchone()
            conn.close()
            if row:
                v_nom.set(row[0]); v_usr.set(row[1])
                v_rol.set(row[2]); v_activo.set(row[3])
            tk.Label(frm, text="Dejar contraseña vacía para no cambiarla",
                     font=(FONTS['family'], FONTS['small']),
                     bg=COLORS['bg_card'],
                     fg=COLORS['text_secondary']).grid(
                row=6, column=1, sticky='w', padx=6, pady=(0,4))

        def _guardar():
            nombre  = v_nom.get().strip()
            usuario = v_usr.get().strip()
            pwd     = v_pwd.get().strip()
            pwd2    = v_pwd2.get().strip()
            if not nombre or not usuario:
                messagebox.showwarning("Atención",
                    "Nombre y usuario son obligatorios.", parent=win)
                return
            if not uid and not pwd:
                messagebox.showwarning("Atención",
                    "La contraseña es obligatoria.", parent=win)
                return
            if pwd and pwd != pwd2:
                messagebox.showwarning("Atención",
                    "Las contraseñas no coinciden.", parent=win)
                return
            _save_usuario({
                "nombre": nombre, "usuario": usuario,
                "password": pwd, "rol": v_rol.get(),
                "activo": v_activo.get()
            }, uid)
            messagebox.showinfo("✅", "Usuario guardado.", parent=win)
            win.destroy()
            self._load_usuarios()

        fb = tk.Frame(win, bg=COLORS['bg_card'])
        fb.pack(pady=14)
        _btn(fb, "💾  Guardar",  _guardar,   bg=COLORS['success'], width=14).pack(side='left', padx=8)
        _btn(fb, "✖  Cancelar", win.destroy, bg=COLORS['danger'],  width=14).pack(side='left', padx=8)

    # ════════════════════════════════════════════════════
    #  TAB 3 — IMPRESORAS
    # ════════════════════════════════════════════════════
    def _tab_impresoras(self, nb):
        frm = tk.Frame(nb, bg=COLORS['bg_main'])
        nb.add(frm, text="  🖨️  Impresoras  ")

        tb = tk.Frame(frm, bg=COLORS['bg_card'], pady=10)
        tb.pack(fill='x')
        _btn(tb, "➕  Agregar",   self._new_impresora,
             bg=COLORS['success'], width=14).pack(side='left', padx=(16,6))
        _btn(tb, "✏️  Editar",    self._edit_impresora,
             bg=COLORS['warning'], width=14).pack(side='left', padx=6)
        _btn(tb, "🗑️  Eliminar",   self._del_impresora,
             bg=COLORS['danger'],  width=14).pack(side='left', padx=6)
        _btn(tb, "🔄  Actualizar", lambda: self._load_impresoras(),
             bg=COLORS['primary'], width=14).pack(side='left', padx=6)

        cols = ("ID","Nombre","Tipo","Puerto","Predeterminada","Ancho papel")
        self._tree_imp = ttk.Treeview(frm, columns=cols,
                                       show='headings', height=18)
        for col, w in zip(cols, [45,200,120,130,120,110]):
            self._tree_imp.heading(col, text=col)
            self._tree_imp.column(col, width=w, anchor='center')

        sb = ttk.Scrollbar(frm, orient='vertical',
                           command=self._tree_imp.yview)
        self._tree_imp.configure(yscrollcommand=sb.set)
        self._tree_imp.pack(side='left', fill='both',
                             expand=True, padx=(16,0), pady=12)
        sb.pack(side='left', fill='y', pady=12, padx=(0,8))

        self._load_impresoras()

    def _load_impresoras(self):
        for r in self._tree_imp.get_children():
            self._tree_imp.delete(r)
        for p in _get_impresoras():
            pred = "⭐ Sí" if p[4] else "No"
            self._tree_imp.insert('', 'end',
                values=(p[0], p[1], p[2], p[3], pred, f"{p[5]} mm"))

    def _sel_iid(self):
        sel = self._tree_imp.selection()
        if not sel:
            messagebox.showinfo("Seleccione", "Seleccione una impresora.")
            return None
        return self._tree_imp.item(sel[0])['values'][0]

    def _new_impresora(self):  self._impresora_dialog()
    def _edit_impresora(self):
        iid = self._sel_iid()
        if iid: self._impresora_dialog(iid)

    def _del_impresora(self):
        iid = self._sel_iid()
        if iid and messagebox.askyesno("Confirmar",
                                        f"¿Eliminar impresora ID {iid}?"):
            _delete_impresora(iid)
            self._load_impresoras()

    def _impresora_dialog(self, iid=None):
        win = tk.Toplevel(self.parent)
        win.title("Agregar Impresora" if not iid else "Editar Impresora")
        win.geometry("430x380")
        win.configure(bg=COLORS['bg_card'])
        win.grab_set()
        win.resizable(False, False)

        tk.Label(win,
                 text="🖨️  " + ("Agregar Impresora" if not iid else "Editar Impresora"),
                 font=(FONTS['family'], FONTS['subtitle'], 'bold'),
                 bg=COLORS['bg_card'], fg=COLORS['primary']).pack(pady=(20,4))
        ttk.Separator(win).pack(fill='x', padx=20, pady=(0,10))

        frm = tk.Frame(win, bg=COLORS['bg_card'], padx=30)
        frm.pack()

        v_nombre = _lbl_entry(frm, "Nombre",      0)
        v_puerto = _lbl_entry(frm, "Puerto / IP", 1)

        tk.Label(frm, text="Tipo", bg=COLORS['bg_card'],
                 font=(FONTS['family'], FONTS['body'])).grid(
            row=2, column=0, sticky='w', pady=5, padx=6)
        v_tipo = tk.StringVar(value='Térmica')
        ttk.Combobox(frm, textvariable=v_tipo,
                     values=["Térmica","Laser","Inkjet","Matricial"],
                     state='readonly', width=28).grid(
            row=2, column=1, pady=5, padx=6)

        tk.Label(frm, text="Ancho papel (mm)", bg=COLORS['bg_card'],
                 font=(FONTS['family'], FONTS['body'])).grid(
            row=3, column=0, sticky='w', pady=5, padx=6)
        v_ancho = tk.StringVar(value='80')
        ttk.Combobox(frm, textvariable=v_ancho,
                     values=["58","80","110","210"],
                     width=28).grid(row=3, column=1, pady=5, padx=6)

        v_pred = tk.IntVar(value=0)
        tk.Checkbutton(frm, text="Establecer como predeterminada",
                       variable=v_pred, bg=COLORS['bg_card'],
                       font=(FONTS['family'], FONTS['body'])).grid(
            row=4, column=1, sticky='w', pady=5, padx=6)

        if iid:
            conn = sqlite3.connect(DB_FILE)
            row = conn.execute(
                "SELECT nombre,tipo,puerto,predeterminada,ancho_papel FROM impresoras WHERE id=?",
                (iid,)).fetchone()
            conn.close()
            if row:
                v_nombre.set(row[0]); v_tipo.set(row[1])
                v_puerto.set(row[2]); v_pred.set(row[3])
                v_ancho.set(str(row[4]))

        def _guardar():
            nombre = v_nombre.get().strip()
            if not nombre:
                messagebox.showwarning("Atención",
                    "El nombre es obligatorio.", parent=win)
                return
            try: ancho = int(v_ancho.get())
            except: ancho = 80
            _save_impresora({
                "nombre": nombre, "tipo": v_tipo.get(),
                "puerto": v_puerto.get().strip(),
                "predeterminada": v_pred.get(),
                "ancho_papel": ancho
            }, iid)
            messagebox.showinfo("✅", "Impresora guardada.", parent=win)
            win.destroy()
            self._load_impresoras()

        fb = tk.Frame(win, bg=COLORS['bg_card'])
        fb.pack(pady=14)
        _btn(fb, "💾  Guardar",  _guardar,   bg=COLORS['success'], width=14).pack(side='left', padx=8)
        _btn(fb, "✖  Cancelar", win.destroy, bg=COLORS['danger'],  width=14).pack(side='left', padx=8)