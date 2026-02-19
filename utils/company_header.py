"""
utils/company_header.py
Utilidades para mostrar el header de empresa en:
  - Cabecera principal del POS
  - Tickets de venta (texto plano para impresora térmica)
  - Facturas (estructura de datos para PDF/reporte)
"""

import os
import sqlite3
from pathlib import Path

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

import tkinter as tk
from tkinter import ttk

try:
    from config.settings import COLORS, FONTS, SPACING
except ImportError:
    COLORS  = {'primary': '#2563eb', 'bg_card': '#ffffff', 'bg_main': '#f1f5f9',
               'bg_sidebar': '#1e293b', 'text_white': '#ffffff',
               'text_secondary': '#64748b'}
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

FOOTER_INFO = {
    "empresa":  "Venialgo Sistemas",
    "email":    "davenialgo@proton.me",
    "whatsapp": "+595 994-686 493",
    "web":      "www.venialgosistemas.com",
}


# ════════════════════════════════════════════════════════════
#  DATOS
# ════════════════════════════════════════════════════════════

def get_company() -> dict:
    """Carga datos de empresa desde la BD. Cacheable."""
    try:
        conn = sqlite3.connect(DB_FILE)
        c    = conn.cursor()
        c.execute("""
            SELECT razon_social, ruc, telefono, direccion, correo, logo_path
            FROM empresa WHERE id=1
        """)
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


