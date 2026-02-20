# -*- coding: utf-8 -*-
"""
pricing_system.py
Sistema de precios por modalidad de pago
Venialgo Sistemas POS

Logica:
  Contado  = costo * (1 + porcentaje_contado/100)
  Credito  = costo * (1 + porcentaje_cuota_N/100)

Tabla configuracion_precios:
  id, nombre, tipo (contado/credito), cuotas, porcentaje, activo
"""

import os, sys, sqlite3, tkinter as tk
from tkinter import ttk, messagebox

# ── Colores y fuentes ─────────────────────────────────────────
try:
    from config.settings import COLORS, FONTS, SPACING
except ImportError:
    COLORS  = {'primary':'#2563eb','bg_main':'#f1f5f9','bg_card':'#ffffff',
                'bg_sidebar':'#1e293b','text_white':'#ffffff','text_secondary':'#64748b',
                'success':'#16a34a','danger':'#dc2626','warning':'#d97706','border':'#e2e8f0'}
    FONTS   = {'family':'Segoe UI','title':16,'subtitle':13,'body':10,'small':9}
    SPACING = {'xs':4,'sm':8,'md':12,'lg':16,'xl':24}

def _get_db():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.path.expanduser("~")
    d = os.path.join(base, "VenialgoPOS")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "pos_database.db")

DB_FILE = _get_db()

# ════════════════════════════════════════════════════════════
#  DB HELPERS
# ════════════════════════════════════════════════════════════

