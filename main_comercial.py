# -*- coding: utf-8 -*-
"""
main_comercial.py — Venialgo Sistemas POS v1.1
Dashboard moderno con sidebar oscuro + contenido claro
Inspirado en Stripe / Linear / SaaS 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os, sys
from datetime import datetime
import hashlib
from utils.fecha_es import fecha_corta, fecha_larga

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from database.db_manager import DatabaseManager
from license.license_manager import is_licensed
from backup.backup_manager import backup_service
from modules.admin.admin_ui import _ensure_tables
from modules.admin.license_ui import eula_accepted, EULAWindow, ActivationWindow
from modules.admin.login_window import LoginWindow
from modules.admin.first_run_wizard import is_first_run, FirstRunWizard

# Hash SHA-256 de la contraseña por defecto 'admin123'
DEFAULT_ADMIN_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"
from utils.company_header import get_company

APP_VERSION = "1.1"
_ensure_tables()

# ══════════════════════════════════════════════════════════════
#  PALETA DE COLORES
# ══════════════════════════════════════════════════════════════
# Inspiración: sidebar azul marino profundo + contenido gris muy claro
# Acento: azul eléctrico para highlights y activos
# Enfoque: contraste limpio, sin bordes gruesos, espaciado generoso

THEME = {
    # Sidebar
    "sb_bg":        "#0D1B4B",   # Azul marino profundo (igual que login)
    "sb_bg_mid":    "#1A3A8F",   # Azul medio (extremo inferior del gradiente)
    "sb_hover":     "#1F2937",   # gray-800
    "sb_active":    "#1D4ED8",   # blue-700 — estado activo
    "sb_active_bg": "#1E3A8A",   # blue-900 bg para activo
    "sb_text":      "#9CA3AF",   # gray-400
    "sb_text_act":  "#FFFFFF",
    "sb_logo_bg":   "#1D4ED8",   # azul logo

    # Topbar
    "tb_bg":        "#FFFFFF",
    "tb_border":    "#E5E7EB",   # gray-200
    "tb_text":      "#111827",
    "tb_sub":       "#6B7280",   # gray-500

    # Contenido
    "ct_bg":        "#F9FAFB",   # gray-50
    "card_bg":      "#FFFFFF",
    "card_border":  "#E5E7EB",

    # Acentos por módulo
    "acc_blue":     "#2563EB",
    "acc_green":    "#059669",
    "acc_amber":    "#D97706",
    "acc_rose":     "#E11D48",
    "acc_purple":   "#7C3AED",
    "acc_cyan":     "#0891B2",

    # Texto
    "txt_primary":  "#111827",
    "txt_secondary":"#6B7280",
    "txt_muted":    "#9CA3AF",
    "txt_white":    "#FFFFFF",

    # Botones
    "btn_primary":  "#2563EB",
    "btn_danger":   "#DC2626",
    "btn_logout":   "#7F1D1D",
}

FONT     = "Segoe UI"
FONT_MONO= "Consolas"


# ══════════════════════════════════════════════════════════════
#  WIDGETS REUTILIZABLES
# ══════════════════════════════════════════════════════════════

def make_card(parent, padx=20, pady=16, **kw):
    """Frame tipo card con fondo blanco y borde suave."""
    outer = RoundedCard(parent, padx=padx, pady=pady)
    return outer, outer.body


def stat_card(parent, title, value, accent, icon=""):
    """Card de estadística con ícono, título y valor."""
    outer = RoundedCard(parent, padx=20, pady=18)
    inner = outer.body

    # Ícono + título en la misma fila
    top = tk.Frame(inner, bg=THEME["card_bg"])
    top.pack(fill='x')
    tk.Label(top, text=icon, font=(FONT, 14),
             bg=THEME["card_bg"], fg=accent).pack(side='left')
    tk.Label(top, text=f"  {title}",
             font=(FONT, 9),
             bg=THEME["card_bg"], fg=THEME["txt_secondary"]).pack(side='left')

    # Valor destacado
    tk.Label(inner, text=value,
             font=(FONT, 22, 'bold'),
             bg=THEME["card_bg"], fg=THEME["txt_primary"]).pack(anchor='w', pady=(8, 0))

    # Barra de color inferior
    tk.Frame(inner, bg=accent, height=3).pack(fill='x', pady=(12, 0))

    return outer


class SidebarButton(tk.Frame):
    """Botón de navegación del sidebar con hover y estado activo."""

    def __init__(self, parent, text, icon, command, active=False, **kw):
        super().__init__(parent, bg=THEME["sb_bg"], cursor='hand2', **kw)
        self._cmd     = command
        self._active  = active
        self._text    = text

        self._lbl = tk.Label(self,
            text=f"  {icon}  {text}",
            font=(FONT, 10),
            bg=THEME["sb_active_bg"] if active else THEME["sb_bg"],
            fg=THEME["sb_text_act"]  if active else THEME["sb_text"],
            anchor='w', padx=8, pady=11, cursor='hand2')
        self._lbl.pack(fill='x')

        # Barra lateral izquierda para estado activo
        if active:
            tk.Frame(self, bg=THEME["sb_active"], width=3).place(
                x=0, y=0, relheight=1)

        self.bind('<Button-1>',   self._click)
        self._lbl.bind('<Button-1>', self._click)
        self.bind('<Enter>',      self._hover_in)
        self.bind('<Leave>',      self._hover_out)
        self._lbl.bind('<Enter>', self._hover_in)
        self._lbl.bind('<Leave>', self._hover_out)

    def _hover_in(self, _=None):
        if not self._active:
            self._lbl.config(bg=THEME["sb_hover"], fg=THEME["txt_white"])

    def _hover_out(self, _=None):
        if not self._active:
            self._lbl.config(bg=THEME["sb_bg"], fg=THEME["sb_text"])

    def _click(self, _=None):
        if self._cmd:
            self._cmd()

    def set_active(self, active: bool):
        self._active = active
        if active:
            self._lbl.config(bg=THEME["sb_active_bg"], fg=THEME["sb_text_act"])
            tk.Frame(self, bg=THEME["sb_active"], width=3).place(x=0, y=0, relheight=1)
        else:
            self._lbl.config(bg=THEME["sb_bg"], fg=THEME["sb_text"])
            for w in self.winfo_children():
                if isinstance(w, tk.Frame):
                    w.destroy()



# ── Rounded card widget ───────────────────────────────────────────────────
def _draw_rr(c, x1, y1, x2, y2, r, fill, outline):
    """Rounded rect on canvas; tag='rc'."""
    kw = {'tags': 'rc'}
    r = min(r, max(1,(x2-x1)//2), max(1,(y2-y1)//2))
    c.create_rectangle(x1+r,y1,x2-r,y2, fill=fill,outline='',**kw)
    c.create_rectangle(x1,y1+r,x2,y2-r, fill=fill,outline='',**kw)
    for cx,cy,st in [(x1,y1,90),(x2-2*r,y1,0),(x1,y2-2*r,180),(x2-2*r,y2-2*r,270)]:
        c.create_arc(cx,cy,cx+2*r,cy+2*r,start=st,extent=90,fill=fill,outline=fill,**kw)
    c.create_line(x1+r,y1,x2-r,y1,fill=outline,**kw)
    c.create_line(x1+r,y2,x2-r,y2,fill=outline,**kw)
    c.create_line(x1,y1+r,x1,y2-r,fill=outline,**kw)
    c.create_line(x2,y1+r,x2,y2-r,fill=outline,**kw)
    for cx,cy,st in [(x1,y1,90),(x2-2*r,y1,0),(x1,y2-2*r,180),(x2-2*r,y2-2*r,270)]:
        c.create_arc(cx,cy,cx+2*r,cy+2*r,start=st,extent=90,fill='',outline=outline,style='arc',**kw)

class RoundedCard(tk.Canvas):
    """Canvas card with rounded corners."""
    def __init__(self, parent, radius=8, card_bg=None, border_color=None,
                 padx=16, pady=12, fill_mode=False, **kw):
        card_bg      = card_bg or THEME.get('card_bg','#FFFFFF')
        border_color = border_color or THEME.get('card_border','#E5E7EB')
        try: par_bg = parent.cget('bg')
        except: par_bg = THEME.get('ct_bg','#F9FAFB')
        super().__init__(parent, bg=par_bg, highlightthickness=0, bd=0, **kw)
        self._r=radius; self._fill=card_bg; self._bc=border_color; self._fm=fill_mode
        self._body=tk.Frame(self, bg=card_bg, padx=padx, pady=pady)
        self._fid=self.create_window(radius, radius, anchor='nw', window=self._body)
        self.bind('<Configure>', self._on_cv)
        if not fill_mode:
            self._body.bind('<Configure>', self._on_body)
    @property
    def body(self): return self._body
    def _on_cv(self, e):
        r=self._r; bw=max(1,e.width-2*r)
        self.itemconfig(self._fid, width=bw)
        if self._fm: self.itemconfig(self._fid, height=max(1,e.height-2*r))
        self.delete('rc')
        if e.width>3 and e.height>3:
            _draw_rr(self,1,1,e.width-1,e.height-1,r,self._fill,self._bc)
            self.tag_lower('rc')
    def _on_body(self, e):
        r=self._r; need_h=e.height+2*r
        if abs(self.winfo_height()-need_h)>1: self.configure(height=need_h)


# ── Rounded button widget ─────────────────────────────────────────────────
class RoundedButton(tk.Canvas):
    """Canvas button with rounded corners. Always draws correct color on resize."""
    _R        = 6
    _DISABLED = "#9CA3AF"

    def __init__(self, parent, text, cmd, bg,
                 icon="", font_size=10, btn_pady=9, **kw):
        kw.pop('padx', None); kw.pop('pady', None)
        self._t   = (f"{icon}  {text}") if icon else text
        self._cmd = cmd
        self._bg  = bg
        self._fnt = (FONT, font_size, 'bold')
        self._on  = False
        try:    par_bg = parent.cget('bg')
        except: par_bg = THEME.get('ct_bg','#F9FAFB')
        import tkinter.font as _tf
        _f = _tf.Font(family=FONT, size=font_size, weight='bold')
        h  = _f.metrics('linespace') + btn_pady * 2 + 2
        # Auto minimum width from text measurement unless caller provides one
        if 'width' not in kw:
            kw['width'] = _f.measure(self._t) + 28
        super().__init__(parent, height=h, highlightthickness=0,
                         bd=0, bg=par_bg, cursor='arrow', **kw)
        self.bind('<Configure>',       self._on_cfg)
        self.bind('<Enter>',           self._hover_in)
        self.bind('<Leave>',           self._hover_out)
        self.bind('<ButtonRelease-1>', self._click)

    @staticmethod
    def _dk(c):
        r,g,b = int(c[1:3],16),int(c[3:5],16),int(c[5:7],16)
        return "#{:02x}{:02x}{:02x}".format(
            max(0,int(r*.82)),max(0,int(g*.82)),max(0,int(b*.82)))

    def _draw(self, color=None):
        if color is None:
            color = self._bg if self._on else self._DISABLED
        self.delete('all')
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4 or h < 4:
            return
        r = min(self._R, w//2, h//2)
        self.create_rectangle(r, 0, w-r, h,   fill=color, outline='')
        self.create_rectangle(0, r, w,   h-r, fill=color, outline='')
        for cx,cy,st in [(0,0,90),(w-2*r,0,0),(0,h-2*r,180),(w-2*r,h-2*r,270)]:
            self.create_arc(cx,cy,cx+2*r,cy+2*r,
                            start=st, extent=90, fill=color, outline=color)
        self.create_text(w//2, h//2, text=self._t,
                         font=self._fnt, fill='#ffffff', anchor='center')

    def _on_cfg(self, e=None):
        # Use event width when available (more reliable than winfo_width before mapping)
        w = getattr(e, 'width', 0) or self.winfo_width()
        if w > 4:
            self._draw()
        else:
            self.after(30, self._draw)

    def _hover_in(self, _=None):
        if self._on: self._draw(self._dk(self._bg))
    def _hover_out(self, _=None): self._draw()
    def _click(self, _=None):
        if self._on and self._cmd:
            self._draw(self._dk(self._dk(self._bg)))
            self.after(120, self._draw)
            self._cmd()

    def enable(self):
        self._on = True
        self.config(cursor='hand2')
        self.after_idle(self._draw)

    def disable(self):
        self._on = False
        self.config(cursor='arrow')
        self.after_idle(self._draw)


def _btn(parent, text, cmd, bg, icon="", font_size=10, btn_pady=9, **kw):
    """Rounded button — always enabled."""
    kw.pop('padx', None); kw.pop('pady', None)
    b = RoundedButton(parent, text, cmd, bg, icon=icon,
                      font_size=font_size, btn_pady=btn_pady, **kw)
    b.enable()
    return b




class AppStarter:
    def __init__(self):
        self.root      = tk.Tk()
        self.root.withdraw()
        self.user_data = None

    def start(self):
        self.root.withdraw()
        if not eula_accepted():
            self._step_eula()
        elif not is_licensed():
            self._step_license()
        else:
            self._step_login()
        self.root.mainloop()

    def _step_eula(self):
        def on_accept():
            self.root.after(100, self._after_eula)
        def on_reject():
            self.root.quit(); self.root.destroy(); sys.exit(0)
        EULAWindow(self.root, on_accept=on_accept, on_reject=on_reject)

    def _after_eula(self):
        if not is_licensed(): self._step_license()
        else: self._step_login()

    def _step_license(self):
        _called = [False]
        def _proceed():
            if _called[0]: return
            _called[0] = True
            try:
                if win.winfo_exists(): win.destroy()
            except Exception: pass
            self.root.after(100, self._step_login)

        win = tk.Toplevel(self.root)
        win.withdraw()
        win.protocol("WM_DELETE_WINDOW", _proceed)
        ActivationWindow(win, on_success=_proceed, on_cancel=_proceed)
        win.deiconify()

    def _step_login(self):
        _called = [False]
        def on_login(uid, nombre, rol):
            if _called[0]: return
            _called[0] = True
            self.user_data = {"id": uid, "nombre": nombre, "rol": rol}
            self.root.after(100, self._after_login)
        def on_close():
            self.root.quit(); self.root.destroy()

        win = tk.Toplevel(self.root)
        win.withdraw()
        win.protocol("WM_DELETE_WINDOW", on_close)
        LoginWindow(win, on_success=on_login)
        win.deiconify()

    def _after_login(self):
        if not self.user_data: self.root.quit(); return
        if is_first_run(): self._step_wizard()
        else: self._check_default_password()

    def _check_default_password(self):
        """Si el usuario usa la contraseña por defecto, pide que la cambie."""
        uid = self.user_data.get('id')
        try:
            import sqlite3, os, sys
            base = os.environ.get("APPDATA", os.path.expanduser("~")) if sys.platform=="win32" else os.path.expanduser("~")
            db_path = os.path.join(base, "VenialgoPOS", "pos_database.db")
            conn = sqlite3.connect(db_path)
            row = conn.execute("SELECT password FROM usuarios WHERE id=?", (uid,)).fetchone()
            conn.close()
            if row and row[0] == DEFAULT_ADMIN_HASH:
                self._step_force_password_change()
                return
        except Exception:
            pass
        self._step_main()

    def _step_force_password_change(self):
        """Muestra diálogo obligatorio de cambio de contraseña."""
        win = tk.Toplevel(self.root)
        win.withdraw()
        try:
            from utils.window_icon import set_icon as _si; _si(win)
        except Exception:
            pass
        win.title("Cambiar contraseña — Venialgo POS")
        win.resizable(False, False)
        win.configure(bg="#FFFFFF")
        win.protocol("WM_DELETE_WINDOW", lambda: None)  # No se puede cerrar

        W, H = 420, 480
        win.update_idletasks()
        sx, sy = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"{W}x{H}+{(sx-W)//2}+{(sy-H)//2}")

        FONT = "Segoe UI"
        BLUE  = "#1A4FCC"
        GREEN = "#059669"
        RED   = "#E11D48"

        # Header
        hdr = tk.Frame(win, bg="#0F2347", pady=20)
        hdr.pack(fill='x')
        tk.Label(hdr, text="🔐", font=(FONT,28), bg="#0F2347", fg="#FFFFFF").pack()
        tk.Label(hdr, text="Cambio de contraseña requerido",
                 font=(FONT,13,'bold'), bg="#0F2347", fg="#FFFFFF").pack(pady=(6,2))
        tk.Label(hdr, text="Por seguridad, cambie la contraseña por defecto",
                 font=(FONT,9), bg="#0F2347", fg="#8AABD4").pack()

        # Aviso
        av = tk.Frame(win, bg="#FEF3C7", pady=8, padx=16)
        av.pack(fill='x', padx=20, pady=(14,0))
        tk.Label(av, text="⚠  Está usando la contraseña por defecto (admin123).",
                 font=(FONT,9), bg="#FEF3C7", fg="#92400E", anchor='w').pack(fill='x')

        # Formulario
        form = tk.Frame(win, bg="#FFFFFF", padx=28, pady=16)
        form.pack(fill='both', expand=True)

        def _field(parent, label):
            tk.Label(parent, text=label, font=(FONT,9,'bold'),
                     bg="#FFFFFF", fg="#374151").pack(anchor='w', pady=(10,3))
            outer = tk.Frame(parent, bg="#D1D5DB")
            outer.pack(fill='x')
            inner = tk.Frame(outer, bg="#FFFFFF")
            inner.pack(fill='x', padx=1, pady=1)
            e = tk.Entry(inner, show="●", font=(FONT,11), bg="#FFFFFF",
                         fg="#111827", relief='flat', bd=0)
            e.pack(fill='x', padx=10, ipady=9)
            e.bind('<FocusIn>',  lambda ev, o=outer: o.config(bg=BLUE))
            e.bind('<FocusOut>', lambda ev, o=outer: o.config(bg="#D1D5DB"))
            return e

        e_new  = _field(form, "Nueva contraseña")
        e_conf = _field(form, "Confirmar contraseña")

        lbl_err = tk.Label(form, text="", font=(FONT,9), bg="#FFFFFF", fg=RED)
        lbl_err.pack(anchor='w', pady=(6,0))

        def _save():
            nueva = e_new.get().strip()
            conf  = e_conf.get().strip()
            if len(nueva) < 6:
                lbl_err.config(text="⚠  Mínimo 6 caracteres"); return
            if nueva != conf:
                lbl_err.config(text="⚠  Las contraseñas no coinciden"); return
            try:
                import sqlite3, hashlib, os, sys
                hpwd = hashlib.sha256(nueva.encode()).hexdigest()
                base = os.environ.get("APPDATA", os.path.expanduser("~")) if sys.platform=="win32" else os.path.expanduser("~")
                db_path = os.path.join(base, "VenialgoPOS", "pos_database.db")
                conn = sqlite3.connect(db_path)
                conn.execute("UPDATE usuarios SET password=? WHERE id=?",
                             (hpwd, self.user_data.get('id')))
                conn.commit(); conn.close()
                win.destroy()
                self.root.after(100, self._step_main)
            except Exception as ex:
                lbl_err.config(text=f"Error: {ex}")

        # Botón guardar
        btn = tk.Label(form, text="  ✅  GUARDAR Y CONTINUAR  ",
                       font=(FONT,11,'bold'), bg=GREEN, fg="#FFFFFF",
                       cursor='hand2', pady=12, anchor='center')
        btn.pack(fill='x', pady=(14,0))
        btn.bind('<Enter>',           lambda e: btn.config(bg="#047857"))
        btn.bind('<Leave>',           lambda e: btn.config(bg=GREEN))
        btn.bind('<ButtonRelease-1>', lambda e: _save())
        win.bind('<Return>', lambda e: _save())

        win.deiconify()
        win.grab_set()

    def _step_wizard(self):
        _called = [False]
        def on_complete():
            if _called[0]: return
            _called[0] = True
            try:
                if win.winfo_exists(): win.destroy()
            except Exception: pass
            self.root.after(100, self._step_main)

        win = tk.Toplevel(self.root)
        win.withdraw()
        win.protocol("WM_DELETE_WINDOW", on_complete)
        FirstRunWizard(win, on_complete=on_complete)
        win.deiconify()

    def _step_main(self):
        if not self.user_data: self.root.quit(); return
        self.root.deiconify()
        POSApp(self.root, current_user=self.user_data)



def startup_flow():
    AppStarter().start()


# ══════════════════════════════════════════════════════════════
#  APLICACIÓN PRINCIPAL — DASHBOARD
# ══════════════════════════════════════════════════════════════

class POSApp:

    MENU = [
        ("🏠", "Inicio",        "home"),
        ("🛒", "Punto de Venta","sales"),
        ("💳", "Créditos",      "credits"),
        ("📦", "Productos",     "products"),
        ("👥", "Clientes",      "customers"),
        ("📊", "Reportes",      "reports"),
        ("🏦", "Arqueo de Caja","arqueo"),
        ("⚙️", "Configuración", "admin"),
    ]

    def __init__(self, root, current_user=None):
        self.root         = root
        self.current_user = current_user or {"id":0,"nombre":"Sistema","rol":"Administrador"}
        self._active_key  = "home"
        self._sb_btns     = {}
        self._clock_job   = None

        co          = get_company()
        self._empresa = co.get("razon_social") or "Venialgo Sistemas"

        self.root.title(f"{self._empresa} — POS v{APP_VERSION}")
        self.root.state('zoomed')          # Maximizado
        self.root.minsize(1024, 650)
        self.root.configure(bg=THEME["sb_bg"])
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._set_window_icon(self.root)

        self.db = DatabaseManager()
        backup_service.start()

        self._setup_styles()
        self._build_layout()
        self._show_home()
        # Verificar cuotas vencidas al iniciar (con delay para que la UI cargue)
        self.root.after(1500, self._check_overdue_alert)

    # ── Ícono de ventana ─────────────────────────────────────
    def _set_window_icon(self, window):
        """Aplica el ícono de Venialgo a cualquier ventana Tk o Toplevel."""
        import os, sys
        # Rutas donde puede estar el .ico (desarrollo y producción)
        base = os.path.dirname(os.path.abspath(
            sys.executable if getattr(sys,'frozen',False) else __file__))
        candidates = [
            os.path.join(base, 'assets', 'venialgosist.ico'),
            os.path.join(base, 'assets', 'app_icon.ico'),
            os.path.join(ROOT_DIR, 'assets', 'venialgosist.ico'),
            os.path.join(ROOT_DIR, 'assets', 'app_icon.ico'),
        ]
        for path in candidates:
            if os.path.isfile(path):
                try:
                    window.iconbitmap(path)
                    return
                except Exception:
                    pass
        # Fallback: ícono desde PNG con PhotoImage (sin .ico)
        png_candidates = [
            os.path.join(base, 'assets', 'VenialgoSistemasLogo.png'),
            os.path.join(ROOT_DIR, 'assets', 'VenialgoSistemasLogo.png'),
        ]
        for path in png_candidates:
            if os.path.isfile(path):
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(path).resize((32,32), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    window.iconphoto(True, photo)
                    window._icon_ref = photo  # evitar GC
                    return
                except Exception:
                    pass

    # ── Estilos globales ──────────────────────────────────────
    def _setup_styles(self):
        s = ttk.Style()
        try: s.theme_use('clam')
        except: pass

        s.configure("POS.Treeview",
            background=THEME["card_bg"],
            foreground=THEME["txt_primary"],
            fieldbackground=THEME["card_bg"],
            rowheight=34, font=(FONT, 10),
            borderwidth=0, relief='flat')
        s.configure("POS.Treeview.Heading",
            background=THEME["sb_bg"],
            foreground=THEME["txt_white"],
            font=(FONT, 9, 'bold'),
            relief='flat', borderwidth=0, padding=(12, 8))
        s.map("POS.Treeview",
            background=[('selected', THEME["acc_blue"])],
            foreground=[('selected', THEME["txt_white"])])
        s.map("POS.Treeview.Heading",
            background=[('active', THEME["acc_blue"])])

        s.configure("Sidebar.TFrame", background=THEME["sb_bg"])
        s.configure("Content.TFrame", background=THEME["ct_bg"])

    # ── Layout raíz: sidebar + main ───────────────────────────
    def _build_layout(self):
        # Footer PRIMERO — regla tkinter: side='bottom' debe ir antes que side='left'
        self._build_footer()

        # Columna izquierda (sidebar fija 220px) — con degradado
        SB_W = 220
        self._sb_canvas = tk.Canvas(self.root, width=SB_W, highlightthickness=0, bd=0)
        self._sb_canvas.pack(side='left', fill='y')

        # Frame contenedor sobre el canvas
        self._sidebar = tk.Frame(self._sb_canvas, bg=THEME["sb_bg"], width=SB_W)
        self._sb_win  = self._sb_canvas.create_window(0, 0, anchor='nw',
                                                       window=self._sidebar,
                                                       width=SB_W)

        def _draw_gradient(event=None):
            h = self._sb_canvas.winfo_height() or 800
            self._sb_canvas.delete("grad")
            r1,g1,b1 = 0x0D,0x1B,0x4B   # #0D1B4B top
            r2,g2,b2 = 0x1A,0x3A,0x8F   # #1A3A8F bottom
            for i in range(h):
                t = i / h
                r = int(r1+(r2-r1)*t); g = int(g1+(g2-g1)*t); b = int(b1+(b2-b1)*t)
                self._sb_canvas.create_line(0,i,SB_W,i,
                    fill=f"#{r:02x}{g:02x}{b:02x}", tags="grad")
            self._sb_canvas.tag_lower("grad")
            self._sb_canvas.itemconfig(self._sb_win, height=max(h, self._sidebar.winfo_reqheight()))

        def _update_height(event=None):
            h = max(self._sb_canvas.winfo_height(), self._sidebar.winfo_reqheight())
            self._sb_canvas.itemconfig(self._sb_win, height=h)
            _draw_gradient()

        self._sb_canvas.bind("<Configure>", _update_height)
        self._sidebar.bind("<Configure>",   _update_height)

        self._sidebar.pack_propagate(False)

        # Columna derecha (topbar + contenido)
        right = tk.Frame(self.root, bg=THEME["ct_bg"])
        right.pack(side='left', fill='both', expand=True)

        self._build_sidebar()
        self._build_topbar(right)
        self._build_content_area(right)

    # ── FOOTER ────────────────────────────────────────────────
    def _build_footer(self):
        """Barra inferior con datos de contacto de Venialgo Sistemas."""
        footer = tk.Frame(self.root, bg="#0F172A", height=28)
        footer.pack(fill='x', side='bottom')
        footer.pack_propagate(False)
        tk.Label(footer,
                 text="  ✉ davenialgo@proton.me   │   📱 WhatsApp: +595 994-686 493   │   🌐 www.venialgosistemas.com  ",
                 font=(FONT, 8), bg="#0F172A", fg="#FFFFFF").pack(side='left', pady=4)

    # ── SIDEBAR ───────────────────────────────────────────────
    def _build_sidebar(self):
        sb = self._sidebar

        # Logo — muestra logo de empresa si está configurado, o círculo con inicial
        logo_area = tk.Frame(sb, bg=THEME["sb_bg"], pady=14)
        logo_area.pack(fill='x')
        self._sb_logo_area = logo_area   # referencia para refresh

        # Intentar cargar logo de la empresa desde la BD
        _logo_shown = False
        try:
            from utils.company_header import get_company
            from PIL import Image, ImageTk
            _co = get_company()
            _logo_path = _co.get("logo_path","")
            if _logo_path and __import__('os').path.isfile(_logo_path):
                _img = Image.open(_logo_path).convert("RGBA")
                _img.thumbnail((42,42), Image.LANCZOS)
                # Pegar sobre fondo transparente cuadrado
                _canvas_img = Image.new("RGBA",(42,42),(0,0,0,0))
                _ox=(42-_img.width)//2; _oy=(42-_img.height)//2
                _canvas_img.paste(_img,(_ox,_oy),_img)
                self._sb_logo_photo = ImageTk.PhotoImage(_canvas_img)
                tk.Label(logo_area, image=self._sb_logo_photo,
                         bg=THEME["sb_bg"]).pack(side='left', padx=(16,10))
                _logo_shown = True
        except Exception:
            pass

        if not _logo_shown:
            logo_circle = tk.Frame(logo_area, bg=THEME["sb_logo_bg"], width=38, height=38)
            logo_circle.pack_propagate(False)
            logo_circle.pack(side='left', padx=(20, 10))
            tk.Label(logo_circle, text=self._empresa[:1].upper(), font=(FONT, 16, 'bold'),
                     bg=THEME["sb_logo_bg"], fg=THEME["txt_white"]).pack(expand=True)

        tk.Label(logo_area, text=self._empresa,
                 font=(FONT, 11, 'bold'),
                 bg=THEME["sb_bg"], fg=THEME["txt_white"],
                 wraplength=140, justify='left').pack(side='left')

        # Separador
        tk.Frame(sb, bg="#1E3473", height=1).pack(fill='x', padx=16, pady=(0, 10))

        # Label sección
        tk.Label(sb, text="NAVEGACIÓN",
                 font=(FONT, 7, 'bold'),
                 bg=THEME["sb_bg"], fg=THEME["sb_text"],
                 padx=20).pack(anchor='w', pady=(4, 6))

        # Filtrar por rol
        rol   = self.current_user.get('rol', '')
        perms = {
            "home":     ["Administrador","Supervisor","Cajero"],
            "sales":    ["Administrador","Supervisor","Cajero"],
            "credits":  ["Administrador","Supervisor","Cajero"],
            "products": ["Administrador","Supervisor"],
            "customers":["Administrador","Supervisor","Cajero"],
            "reports":  ["Administrador","Supervisor","Cajero"],
            "arqueo":   ["Administrador","Supervisor"],
            "admin":    ["Administrador"],
        }

        for icon, label, key in self.MENU:
            if rol not in perms.get(key, []):
                continue
            btn = SidebarButton(sb, label, icon,
                                command=lambda k=key: self._navigate(k),
                                active=(key == self._active_key))
            btn.pack(fill='x', padx=8, pady=1)
            self._sb_btns[key] = btn

        # Espacio flexible
        tk.Frame(sb, bg=THEME["sb_bg"]).pack(fill='both', expand=True)

        # Separador
        tk.Frame(sb, bg="#1E3473", height=1).pack(fill='x', padx=16, pady=8)

        # Info backup
        self._lbl_backup = tk.Label(sb,
            text="Backup: ---",
            font=(FONT, 7), bg=THEME["sb_bg"], fg=THEME["sb_text"],
            wraplength=190, justify='left', padx=20)
        self._lbl_backup.pack(anchor='w', pady=(0, 4))

        # Botón cerrar sesión
        btn_lo = RoundedButton(sb, "Cerrar Sesión", self._logout,
                               THEME["btn_logout"], icon="✖", btn_pady=11)
        btn_lo.pack(fill='x', padx=8, pady=(0, 12))
        btn_lo.enable()

    # ── TOPBAR ────────────────────────────────────────────────
    def _build_topbar(self, parent):
        tb = tk.Frame(parent, bg=THEME["tb_bg"], height=60)
        tb.pack(fill='x', side='top')
        tb.pack_propagate(False)

        # Borde inferior
        tk.Frame(parent, bg=THEME["tb_border"], height=1).pack(fill='x')

        # Izquierda: nombre del módulo (se actualiza al navegar)
        left = tk.Frame(tb, bg=THEME["tb_bg"])
        left.pack(side='left', fill='y', padx=24)

        self._lbl_module = tk.Label(left, text="Inicio",
            font=(FONT, 15, 'bold'),
            bg=THEME["tb_bg"], fg=THEME["txt_primary"])
        self._lbl_module.pack(side='left', pady=16)

        # Derecha: reloj + usuario + rol + licencia
        right = tk.Frame(tb, bg=THEME["tb_bg"])
        right.pack(side='right', fill='y', padx=20)

        # Reloj
        self._lbl_clock = tk.Label(right, text="",
            font=(FONT_MONO, 10),
            bg=THEME["tb_bg"], fg=THEME["txt_secondary"])
        self._lbl_clock.pack(side='right', padx=(16, 0), pady=18)
        self._tick_clock()

        # Separador
        tk.Frame(right, bg=THEME["tb_border"], width=1).pack(
            side='right', fill='y', pady=14, padx=8)

        # Badge licencia
        lic_ok = is_licensed()
        tk.Label(right,
            text=" Licenciado " if lic_ok else " Sin licencia ",
            font=(FONT, 8, 'bold'),
            bg=THEME["acc_green"] if lic_ok else THEME["acc_rose"],
            fg="white", padx=6, pady=3).pack(side='right', pady=20)

        # Badge rol
        rol_col = {"Administrador": THEME["acc_purple"],
                   "Supervisor":    THEME["acc_cyan"],
                   "Cajero":        THEME["acc_green"]}.get(
                   self.current_user.get('rol',''), THEME["acc_blue"])
        tk.Label(right,
            text=f" {self.current_user.get('rol','')} ",
            font=(FONT, 8, 'bold'),
            bg=rol_col, fg="white", padx=6, pady=3).pack(side='right', pady=20, padx=4)

        # Nombre usuario
        tk.Label(right,
            text=f"👤  {self.current_user.get('nombre','')}",
            font=(FONT, 10),
            bg=THEME["tb_bg"], fg=THEME["txt_primary"]).pack(side='right', pady=18)

    def _tick_clock(self):
        self._lbl_clock.config(text=fecha_corta())
        self._clock_job = self.root.after(1000, self._tick_clock)

    # ── ÁREA DE CONTENIDO ─────────────────────────────────────
    def _build_content_area(self, parent):
        self._content = tk.Frame(parent, bg=THEME["ct_bg"])
        self._content.pack(fill='both', expand=True)

    def _clear_content(self):
        for w in self._content.winfo_children():
            w.destroy()

    # ── NAVEGACIÓN ────────────────────────────────────────────
    def _navigate(self, key):
        # Desactivar botón anterior
        if self._active_key in self._sb_btns:
            self._sb_btns[self._active_key].set_active(False)
        self._active_key = key
        if key in self._sb_btns:
            self._sb_btns[key].set_active(True)

        # Nombre módulo en topbar
        labels = {k: l for _, l, k in self.MENU}
        self._lbl_module.config(text=labels.get(key, ""))

        self._clear_content()
        dispatch = {
            "home":     self._show_home,
            "sales":    self._show_module_sales,
            "credits":  self._show_module_credits,
            "products": self._show_module_products,
            "customers":self._show_module_customers,
            "reports":  self._show_module_reports,
            "arqueo":   self._show_module_arqueo,
            "admin":    self._show_module_admin,
        }
        dispatch.get(key, self._show_home)()

    # ── HOME: DASHBOARD ───────────────────────────────────────
    def _show_home(self):
        ct = self._content
        scroll_canvas = tk.Canvas(ct, bg=THEME["ct_bg"], highlightthickness=0)
        scrollbar     = ttk.Scrollbar(ct, orient='vertical',
                                      command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        scroll_canvas.pack(side='left', fill='both', expand=True)

        page = tk.Frame(scroll_canvas, bg=THEME["ct_bg"])
        win_id = scroll_canvas.create_window((0,0), window=page, anchor='nw')

        def _on_resize(e):
            scroll_canvas.itemconfig(win_id, width=e.width)
        def _on_frame(e):
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox('all'))
        scroll_canvas.bind('<Configure>', _on_resize)
        page.bind('<Configure>', _on_frame)
        def _mwheel_home(e):
            try: scroll_canvas.yview_scroll(-1*(e.delta//120), 'units')
            except Exception: scroll_canvas.unbind_all('<MouseWheel>')
        scroll_canvas.bind('<Enter>', lambda e: scroll_canvas.bind_all('<MouseWheel>', _mwheel_home))
        scroll_canvas.bind('<Leave>', lambda e: scroll_canvas.unbind_all('<MouseWheel>'))

        pad = {"padx": 28, "pady": 0}

        # ── Bienvenida ────────────────────────────────────────
        greeting = tk.Frame(page, bg=THEME["ct_bg"])
        greeting.pack(fill='x', padx=28, pady=(16, 0))
        hoy = fecha_larga()
        tk.Label(greeting, text=f"Bienvenido, {self.current_user.get('nombre','')} 👋",
                 font=(FONT, 16, 'bold'),
                 bg=THEME["ct_bg"], fg=THEME["txt_primary"]).pack(anchor='w')
        tk.Label(greeting, text=hoy,
                 font=(FONT, 9),
                 bg=THEME["ct_bg"], fg=THEME["txt_secondary"]).pack(anchor='w', pady=(2,0))

        # ── Línea separadora ─────────────────────────────────
        tk.Frame(page, bg=THEME["card_border"], height=1).pack(
            fill='x', padx=28, pady=(12, 8))

        # ── Cards de estadísticas ─────────────────────────────
        tk.Label(page, text="Resumen del día",
                 font=(FONT, 10, 'bold'),
                 bg=THEME["ct_bg"], fg=THEME["txt_secondary"]).pack(
                 anchor='w', padx=28, pady=(0, 10))

        cards_row = tk.Frame(page, bg=THEME["ct_bg"])
        cards_row.pack(fill='x', padx=24, pady=(0, 20))

        # Obtener datos reales
        stats = self._get_today_stats()

        cards_data = [
            ("Ventas del día",    stats["count"],     THEME["acc_blue"],   "🛒"),
            ("Ingresos",          stats["revenue"],   THEME["acc_green"],  "💰"),
            ("Productos vendidos",stats["items"],     THEME["acc_amber"],  "📦"),
            ("Créditos activos",  stats["credits"],   THEME["acc_purple"], "💳"),
        ]

        for i, (title, val, accent, icon) in enumerate(cards_data):
            card = stat_card(cards_row, title, val, accent, icon)
            card.grid(row=0, column=i, sticky='nsew', padx=4, pady=4)
            cards_row.columnconfigure(i, weight=1)



        # ── Tabla últimas ventas ──────────────────────────────
        bottom = tk.Frame(page, bg=THEME["ct_bg"])
        bottom.pack(fill='both', expand=True, padx=28, pady=(0, 28))
        bottom.columnconfigure(0, weight=3)
        bottom.columnconfigure(1, weight=2)
        bottom.rowconfigure(0, weight=1)

        # Card tabla
        tbl_outer = RoundedCard(bottom, padx=0, pady=0, fill_mode=True)
        tbl_outer.grid(row=0, column=0, sticky='nsew', padx=(0,8))
        tbl_inner = tbl_outer.body

        tk.Label(tbl_inner, text="Últimas ventas",
                 font=(FONT, 11, 'bold'),
                 bg=THEME["card_bg"], fg=THEME["txt_primary"]).pack(
                 anchor='w', padx=16, pady=(14,8))
        tk.Frame(tbl_inner, bg=THEME["card_border"], height=1).pack(fill='x')

        cols = ('ID','Fecha','Cliente','Total','Método')
        tree = ttk.Treeview(tbl_inner, columns=cols, show='headings',
                            height=8, style='POS.Treeview')
        for col, w in zip(cols, [50,130,180,110,100]):
            tree.heading(col, text=col)
            tree.column(col, width=w,
                        anchor='center' if col in ('ID','Total') else 'w')

        sb_tree = ttk.Scrollbar(tbl_inner, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=sb_tree.set)
        sb_tree.pack(side='right', fill='y', padx=(0,4), pady=4)
        tree.pack(fill='both', expand=True, padx=4, pady=(4,12))

        # Insertar datos
        from utils.formatters import format_currency
        ventas = self.db.get_sales_by_date(
            datetime.now().strftime('%Y-%m-%d'),
            datetime.now().strftime('%Y-%m-%d')
        )
        for v in ventas[:30]:
            tree.insert('', 'end', values=(
                v.get('id',''),
                v.get('fecha','')[:16] if v.get('fecha') else '',
                v.get('customer_name','') or 'Consumidor Final',
                format_currency(v.get('total',0)),
                v.get('payment_method',''),
            ))

        # Alternar colores filas
        tree.tag_configure('odd',  background='#F9FAFB')
        tree.tag_configure('even', background=THEME["card_bg"])
        for i, iid in enumerate(tree.get_children()):
            tree.item(iid, tags=('odd' if i%2 else 'even',))

        # Card accesos rápidos
        act_outer = RoundedCard(bottom, padx=0, pady=0, fill_mode=True)
        act_outer.grid(row=0, column=1, sticky='nsew', padx=(8,0))
        act_inner = act_outer.body

        tk.Label(act_inner, text="Accesos rápidos",
                 font=(FONT, 11, 'bold'),
                 bg=THEME["card_bg"], fg=THEME["txt_primary"]).pack(
                 anchor='w', padx=16, pady=(14,8))
        tk.Frame(act_inner, bg=THEME["card_border"], height=1).pack(fill='x')

        _rol = self.current_user.get('rol', '')
        _qa_perms = {
            "sales":    ["Administrador","Supervisor","Cajero"],
            "credits":  ["Administrador","Supervisor","Cajero"],
            "products": ["Administrador","Supervisor"],
            "customers":["Administrador","Supervisor","Cajero"],
            "reports":  ["Administrador","Supervisor","Cajero"],
        }
        quick_actions = [
            ("🛒  Nueva venta",     THEME["acc_blue"],   "sales"),
            ("💳  Ver créditos",    THEME["acc_purple"], "credits"),
            ("📦  Agregar producto",THEME["acc_amber"],  "products"),
            ("👥  Nuevo cliente",   THEME["acc_green"],  "customers"),
            ("📊  Ver reportes",    THEME["acc_cyan"],   "reports"),
        ]
        btns_qa = [(l,c,k) for l,c,k in quick_actions
                   if _rol in _qa_perms.get(k,[])]
        for i,(label,color,key) in enumerate(btns_qa):
            is_last = (i == len(btns_qa)-1)
            btn = RoundedButton(act_inner, label, lambda k=key: self._navigate(k),
                                color, btn_pady=10, font_size=10)
            btn.pack(fill='x', padx=12, pady=(4, 12 if is_last else 4))
            btn.enable()

    def _darken(self, hex_color):
        """Oscurece un color hex un 15%."""
        r,g,b = int(hex_color[1:3],16), int(hex_color[3:5],16), int(hex_color[5:7],16)
        return f"#{max(0,int(r*0.85)):02x}{max(0,int(g*0.85)):02x}{max(0,int(b*0.85)):02x}"

    def _get_today_stats(self):
        try:
            hoy = datetime.now().strftime('%Y-%m-%d')
            s   = self.db.get_sales_summary(hoy, hoy)
            from utils.formatters import format_currency
            credits = self.db.get_all_credit_sales('active')
            items = self.db.execute_scalar(
                """SELECT COALESCE(SUM(d.cantidad),0) FROM detalle_ventas d
                   JOIN ventas v ON d.venta_id=v.id
                   WHERE v.fecha >= ?""", (hoy,)) or 0
            return {
                "count":   str(s.get('total_sales', 0)),
                "revenue": format_currency(s.get('total_revenue', 0)),
                "items":   str(int(items)),
                "credits": str(len(credits)),
            }
        except Exception:
            return {"count":"0","revenue":"Gs. 0","items":"0","credits":"0"}

    # ── MÓDULOS ───────────────────────────────────────────────
    def _show_module_arqueo(self):
        from modules.arqueo.arqueo_ui import ArqueoModule
        ArqueoModule(self._content, self.db, current_user=self.current_user)

    def _show_module_sales(self):
        # Verificar arqueo vencido antes de abrir ventas
        try:
            from modules.arqueo.arqueo_ui import check_arqueo_bloqueado
            if check_arqueo_bloqueado(self.db, self.root):
                return  # Bloqueado — muestra diálogo automáticamente
        except Exception:
            pass
        from modules.sales.sale_ui import SalesModule
        SalesModule(self._content, self.db)

    def _show_module_credits(self):
        from modules.credits.credit_ui import CreditsModule
        CreditsModule(self._content, self.db)

    def _show_module_products(self):
        from modules.products.product_ui import ProductModule
        ProductModule(self._content, self.db, self.current_user)

    def _show_module_customers(self):
        from modules.customers.customer_ui import CustomerModule
        CustomerModule(self._content, self.db)

    def _show_module_reports(self):
        from modules.reports.report_ui import ReportsModule
        ReportsModule(self._content, self.db, current_user=self.current_user)

    def _show_module_admin(self):
        from modules.admin.admin_ui import AdminModule
        AdminModule(self._content, self.db, self.current_user,
                    on_company_saved=self._refresh_header)

    def _refresh_header(self):
        co = get_company()
        self._empresa = co.get("razon_social") or "Venialgo Sistemas"
        self.root.title(f"{self._empresa} — POS v{APP_VERSION}")
        # Refrescar logo del sidebar sin reconstruir todo el sidebar
        self._refresh_sidebar_logo(co)

    def _refresh_sidebar_logo(self, co=None):
        """Reconstruye solo el área del logo en el sidebar."""
        if not hasattr(self, "_sb_logo_area"):
            return
        if co is None:
            co = get_company()
        logo_area = self._sb_logo_area
        # Destruir widgets actuales del logo_area
        for w in logo_area.winfo_children():
            w.destroy()
        # Reconstruir
        _logo_shown = False
        try:
            from PIL import Image, ImageTk
            import os as _os
            _logo_path = co.get("logo_path","")
            if _logo_path and _os.path.isfile(_logo_path):
                _img = Image.open(_logo_path).convert("RGBA")
                _img.thumbnail((42,42), Image.LANCZOS)
                _canvas_img = Image.new("RGBA",(42,42),(0,0,0,0))
                _ox=(42-_img.width)//2; _oy=(42-_img.height)//2
                _canvas_img.paste(_img,(_ox,_oy),_img)
                self._sb_logo_photo = ImageTk.PhotoImage(_canvas_img)
                tk.Label(logo_area, image=self._sb_logo_photo,
                         bg=THEME["sb_bg"]).pack(side='left', padx=(16,10))
                _logo_shown = True
        except Exception:
            pass
        if not _logo_shown:
            logo_circle = tk.Frame(logo_area, bg=THEME["sb_logo_bg"], width=38, height=38)
            logo_circle.pack_propagate(False)
            logo_circle.pack(side='left', padx=(20,10))
            tk.Label(logo_circle, text=self._empresa[:1].upper(),
                     font=(FONT,16,'bold'),
                     bg=THEME["sb_logo_bg"], fg=THEME["txt_white"]).pack(expand=True)
        tk.Label(logo_area, text=self._empresa,
                 font=(FONT,11,'bold'),
                 bg=THEME["sb_bg"], fg=THEME["txt_white"],
                 wraplength=140, justify='left').pack(side='left')

    # ── CIERRE / LOGOUT ───────────────────────────────────────
    def _check_overdue_alert(self):
        """Muestra alerta si hay créditos con cuotas vencidas al iniciar el sistema."""
        try:
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            # Obtener créditos vencidos
            credits = self.db.get_all_credits()
            vencidos = []
            for c in credits:
                if c.get('status') == 'active':
                    nxt = c.get('next_payment_date') or c.get('proximo_pago','')
                    if nxt and nxt < today:
                        nombre = c.get('customer_name') or c.get('cliente_nombre','Sin nombre')
                        monto  = c.get('installment_amount') or c.get('monto_cuota', 0)
                        vencidos.append((nombre, nxt, monto))
            if not vencidos:
                return
            # Mostrar ventana de alerta
            dlg = tk.Toplevel(self.root)
            self._set_window_icon(dlg)
            dlg.title("⚠ Cuotas Vencidas")
            dlg.resizable(False, False)
            dlg.configure(bg="#FFFFFF")
            dlg.transient(self.root)
            dlg.grab_set()
            w = 460; h = min(140 + len(vencidos)*34, 520)
            dlg.update_idletasks()
            sx = (dlg.winfo_screenwidth()  - w) // 2
            sy = (dlg.winfo_screenheight() - h) // 2
            dlg.geometry(f"{w}x{h}+{sx}+{sy}")
            # Header rojo
            hdr = tk.Frame(dlg, bg="#B91C1C", pady=12)
            hdr.pack(fill='x')
            tk.Label(hdr, text="⚠  Cuotas Vencidas",
                     font=(FONT,13,'bold'), bg="#B91C1C", fg="#FFFFFF").pack(anchor='w', padx=16)
            tk.Label(hdr, text=f"Hay {len(vencidos)} crédito(s) con cuotas pendientes de cobro",
                     font=(FONT,9), bg="#B91C1C", fg="#FFCDD2").pack(anchor='w', padx=16)
            # Lista
            from utils.formatters import format_currency
            list_frame = tk.Frame(dlg, bg="#FFFFFF", padx=16, pady=8)
            list_frame.pack(fill='both', expand=True)
            # Encabezado tabla
            hdr_row = tk.Frame(list_frame, bg="#FEF2F2")
            hdr_row.pack(fill='x', pady=(0,2))
            for txt, w_ in [("Cliente",200),("Vencimiento",110),("Cuota",110)]:
                tk.Label(hdr_row, text=txt, font=(FONT,9,'bold'),
                         bg="#FEF2F2", fg="#7F1D1D", width=w_//8, anchor='w').pack(side='left', padx=4, pady=4)
            tk.Frame(list_frame, bg="#FECACA", height=1).pack(fill='x')
            # Filas
            canvas = tk.Canvas(list_frame, bg="#FFFFFF", highlightthickness=0)
            scrollbar = tk.Scrollbar(list_frame, orient='vertical', command=canvas.yview)
            scroll_frame = tk.Frame(canvas, bg="#FFFFFF")
            scroll_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
            canvas.create_window((0,0), window=scroll_frame, anchor='nw')
            canvas.configure(yscrollcommand=scrollbar.set)
            max_visible = min(len(vencidos), 8)
            canvas.pack(side='left', fill='both', expand=True)
            if len(vencidos) > 8: scrollbar.pack(side='right', fill='y')
            for i, (nombre, fecha, monto) in enumerate(vencidos):
                row_bg = "#FFF1F2" if i%2==0 else "#FFFFFF"
                row = tk.Frame(scroll_frame, bg=row_bg)
                row.pack(fill='x')
                tk.Label(row, text=nombre[:28], font=(FONT,9), bg=row_bg,
                         fg="#1F2937", anchor='w', width=25).pack(side='left', padx=4, pady=3)
                tk.Label(row, text=fecha, font=(FONT,9), bg=row_bg,
                         fg="#DC2626", anchor='w', width=13).pack(side='left', padx=4)
                tk.Label(row, text=format_currency(monto), font=(FONT,9,'bold'), bg=row_bg,
                         fg="#059669", anchor='e', width=13).pack(side='left', padx=4)
            # Botones
            btn_row = tk.Frame(dlg, bg="#FFFFFF", pady=10)
            btn_row.pack(fill='x', padx=16)
            def _ir_creditos():
                dlg.grab_release(); dlg.destroy()
                self._navigate('credits')
            tk.Label(btn_row, text="  Ver Créditos  ", font=(FONT,10,'bold'),
                     bg="#2563EB", fg="#FFFFFF", cursor='hand2', padx=12, pady=8).pack(side='left', padx=(0,8))
            tk.Label(btn_row, text="  Cerrar  ", font=(FONT,10),
                     bg="#6B7280", fg="#FFFFFF", cursor='hand2', padx=12, pady=8).pack(side='left')
            # Bindings
            btn_row.winfo_children()[0].bind('<ButtonRelease-1>', lambda e: _ir_creditos())
            btn_row.winfo_children()[1].bind('<ButtonRelease-1>', lambda e: (dlg.grab_release(), dlg.destroy()))
            dlg.bind('<Escape>', lambda e: (dlg.grab_release(), dlg.destroy()))
        except Exception as ex:
            print(f"[overdue alert] {ex}")

    def _on_close(self):
        if self._clock_job:
            self.root.after_cancel(self._clock_job)
        try: backup_service.stop()
        except: pass
        self.root.destroy()

    def _logout(self):
        if messagebox.askyesno("Cerrar Sesión", "¿Desea cerrar la sesión?"):
            if self._clock_job:
                self.root.after_cancel(self._clock_job)
            try: backup_service.stop()
            except: pass
            self.root.destroy()
            startup_flow()


def main():
    startup_flow()

if __name__ == "__main__":
    main()