def _load_logo_image(max_w: int, max_h: int):
    """Retorna PhotoImage del logo o None."""
    if not PIL_AVAILABLE:
        return None
    co = get_company()
    path = co.get("logo_path","")
    if not path or not os.path.exists(path):
        return None
    try:
        img = Image.open(path).convert("RGBA")
        img.thumbnail((max_w, max_h), Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


# ════════════════════════════════════════════════════════════
#  WIDGET — Header Tkinter
# ════════════════════════════════════════════════════════════

class CompanyHeaderWidget(tk.Frame):
    """
    Widget reutilizable que muestra logo + datos de empresa.
    Úsalo así en el header principal:

        hdr = CompanyHeaderWidget(parent, height=64)
        hdr.pack(fill='x')
    """

    def __init__(self, parent, height: int = 64, bg: str = None, **kwargs):
        bg = bg or COLORS['bg_card']
        super().__init__(parent, bg=bg, height=height, **kwargs)
        self.pack_propagate(False)
        self._bg = bg
        self._build()

    def _build(self):
        co = get_company()

        # ── Logo (izquierda) ──────────────────────────────────
        logo_img = _load_logo_image(120, 54)
        if logo_img:
            lbl_logo = tk.Label(self, image=logo_img, bg=self._bg)
            lbl_logo.image = logo_img   # evitar GC
            lbl_logo.pack(side='left', padx=(14, 8), pady=4)
        else:
            # Placeholder con inicial de la empresa
            inicial = (co.get("razon_social") or "?")[0].upper()
            tk.Label(self, text=inicial,
                     font=(FONTS['family'], 26, 'bold'),
                     bg=COLORS['primary'], fg='white',
                     width=3, height=1).pack(side='left', padx=(14,8), pady=8)

        # Separador vertical
        ttk.Separator(self, orient='vertical').pack(side='left', fill='y', pady=10)

        # ── Datos texto (centro) ──────────────────────────────
        frm_txt = tk.Frame(self, bg=self._bg)
        frm_txt.pack(side='left', padx=12, fill='y', expand=True)

        nombre = co.get("razon_social") or "Sistema POS"
        tk.Label(frm_txt, text=nombre,
                 font=(FONTS['family'], FONTS['title'], 'bold'),
                 bg=self._bg, fg=COLORS['primary'],
                 anchor='w').pack(fill='x')

        sub_parts = []
        if co.get("ruc"):      sub_parts.append(f"RUC: {co['ruc']}")
        if co.get("telefono"): sub_parts.append(f"📞 {co['telefono']}")
        if co.get("correo"):   sub_parts.append(f"✉️ {co['correo']}")

        if sub_parts:
            tk.Label(frm_txt, text="   |   ".join(sub_parts),
                     font=(FONTS['family'], FONTS['small']),
                     bg=self._bg, fg=COLORS['text_secondary'],
                     anchor='w').pack(fill='x')

        if co.get("direccion"):
            tk.Label(frm_txt, text=f"📍 {co['direccion']}",
                     font=(FONTS['family'], FONTS['small']),
                     bg=self._bg, fg=COLORS['text_secondary'],
                     anchor='w').pack(fill='x')

    def refresh(self):
        """Recarga los datos (útil tras guardar cambios en empresa)."""
        for w in self.winfo_children():
            w.destroy()
        self._build()


# ════════════════════════════════════════════════════════════
#  TICKET DE VENTA — Texto plano para impresora térmica
# ════════════════════════════════════════════════════════════

def build_ticket_header(ancho: int = 42) -> str:
    """
    Genera el encabezado del ticket en texto plano.
    ancho: caracteres por línea (42 = 58mm, 48 = 80mm)

    Retorna string con saltos de línea.
    """
    co    = get_company()
    sep   = "─" * ancho
    lines = []

    def centrar(texto: str) -> str:
        return texto.center(ancho)

    def wrap(texto: str, max_len: int) -> list:
        """Parte texto largo en líneas de max_len caracteres."""
        words  = texto.split()
        line   = ""
        result = []
        for w in words:
            if len(line) + len(w) + 1 <= max_len:
                line += ("" if not line else " ") + w
            else:
                if line: result.append(line)
                line = w
        if line: result.append(line)
        return result or [""]

    lines.append(sep)

    # Nombre empresa
    nombre = co.get("razon_social") or "Mi Empresa"
    for ln in wrap(nombre.upper(), ancho):
        lines.append(centrar(ln))

    # RUC
    if co.get("ruc"):
        lines.append(centrar(f"RUC: {co['ruc']}"))

    # Teléfono
    if co.get("telefono"):
        lines.append(centrar(f"Tel: {co['telefono']}"))

    # Correo
    if co.get("correo"):
        lines.append(centrar(co['correo']))

    # Dirección
    if co.get("direccion"):
        for ln in wrap(co['direccion'], ancho):
            lines.append(centrar(ln))

    lines.append(sep)
    return "\n".join(lines)


def build_ticket_footer(ancho: int = 42) -> str:
    """
    Genera el pie del ticket con agradecimiento y datos de Venialgo.
    """
    sep   = "─" * ancho
    lines = [
        sep,
        "¡Gracias por su compra!".center(ancho),
        sep,
        f"Sistema: {FOOTER_INFO['empresa']}".center(ancho),
        FOOTER_INFO['whatsapp'].center(ancho),
        sep,
        "",
        "",   # espacio para cortar papel
    ]
    return "\n".join(lines)


def build_full_ticket(items: list, totales: dict,
                      cajero: str = "",
                      numero: str = "",
                      ancho: int = 42) -> str:
    """
    Genera un ticket completo en texto plano.

    items = [{"desc": str, "qty": float, "precio": float, "subtotal": float}]
    totales = {"subtotal": float, "descuento": float, "iva": float, "total": float}
    cajero = nombre del cajero
    numero = número de ticket
    """
    from datetime import datetime
    sep  = "─" * ancho
    sep2 = "═" * ancho
    lines = []

    lines.append(build_ticket_header(ancho))

    # Número y fecha
    now = datetime.now()
    if numero:
        lines.append(f"  Ticket N°: {numero}")
    lines.append(f"  Fecha:     {now.strftime('%d/%m/%Y')}")
    lines.append(f"  Hora:      {now.strftime('%H:%M:%S')}")
    if cajero:
        lines.append(f"  Cajero:    {cajero}")
    lines.append(sep)

    # Columnas
    col_desc  = ancho - 18
    lines.append(f"  {'Descripción':<{col_desc}}{'Cant':>4}  {'Total':>8}")
    lines.append(sep)

    # Items
    for item in items:
        desc     = str(item.get("desc",""))[:col_desc]
        qty      = item.get("qty", 1)
        subtotal = item.get("subtotal", 0)
        lines.append(f"  {desc:<{col_desc}}{qty:>4.0f}  {subtotal:>8,.0f}")
        if item.get("precio"):
            precio = item["precio"]
            lines.append(f"  {'@':>{col_desc}} {precio:,.0f} c/u")

    lines.append(sep)

    # Totales
    sub  = totales.get("subtotal", 0)
    desc = totales.get("descuento", 0)
    iva  = totales.get("iva", 0)
    tot  = totales.get("total", 0)

    if sub != tot:
        lines.append(f"  {'Subtotal':>{ancho-12}} {sub:>9,.0f}")
    if desc > 0:
        lines.append(f"  {'Descuento':>{ancho-12}} {desc:>9,.0f}")
    if iva > 0:
        lines.append(f"  {'IVA (10%)':>{ancho-12}} {iva:>9,.0f}")

    lines.append(sep2)
    lines.append(f"  {'TOTAL':>{ancho-12}} {tot:>9,.0f}")
    lines.append(sep2)

    lines.append(build_ticket_footer(ancho))
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════
#  FACTURA — Datos estructurados para PDF/reporte
# ════════════════════════════════════════════════════════════

def get_invoice_header_data(numero: str = "", cliente: dict = None) -> dict:
    """
    Retorna un dict con todos los datos necesarios para
    construir un encabezado de factura en cualquier formato (PDF, DOCX, etc.)

    Uso:
        data = get_invoice_header_data("F-0001", cliente)
        # Usar data["empresa"], data["cliente"], data["numero"], etc.
    """
    from datetime import datetime
    co = get_company()
    return {
        "empresa": {
            "nombre":    co.get("razon_social",""),
            "ruc":       co.get("ruc",""),
            "telefono":  co.get("telefono",""),
            "correo":    co.get("correo",""),
            "direccion": co.get("direccion",""),
            "logo_path": co.get("logo_path",""),
        },
        "factura": {
            "numero":    numero,
            "fecha":     datetime.now().strftime("%d/%m/%Y"),
            "hora":      datetime.now().strftime("%H:%M"),
        },
        "cliente": cliente or {},
        "pie": {
            "soporte":   f"{FOOTER_INFO['empresa']} — {FOOTER_INFO['whatsapp']}",
        }
    }


# ════════════════════════════════════════════════════════════
#  FOOTER BAR TKINTER (reutilizable en toda la app)
# ════════════════════════════════════════════════════════════

def add_footer(window, bg: str = "#1e293b") -> tk.Frame:
    """Barra footer con datos de Venialgo Sistemas."""
    bar = tk.Frame(window, bg=bg, height=26)
    bar.pack(side='bottom', fill='x')
    bar.pack_propagate(False)
    txt = (
        f"  ★ {FOOTER_INFO['empresa']}  │  "
        f"✉ {FOOTER_INFO['email']}  │  "
        f"📱 {FOOTER_INFO['whatsapp']}  │  "
        f"🌐 {FOOTER_INFO['web']}  "
    )
    tk.Label(bar, text=txt, bg=bg, fg='#94a3b8',
             font=(FONTS['family'], FONTS['small'])).pack(side='left')
    return bar