def ensure_pricing_tables():
    """Crea tablas de precios si no existen."""
    conn = sqlite3.connect(DB_FILE, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS config_precios (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre     TEXT NOT NULL,
            tipo       TEXT NOT NULL,   -- 'contado' o 'credito'
            cuotas     INTEGER DEFAULT 1,
            porcentaje REAL DEFAULT 0,
            activo     INTEGER DEFAULT 1
        )
    """)

    # Insertar configuracion por defecto si la tabla esta vacia
    c.execute("SELECT COUNT(*) FROM config_precios")
    if c.fetchone()[0] == 0:
        defaults = [
            ("Contado",      "contado", 1,  30.0),
            ("Credito 3c",   "credito", 3,  45.0),
            ("Credito 6c",   "credito", 6,  60.0),
            ("Credito 12c",  "credito", 12, 80.0),
            ("Credito 18c",  "credito", 18, 100.0),
            ("Credito 24c",  "credito", 24, 120.0),
        ]
        for nombre, tipo, cuotas, pct in defaults:
            c.execute("""INSERT INTO config_precios (nombre,tipo,cuotas,porcentaje,activo)
                         VALUES (?,?,?,?,1)""", (nombre, tipo, cuotas, pct))

    # Agregar columna costo a productos si no existe
    try:
        c.execute("ALTER TABLE productos ADD COLUMN costo REAL DEFAULT 0")
    except Exception:
        pass

    conn.commit()
    conn.close()


def get_all_pricing():
    """Retorna lista de todas las configuraciones de precio."""
    conn = sqlite3.connect(DB_FILE, timeout=10)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM config_precios WHERE activo=1 ORDER BY tipo,cuotas"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_pricing_all():
    """Retorna todas (incluyendo inactivas) para administración."""
    conn = sqlite3.connect(DB_FILE, timeout=10)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM config_precios ORDER BY tipo,cuotas"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_pricing(data, pid=None):
    conn = sqlite3.connect(DB_FILE, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    if pid:
        conn.execute("""UPDATE config_precios
            SET nombre=?,tipo=?,cuotas=?,porcentaje=?,activo=? WHERE id=?""",
            (data['nombre'], data['tipo'], data['cuotas'],
             data['porcentaje'], data.get('activo',1), pid))
    else:
        conn.execute("""INSERT INTO config_precios (nombre,tipo,cuotas,porcentaje,activo)
            VALUES (?,?,?,?,?)""",
            (data['nombre'], data['tipo'], data['cuotas'],
             data['porcentaje'], data.get('activo',1)))
    conn.commit()
    conn.close()


def delete_pricing(pid):
    conn = sqlite3.connect(DB_FILE, timeout=10)
    conn.execute("UPDATE config_precios SET activo=0 WHERE id=?", (pid,))
    conn.commit()
    conn.close()


def calcular_precio(costo: float, config_id: int) -> float:
    """Calcula el precio de venta dado el costo y la config de precio."""
    conn = sqlite3.connect(DB_FILE, timeout=10)
    row = conn.execute(
        "SELECT porcentaje FROM config_precios WHERE id=?", (config_id,)
    ).fetchone()
    conn.close()
    if not row:
        return costo
    return round(costo * (1 + row[0] / 100), 0)


def calcular_todos_precios(costo: float) -> list:
    """Retorna lista de precios calculados para todas las modalidades activas."""
    configs = get_all_pricing()
    result  = []
    for c in configs:
        precio = round(costo * (1 + c['porcentaje'] / 100), 0)
        result.append({
            "id":         c['id'],
            "nombre":     c['nombre'],
            "tipo":       c['tipo'],
            "cuotas":     c['cuotas'],
            "porcentaje": c['porcentaje'],
            "precio":     precio,
            "cuota_monto": round(precio / c['cuotas'], 0) if c['cuotas'] > 1 else 0,
        })
    return result


# ════════════════════════════════════════════════════════════
#  WIDGET: TABLA DE PRECIOS (para mostrar en punto de venta)
# ════════════════════════════════════════════════════════════

class PreciosWidget(tk.Frame):
    """
    Muestra tabla de precios calculados a partir del costo.
    Se puede embeber en cualquier ventana.
    """

    def __init__(self, parent, costo=0, **kw):
        super().__init__(parent, bg=COLORS['bg_card'], **kw)
        self.costo = costo
        self._build()
        if costo:
            self.update_precios(costo)

    def _build(self):
        tk.Label(self, text="Precios de Venta",
                 font=(FONTS['family'], FONTS['body'], 'bold'),
                 bg=COLORS['bg_card'], fg=COLORS['primary']).pack(anchor='w', pady=(0,4))

        cols = ("Modalidad", "% Ganancia", "Precio Venta", "Cuota")
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=7)
        widths    = [130, 90, 110, 100]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor='center')

        # Colores por tipo
        self.tree.tag_configure('contado', background='#f0fdf4', foreground='#166534')
        self.tree.tag_configure('credito', background='#eff6ff', foreground='#1e40af')

        sb = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side='left', fill='both', expand=True)
        sb.pack(side='left', fill='y')

    def update_precios(self, costo: float):
        """Actualiza la tabla con nuevos precios calculados."""
        self.costo = costo
        for row in self.tree.get_children():
            self.tree.delete(row)
        if not costo:
            return
        for p in calcular_todos_precios(costo):
            cuota_txt = f"Gs. {p['cuota_monto']:,.0f}" if p['cuota_monto'] else "—"
            tag = 'contado' if p['tipo'] == 'contado' else 'credito'
            self.tree.insert('', 'end', values=(
                p['nombre'],
                f"{p['porcentaje']:.0f}%",
                f"Gs. {p['precio']:,.0f}",
                cuota_txt,
            ), tags=(tag,))


# ════════════════════════════════════════════════════════════
#  VENTANA: CALCULADORA DE PRECIOS (popup rápido)
# ════════════════════════════════════════════════════════════

class CalculadoraPrecios(tk.Toplevel):
    """
    Popup que muestra todos los precios para un producto dado su costo.
    Uso: CalculadoraPrecios(parent, nombre_producto, costo)
    """

    def __init__(self, parent, nombre="Producto", costo=0):
        super().__init__(parent)
        self.title(f"Precios — {nombre}")
        self.geometry("520x420")
        self.configure(bg=COLORS['bg_card'])
        self.resizable(False, False)
        self.grab_set()

        # Centrar
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 520) // 2
        y = (self.winfo_screenheight() - 420) // 2
        self.geometry(f"520x420+{x}+{y}")

        self._build(nombre, costo)

    def _build(self, nombre, costo):
        # Header
        hdr = tk.Frame(self, bg=COLORS['bg_sidebar'], pady=12)
        hdr.pack(fill='x')
        tk.Label(hdr, text=f"Precios: {nombre}",
                 font=(FONTS['family'], 13, 'bold'),
                 bg=COLORS['bg_sidebar'], fg='white').pack()
        tk.Label(hdr, text=f"Costo: Gs. {costo:,.0f}",
                 font=(FONTS['family'], FONTS['small']),
                 bg=COLORS['bg_sidebar'], fg='#94a3b8').pack()

        # Widget de precios
        frm = tk.Frame(self, bg=COLORS['bg_card'], padx=16, pady=12)
        frm.pack(fill='both', expand=True)
        pw = PreciosWidget(frm, costo=costo)
        pw.pack(fill='both', expand=True)

        # Boton cerrar
        tk.Button(self, text="Cerrar",
                  command=self.destroy,
                  bg=COLORS['primary'], fg='white',
                  font=(FONTS['family'], FONTS['body'], 'bold'),
                  relief='flat', pady=8, cursor='hand2').pack(
            fill='x', padx=16, pady=(0,12))


# ════════════════════════════════════════════════════════════
#  PANEL: ADMINISTRACIÓN DE CONFIGURACION DE PRECIOS
# ════════════════════════════════════════════════════════════

class PanelConfigPrecios(tk.Frame):
    """
    Panel para administrar las modalidades de precio.
    Se puede embeber en el módulo de Administración.
    """

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=COLORS['bg_main'], **kw)
        ensure_pricing_tables()
        self._build()

    def _build(self):
        # Toolbar
        tb = tk.Frame(self, bg=COLORS['bg_card'], pady=10)
        tb.pack(fill='x')
        tk.Label(tb, text="Configuracion de Precios y Porcentajes",
                 font=(FONTS['family'], FONTS['subtitle'], 'bold'),
                 bg=COLORS['bg_card'], fg=COLORS['primary']).pack(side='left', padx=16)

        for txt, cmd, bg in [
            ("+ Nueva", self._new, COLORS['success']),
            ("Editar",  self._edit, COLORS['warning']),
            ("Eliminar",self._delete, COLORS['danger']),
        ]:
            tk.Button(tb, text=txt, command=cmd, bg=bg, fg='white',
                      font=(FONTS['family'], FONTS['small'], 'bold'),
                      relief='flat', padx=10, pady=6, cursor='hand2').pack(
                side='right', padx=4)

        # Info
        info = tk.Frame(self, bg='#eff6ff', pady=8)
        info.pack(fill='x', padx=16, pady=(8,0))
        tk.Label(info,
                 text="Los precios se calculan automaticamente: Precio = Costo x (1 + %/100)\n"
                      "Ejemplo: Costo Gs.100.000 con 30% = Precio Gs.130.000",
                 font=(FONTS['family'], FONTS['small']),
                 bg='#eff6ff', fg='#1e40af', justify='left').pack(anchor='w', padx=12)

        # Tabla
        cols = ("ID","Nombre","Tipo","Cuotas","% Ganancia","Activo")
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=14)
        for col, w in zip(cols, [40,160,90,70,100,70]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor='center')

        self.tree.tag_configure('contado', background='#f0fdf4')
        self.tree.tag_configure('credito', background='#eff6ff')

        sb = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side='left', fill='both', expand=True, padx=(16,0), pady=12)
        sb.pack(side='left', fill='y', pady=12, padx=(0,8))

        self._load()

    def _load(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        for p in get_all_pricing_all():
            tag = 'contado' if p['tipo']=='contado' else 'credito'
            self.tree.insert('', 'end', values=(
                p['id'], p['nombre'], p['tipo'].capitalize(),
                p['cuotas'], f"{p['porcentaje']:.1f}%",
                "Si" if p['activo'] else "No"
            ), tags=(tag,))

    def _sel_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Seleccione", "Seleccione una fila.")
            return None
        return self.tree.item(sel[0])['values'][0]

    def _new(self):   self._dialog()
    def _edit(self):
        pid = self._sel_id()
        if pid: self._dialog(pid)

    def _delete(self):
        pid = self._sel_id()
        if pid and messagebox.askyesno("Confirmar", f"Eliminar configuracion ID {pid}?"):
            delete_pricing(pid)
            self._load()

    def _dialog(self, pid=None):
        win = tk.Toplevel(self)
        win.title("Nueva Modalidad" if not pid else "Editar Modalidad")
        win.geometry("400x360")
        win.configure(bg=COLORS['bg_card'])
        win.grab_set()
        win.resizable(False, False)

        tk.Label(win,
                 text="Nueva Modalidad de Precio" if not pid else "Editar Modalidad",
                 font=(FONTS['family'], FONTS['subtitle'], 'bold'),
                 bg=COLORS['bg_card'], fg=COLORS['primary']).pack(pady=(20,4))
        ttk.Separator(win).pack(fill='x', padx=20, pady=(0,12))

        frm = tk.Frame(win, bg=COLORS['bg_card'], padx=30)
        frm.pack()

        def lbl_entry(label, row, width=28):
            tk.Label(frm, text=label, bg=COLORS['bg_card'],
                     font=(FONTS['family'], FONTS['body'])).grid(
                row=row, column=0, sticky='w', pady=6, padx=(0,16))
            var = tk.StringVar()
            tk.Entry(frm, textvariable=var, width=width,
                     relief='solid', bd=1,
                     font=(FONTS['family'], FONTS['body'])).grid(
                row=row, column=1, pady=6)
            return var

        v_nombre = lbl_entry("Nombre",     0)
        v_pct    = lbl_entry("% Ganancia", 2)
        v_cuotas = lbl_entry("Cuotas",     3)

        tk.Label(frm, text="Tipo", bg=COLORS['bg_card'],
                 font=(FONTS['family'], FONTS['body'])).grid(
            row=1, column=0, sticky='w', pady=6, padx=(0,16))
        v_tipo = tk.StringVar(value='contado')
        ttk.Combobox(frm, textvariable=v_tipo, values=["contado","credito"],
                     state='readonly', width=26).grid(row=1, column=1, pady=6)

        v_activo = tk.IntVar(value=1)
        tk.Checkbutton(frm, text="Activo", variable=v_activo,
                       bg=COLORS['bg_card'],
                       font=(FONTS['family'], FONTS['body'])).grid(
            row=4, column=1, sticky='w')

        if pid:
            conn = sqlite3.connect(DB_FILE)
            row  = conn.execute(
                "SELECT nombre,tipo,cuotas,porcentaje,activo FROM config_precios WHERE id=?",
                (pid,)).fetchone()
            conn.close()
            if row:
                v_nombre.set(row[0]); v_tipo.set(row[1])
                v_cuotas.set(str(row[2])); v_pct.set(str(row[3]))
                v_activo.set(row[4])

        def _guardar():
            nombre = v_nombre.get().strip()
            if not nombre:
                messagebox.showwarning("Error","Ingrese un nombre.", parent=win)
                return
            try:
                pct    = float(v_pct.get().replace(',','.'))
                cuotas = int(v_cuotas.get() or "1")
            except ValueError:
                messagebox.showwarning("Error",
                    "Porcentaje y cuotas deben ser numeros.", parent=win)
                return
            save_pricing({
                "nombre":     nombre,
                "tipo":       v_tipo.get(),
                "cuotas":     cuotas,
                "porcentaje": pct,
                "activo":     v_activo.get(),
            }, pid)
            win.destroy()
            self._load()

        fb = tk.Frame(win, bg=COLORS['bg_card'])
        fb.pack(pady=14)
        tk.Button(fb, text="Guardar", command=_guardar,
                  bg=COLORS['success'], fg='white',
                  font=(FONTS['family'], FONTS['body'], 'bold'),
                  relief='flat', padx=14, pady=8, cursor='hand2',
                  width=12).pack(side='left', padx=8)
        tk.Button(fb, text="Cancelar", command=win.destroy,
                  bg=COLORS['danger'], fg='white',
                  font=(FONTS['family'], FONTS['body'], 'bold'),
                  relief='flat', padx=14, pady=8, cursor='hand2',
                  width=12).pack(side='left', padx=8)
