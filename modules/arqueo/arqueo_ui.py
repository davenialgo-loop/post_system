"""Módulo Arqueo de Caja — Venialgo POS"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from utils.formatters import format_currency
try:
    from utils.window_icon import set_icon as _set_icon
except ImportError:
    def _set_icon(w): pass

THEME = {
    "ct_bg":"#F9FAFB","card_bg":"#FFFFFF","card_border":"#E5E7EB","sb_bg":"#111827",
    "txt_primary":"#111827","txt_secondary":"#6B7280","txt_white":"#FFFFFF",
    "acc_blue":"#2563EB","acc_green":"#059669","acc_amber":"#D97706","acc_rose":"#E11D48",
    "acc_purple":"#7C3AED","btn_secondary":"#6B7280","btn_danger":"#DC2626",
    "input_bg":"#FFFFFF","input_brd":"#D1D5DB","input_foc":"#2563EB",
    "row_odd":"#F9FAFB","row_even":"#FFFFFF",
}
FONT = "Segoe UI"

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
    """Canvas card with rounded corners.
    fill_mode=False → body height drives canvas height (for KPI/form cards).
    fill_mode=True  → canvas height drives body height (for table/fill cards).
    """
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
        if color is None: color = self._bg if self._on else self._DISABLED
        self.delete('all')
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4 or h < 4: return
        r = min(self._R, w//2, h//2)
        self.create_rectangle(r, 0, w-r, h, fill=color, outline='')
        self.create_rectangle(0, r, w, h-r, fill=color, outline='')
        for cx,cy,st in [(0,0,90),(w-2*r,0,0),(0,h-2*r,180),(w-2*r,h-2*r,270)]:
            self.create_arc(cx,cy,cx+2*r,cy+2*r,
                            start=st,extent=90,fill=color,outline=color)
        self.create_text(w//2, h//2, text=self._t,
                         font=self._fnt, fill='#ffffff', anchor='center')

    def _on_cfg(self, e=None):
        # winfo_width returns 1 until first layout — use event width if available
        w = (e.width if e and hasattr(e,'width') else 0) or self.winfo_width()
        if w > 4:
            self._draw()
        else:
            self.after(20, self._draw)   # retry after layout pass

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
        self.after_idle(self._draw)   # draw after Tk processes geometry

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






def _entry(parent, **kw):
    outer = tk.Frame(parent, bg=THEME["input_brd"])
    inner = tk.Frame(outer, bg=THEME["input_bg"]); inner.pack(fill='x',padx=1,pady=1)
    e = tk.Entry(inner, font=(FONT,12), bg=THEME["input_bg"], fg=THEME["txt_primary"],
                 relief='flat', bd=0, insertbackground=THEME["acc_blue"], **kw)
    e.pack(fill='x', padx=12, pady=9)
    outer._e = e
    outer.get   = e.get
    outer.delete = e.delete
    outer.insert = e.insert
    outer.focus  = e.focus
    outer.bind   = e.bind
    e.bind('<FocusIn>',  lambda _: outer.config(bg=THEME["input_foc"]))
    e.bind('<FocusOut>', lambda _: outer.config(bg=THEME["input_brd"]))
    return outer

def _center(win, w, h):
    win.update_idletasks()
    sw,sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

def _setup_styles():
    s = ttk.Style()
    try: s.theme_use('clam')
    except: pass
    s.configure("POS.Treeview", background="#fff", foreground="#111827",
        fieldbackground="#fff", rowheight=32, font=(FONT,10), borderwidth=0)
    s.configure("POS.Treeview.Heading", background="#111827", foreground="#fff",
        font=(FONT,9,'bold'), relief='flat', padding=(8,6))
    s.map("POS.Treeview", background=[('selected','#2563EB')], foreground=[('selected','#fff')])


class ArqueoModule:
    def __init__(self, parent, db_manager, current_user=None):
        self.parent = parent
        self.db = db_manager
        self.current_user = current_user or {}
        self._usuario_nombre = self.current_user.get('nombre','Sistema')
        self._rol = (self.current_user.get('rol') or '').lower()
        _setup_styles()
        self._build()

    def _build(self):
        bg = THEME["ct_bg"]
        # Header
        hdr = tk.Frame(self.parent, bg=bg)
        hdr.pack(fill='x', padx=28, pady=(20,0))
        tk.Label(hdr, text="🏦  Arqueo de Caja", font=(FONT,16,'bold'),
                 bg=bg, fg=THEME["txt_primary"]).pack(side='left')
        tk.Frame(self.parent, bg=THEME["card_border"], height=1).pack(fill='x', padx=28, pady=(10,14))

        # Panel principal
        main = tk.Frame(self.parent, bg=bg)
        main.pack(fill='both', expand=True, padx=24)

        # Columna izquierda: estado actual + acciones
        left = tk.Frame(main, bg=bg); left.pack(side='left', fill='both', expand=True, padx=(0,12))

        # Card estado
        self._status_card_outer = RoundedCard(left, padx=20, pady=20)
        self._status_card_outer.pack(fill='x', pady=(0,14))
        self._status_card = self._status_card_outer.body

        # Card acciones
        act_outer = RoundedCard(left, padx=20, pady=16)
        act_outer.pack(fill='x', pady=(0,14))
        act_inner = act_outer.body
        tk.Label(act_inner, text="Acciones", font=(FONT,10,'bold'),
                 bg=THEME["card_bg"], fg=THEME["txt_secondary"]).pack(anchor='w', pady=(0,10))

        self.btn_abrir  = _btn(act_inner, "Abrir Caja",  self._abrir_arqueo,  THEME["acc_green"],  "🔓")
        self.btn_abrir.pack(fill='x', pady=(0,8))
        self.btn_cerrar = _btn(act_inner, "Cerrar Caja", self._cerrar_arqueo, THEME["btn_danger"],  "🔒")
        self.btn_cerrar.pack(fill='x')

        # Columna derecha: historial
        right = tk.Frame(main, bg=bg); right.pack(side='right', fill='both', expand=True, padx=(12,0))

        hist_outer = RoundedCard(right, padx=0, pady=0, fill_mode=True)
        hist_outer.pack(fill='both', expand=True)
        hist_inner = hist_outer.body

        hist_hdr = tk.Frame(hist_inner, bg=THEME["card_bg"], padx=16, pady=10)
        hist_hdr.pack(fill='x')
        tk.Label(hist_hdr, text="Historial de Arqueos", font=(FONT,11,'bold'),
                 bg=THEME["card_bg"], fg=THEME["txt_primary"]).pack(side='left')
        btn_ref = _btn(hist_hdr, "Actualizar", self._refresh, THEME["acc_blue"], "↻")
        btn_ref.pack(side='right')
        tk.Frame(hist_inner, bg=THEME["card_border"], height=1).pack(fill='x')

        cols = ('ID','Apertura','Cierre','Ventas','Efectivo','Total Venta','Estado')
        self.tree = ttk.Treeview(hist_inner, columns=cols, show='headings', style='POS.Treeview')
        for col, w in zip(cols, [45, 130, 130, 60, 110, 110, 80]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor='center')
        sb = ttk.Scrollbar(hist_inner, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y', padx=(0,4), pady=4)
        self.tree.pack(fill='both', expand=True, padx=4, pady=4)
        self.tree.bind('<Double-Button-1>', self._ver_detalle)
        self.tree.tag_configure('abierto', background='#D1FAE5', foreground='#065F46')
        self.tree.tag_configure('cerrado', background='#F9FAFB')

        self._refresh()

    def _refresh(self):
        """Actualiza estado y tabla."""
        self._update_status_card()
        self._load_history()

    def _update_status_card(self):
        for w in self._status_card.winfo_children():
            w.destroy()

        arq = None
        try: arq = self.db.get_arqueo_abierto()
        except: pass

        if arq:
            fecha_ap = arq.get('fecha_apertura','')[:16]
            # Calcular ventas desde apertura
            try:
                ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn = self.db._conn()
                r = conn.execute(
                    "SELECT COUNT(*), COALESCE(SUM(total),0) FROM ventas WHERE fecha BETWEEN ? AND ?",
                    (arq['fecha_apertura'], ahora)).fetchone()
                conn.close()
                n_ventas = r[0] if r else 0
                total_v  = r[1] if r else 0
            except:
                n_ventas = 0; total_v = 0

            # Header verde
            hdr2 = tk.Frame(self._status_card, bg="#059669", pady=10)
            hdr2.pack(fill='x', pady=(0,12))
            tk.Label(hdr2, text="🔓  CAJA ABIERTA", font=(FONT,13,'bold'),
                     bg="#059669", fg="#fff").pack(anchor='w', padx=12)
            tk.Label(hdr2, text=f"Apertura: {fecha_ap}  ·  Turno de: {arq.get('usuario_nombre','')}",
                     font=(FONT,9), bg="#059669", fg="#A7F3D0").pack(anchor='w', padx=14, pady=(2,0))

            # KPIs en tiempo real
            kpi = tk.Frame(self._status_card, bg=THEME["card_bg"])
            kpi.pack(fill='x', pady=12)
            for i, (lbl, val, col) in enumerate([
                ("Ventas del turno",   str(n_ventas),           THEME["acc_blue"]),
                ("Total recaudado",    format_currency(total_v), THEME["acc_green"]),
                ("Monto inicial",      format_currency(arq.get('monto_inicial',0)), THEME["acc_amber"]),
            ]):
                c = tk.Frame(kpi, bg=THEME["card_border"]); c.grid(row=0,column=i,sticky='nsew',padx=4)
                ci = tk.Frame(c, bg=THEME["card_bg"], padx=10, pady=8); ci.pack(fill='both',padx=1,pady=1)
                tk.Label(ci, text=lbl, font=(FONT,8), bg=THEME["card_bg"], fg=THEME["txt_secondary"]).pack(anchor='w')
                tk.Label(ci, text=val, font=(FONT,12,'bold'), bg=THEME["card_bg"], fg=col).pack(anchor='w')
                kpi.columnconfigure(i, weight=1)

            self.btn_abrir.disable()
            self.btn_cerrar.enable()
        else:
            # Sin arqueo abierto
            hdr2 = tk.Frame(self._status_card, bg="#7F1D1D", pady=10)
            hdr2.pack(fill='x')
            tk.Label(hdr2, text="🔒  CAJA CERRADA", font=(FONT,13,'bold'),
                     bg="#7F1D1D", fg="#fff").pack(anchor='w')
            tk.Label(hdr2, text="No hay arqueo activo. Abrí la caja para comenzar a vender.",
                     font=(FONT,9), bg="#7F1D1D", fg="#FECACA").pack(anchor='w', pady=(2,0))
            tk.Label(self._status_card, text="Presioná \"Abrir Caja\" para iniciar el turno.",
                     font=(FONT,10), bg=THEME["card_bg"], fg=THEME["txt_secondary"]).pack(pady=20)
            self.btn_abrir.enable()
            self.btn_cerrar.disable()

    def _load_history(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        try:
            arqueos = self.db.get_arqueos(50)
        except: return
        for a in arqueos:
            ap = (a.get('fecha_apertura','') or '')[:16]
            ci = (a.get('fecha_cierre','')   or '—')[:16]
            estado = a.get('estado','')
            tag = 'abierto' if estado=='abierto' else 'cerrado'
            # Calcular total ventas (efectivo + tarjeta + transferencia)
            tot = (a.get('total_efectivo',0) or 0) + (a.get('total_tarjeta',0) or 0) + (a.get('total_transfer',0) or 0)
            self.tree.insert('','end', iid=str(a.get('id')), tags=(tag,), values=(
                a.get('id',''),
                ap, ci,
                a.get('total_ventas',0),
                format_currency(a.get('total_efectivo',0) or 0),
                format_currency(tot),
                estado.title()
            ))

    def _abrir_arqueo(self):
        """Diálogo para abrir caja."""
        # Verificar que no haya uno abierto
        if self.db.get_arqueo_abierto():
            messagebox.showinfo("Info","Ya hay un arqueo abierto."); return

        dlg = tk.Toplevel(self.parent)
        _set_icon(dlg); dlg.title("Abrir Caja")
        dlg.configure(bg=THEME["ct_bg"]); dlg.resizable(False,False)
        dlg.transient(self.parent); dlg.grab_set(); _center(dlg,420,280)

        btn_bar = tk.Frame(dlg, bg=THEME["card_bg"], padx=16, pady=12)
        btn_bar.pack(fill='x', side='bottom')
        tk.Frame(dlg, bg=THEME["card_border"], height=1).pack(fill='x', side='bottom')

        hdr = tk.Frame(dlg, bg="#059669", pady=12); hdr.pack(fill='x')
        tk.Label(hdr, text="🔓  Abrir Arqueo de Caja", font=(FONT,12,'bold'),
                 bg="#059669", fg="#fff").pack(anchor='w', padx=16)
        tk.Label(hdr, text=datetime.now().strftime("%d/%m/%Y %H:%M"),
                 font=(FONT,9), bg="#059669", fg="#A7F3D0").pack(anchor='w', padx=18)

        body = tk.Frame(dlg, bg=THEME["ct_bg"], padx=24, pady=16)
        body.pack(fill='both', expand=True)
        tk.Label(body, text="Monto inicial en caja (efectivo):",
                 font=(FONT,10,'bold'), bg=THEME["ct_bg"], fg=THEME["txt_secondary"]).pack(anchor='w', pady=(0,6))
        monto_e = _entry(body); monto_e.pack(fill='x'); monto_e.insert(0,"0"); monto_e.focus()

        def abrir():
            try:
                monto = float(monto_e.get().replace('.','').replace(',','') or 0)
            except:
                messagebox.showerror("Error","Ingrese un monto válido",parent=dlg); return
            self.db.abrir_arqueo(monto, self._usuario_nombre)
            messagebox.showinfo("✅","Caja abierta correctamente",parent=dlg)
            dlg.grab_release(); dlg.destroy()
            self._refresh()

        monto_e.bind('<Return>', lambda e: abrir())
        b1=_btn(btn_bar,"Abrir Caja",abrir,THEME["acc_green"],"🔓"); b1.pack(side='left',padx=(0,4),fill='x',expand=True)
        b2=_btn(btn_bar,"Cancelar",dlg.destroy,THEME["btn_secondary"],"✕"); b2.pack(side='left',fill='x',expand=True)

    def _cerrar_arqueo(self):
        """Diálogo para cerrar caja con resumen."""
        arq = self.db.get_arqueo_abierto()
        if not arq:
            messagebox.showinfo("Info","No hay arqueo abierto."); return

        # Calcular totales del turno
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            conn = self.db._conn()
            def _sum(metodo):
                r = conn.execute(
                    "SELECT COALESCE(SUM(total),0) FROM ventas WHERE fecha BETWEEN ? AND ? AND metodo_pago=?",
                    (arq['fecha_apertura'], ahora, metodo)).fetchone()
                return r[0] if r else 0
            ef = _sum('Efectivo')
            tc = _sum('Tarjeta Crédito') + _sum('Tarjeta Débito')
            tr = _sum('Transferencia')
            r2 = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(total),0) FROM ventas WHERE fecha BETWEEN ? AND ?",
                (arq['fecha_apertura'], ahora)).fetchone()
            conn.close()
            n_ventas = r2[0] if r2 else 0
            total_v  = r2[1] if r2 else 0
        except:
            ef = tc = tr = total_v = 0; n_ventas = 0

        dlg = tk.Toplevel(self.parent)
        _set_icon(dlg); dlg.title("Cerrar Caja")
        dlg.configure(bg=THEME["ct_bg"]); dlg.resizable(False,False)
        dlg.transient(self.parent); dlg.grab_set(); _center(dlg,460,560)

        btn_bar = tk.Frame(dlg, bg=THEME["card_bg"], padx=16, pady=12)
        btn_bar.pack(fill='x', side='bottom')
        tk.Frame(dlg, bg=THEME["card_border"], height=1).pack(fill='x', side='bottom')

        hdr = tk.Frame(dlg, bg="#7F1D1D", pady=12); hdr.pack(fill='x')
        tk.Label(hdr, text="🔒  Cerrar Arqueo de Caja", font=(FONT,12,'bold'),
                 bg="#7F1D1D", fg="#fff").pack(anchor='w', padx=16)
        tk.Label(hdr, text=f"Turno iniciado: {arq.get('fecha_apertura','')[:16]}",
                 font=(FONT,9), bg="#7F1D1D", fg="#FECACA").pack(anchor='w', padx=18)

        body = tk.Frame(dlg, bg=THEME["ct_bg"], padx=24, pady=12)
        body.pack(fill='both', expand=True)

        # Resumen del turno
        tk.Label(body, text="Resumen del Turno", font=(FONT,10,'bold'),
                 bg=THEME["ct_bg"], fg=THEME["acc_blue"]).pack(anchor='w', pady=(0,8))

        for lbl, val in [
            ("Ventas realizadas:",  str(n_ventas)),
            ("Efectivo:",           format_currency(ef)),
            ("Tarjeta:",            format_currency(tc)),
            ("Transferencia:",      format_currency(tr)),
            ("Total recaudado:",    format_currency(total_v)),
        ]:
            row = tk.Frame(body, bg=THEME["ct_bg"]); row.pack(fill='x', pady=2)
            tk.Label(row, text=lbl, font=(FONT,10), bg=THEME["ct_bg"],
                     fg=THEME["txt_secondary"], width=20, anchor='w').pack(side='left')
            is_total = "Total" in lbl
            tk.Label(row, text=val, font=(FONT,10,'bold' if is_total else 'normal'),
                     bg=THEME["ct_bg"],
                     fg=THEME["acc_green"] if is_total else THEME["txt_primary"]).pack(side='left')

        tk.Frame(body, bg=THEME["card_border"], height=1).pack(fill='x', pady=10)

        # Monto contado físicamente
        tk.Label(body, text="Efectivo contado en caja:", font=(FONT,10,'bold'),
                 bg=THEME["ct_bg"], fg=THEME["txt_secondary"]).pack(anchor='w', pady=(0,4))
        monto_e = _entry(body); monto_e.pack(fill='x'); monto_e.insert(0, str(int(ef)))
        monto_e.focus()

        # Diferencia en tiempo real
        dif_lbl = tk.Label(body, text="Diferencia: Gs. 0", font=(FONT,10,'bold'),
                           bg=THEME["ct_bg"], fg=THEME["acc_green"])
        dif_lbl.pack(anchor='w', pady=(6,0))

        def _calc_dif(*_):
            try:
                mf = float(monto_e.get().replace('.','').replace(',','') or 0)
                dif = mf - (arq.get('monto_inicial',0) + ef)
                color = THEME["acc_green"] if dif >= 0 else THEME["acc_rose"]
                signo = "+" if dif >= 0 else ""
                dif_lbl.config(text=f"Diferencia: {signo}{format_currency(abs(dif))} {'(sobrante)' if dif>0 else '(faltante)' if dif<0 else '(exacto)'}",
                                fg=color)
            except: pass
        monto_e._e.bind('<KeyRelease>', _calc_dif)
        _calc_dif()

        # Notas
        tk.Label(body, text="Observaciones (opcional):", font=(FONT,10,'bold'),
                 bg=THEME["ct_bg"], fg=THEME["txt_secondary"]).pack(anchor='w', pady=(10,4))
        nota_outer = tk.Frame(body, bg=THEME["input_brd"]); nota_outer.pack(fill='x')
        nota_inner = tk.Frame(nota_outer, bg=THEME["input_bg"]); nota_inner.pack(fill='x',padx=1,pady=1)
        nota_e = tk.Text(nota_inner, font=(FONT,10), bg=THEME["input_bg"], fg=THEME["txt_primary"],
                         relief='flat', bd=0, height=3, insertbackground=THEME["acc_blue"])
        nota_e.pack(fill='x', padx=10, pady=6)

        def cerrar():
            try:
                mf = float(monto_e.get().replace('.','').replace(',','') or 0)
            except:
                messagebox.showerror("Error","Ingrese un monto válido",parent=dlg); return
            notas = nota_e.get("1.0","end").strip()
            if not messagebox.askyesno("Confirmar",
                f"¿Cerrar el arqueo?\n\nEfectivo contado: {format_currency(mf)}\nTotal esperado: {format_currency(ef)}",
                parent=dlg): return
            self.db.cerrar_arqueo(arq['id'], mf, notas)
            messagebox.showinfo("✅","Arqueo cerrado correctamente",parent=dlg)
            dlg.grab_release(); dlg.destroy()
            self._refresh()

        b1=_btn(btn_bar,"Cerrar Caja",cerrar,THEME["btn_danger"],"🔒"); b1.pack(side='left',padx=(0,4),fill='x',expand=True)
        b2=_btn(btn_bar,"Cancelar",dlg.destroy,THEME["btn_secondary"],"✕"); b2.pack(side='left',fill='x',expand=True)

    def _ver_detalle(self, _=None):
        """Muestra detalle de un arqueo del historial."""
        sel = self.tree.selection()
        if not sel: return
        arq_id = int(sel[0])
        arq = self.db.get_arqueo_by_id(arq_id)
        if not arq: return

        dlg = tk.Toplevel(self.parent)
        _set_icon(dlg); dlg.title(f"Arqueo #{arq_id}")
        dlg.configure(bg=THEME["ct_bg"]); dlg.resizable(False,False)
        dlg.transient(self.parent); _center(dlg,420,440)

        btn_bar = tk.Frame(dlg, bg=THEME["card_bg"], padx=16, pady=12)
        btn_bar.pack(fill='x', side='bottom')
        tk.Frame(dlg, bg=THEME["card_border"], height=1).pack(fill='x', side='bottom')

        is_open = arq.get('estado')=='abierto'
        hdr_bg = "#059669" if is_open else THEME["sb_bg"]
        hdr = tk.Frame(dlg, bg=hdr_bg, pady=12); hdr.pack(fill='x')
        tk.Label(hdr, text=f"{'🔓' if is_open else '🔒'}  Arqueo #{arq_id} — {arq.get('estado','').title()}",
                 font=(FONT,12,'bold'), bg=hdr_bg, fg="#fff").pack(anchor='w', padx=16)
        tk.Label(hdr, text=f"Responsable: {arq.get('usuario_nombre','')}",
                 font=(FONT,9), bg=hdr_bg, fg="#A7F3D0" if is_open else "#94A3B8").pack(anchor='w', padx=18)

        body = tk.Frame(dlg, bg=THEME["ct_bg"], padx=24, pady=16)
        body.pack(fill='both', expand=True)

        tot = (arq.get('total_efectivo',0) or 0) + (arq.get('total_tarjeta',0) or 0) + (arq.get('total_transfer',0) or 0)
        dif = arq.get('diferencia',0) or 0

        rows = [
            ("Apertura:",          (arq.get('fecha_apertura','') or '')[:16]),
            ("Cierre:",            (arq.get('fecha_cierre','')   or '—')[:16]),
            ("Monto inicial:",     format_currency(arq.get('monto_inicial',0) or 0)),
            ("Monto final:",       format_currency(arq.get('monto_final',0) or 0)),
            ("—","—"),
            ("Total ventas:",      str(arq.get('total_ventas',0) or 0)),
            ("Efectivo:",          format_currency(arq.get('total_efectivo',0) or 0)),
            ("Tarjeta:",           format_currency(arq.get('total_tarjeta',0) or 0)),
            ("Transferencia:",     format_currency(arq.get('total_transfer',0) or 0)),
            ("Total recaudado:",   format_currency(tot)),
            ("—","—"),
            ("Diferencia:",        f"{'+' if dif>=0 else ''}{format_currency(dif)}"),
        ]
        for lbl, val in rows:
            if lbl == "—":
                tk.Frame(body, bg=THEME["card_border"], height=1).pack(fill='x', pady=6); continue
            row = tk.Frame(body, bg=THEME["ct_bg"]); row.pack(fill='x', pady=2)
            tk.Label(row, text=lbl, font=(FONT,9,'bold'), bg=THEME["ct_bg"],
                     fg=THEME["txt_secondary"], width=18, anchor='w').pack(side='left')
            col = THEME["acc_green"] if "Total" in lbl else (THEME["acc_rose"] if dif<0 and "Difer" in lbl else THEME["txt_primary"])
            tk.Label(row, text=val, font=(FONT,10), bg=THEME["ct_bg"], fg=col).pack(side='left')

        if arq.get('notas',''):
            tk.Label(body, text="Observaciones:", font=(FONT,9,'bold'),
                     bg=THEME["ct_bg"], fg=THEME["txt_secondary"]).pack(anchor='w', pady=(8,2))
            tk.Label(body, text=arq.get('notas',''), font=(FONT,9), bg=THEME["ct_bg"],
                     fg=THEME["txt_primary"], wraplength=360, justify='left').pack(anchor='w')

        bc = _btn(btn_bar,"Cerrar",dlg.destroy,THEME["btn_secondary"],"✕"); bc.enable(); bc.pack()


def check_arqueo_bloqueado(db, parent_root):
    """
    Reglas de bloqueo:
      1. Sin arqueo abierto → bloqueado (debe abrir caja primero)
      2. Arqueo de un día anterior sin cerrar → bloqueado (debe cerrarlo)
      3. Arqueo abierto del día actual → libre para vender
    Retorna True si está BLOQUEADO.
    """
    try:
        arq = db.get_arqueo_abierto()
        hoy = datetime.now().strftime('%Y-%m-%d')

        if not arq:
            # No hay ningún arqueo abierto → debe abrir la caja
            _mostrar_sin_arqueo(parent_root)
            return True

        fecha_apertura = (arq.get('fecha_apertura','') or '')[:10]
        if fecha_apertura and fecha_apertura < hoy:
            # Arqueo de día anterior sin cerrar → debe cerrarlo
            _mostrar_bloqueo(db, parent_root, arq)
            return True

        # Arqueo del día actual abierto → OK
        return False
    except:
        return False


def _mostrar_sin_arqueo(root):
    """Diálogo bloqueante cuando no hay arqueo abierto."""
    dlg = tk.Toplevel(root)
    _set_icon(dlg)
    dlg.title("🔒 Caja cerrada")
    dlg.configure(bg=THEME["ct_bg"])
    dlg.resizable(False, False)
    dlg.transient(root)
    dlg.grab_set()
    dlg.protocol("WM_DELETE_WINDOW", lambda: None)
    _center(dlg, 440, 260)

    hdr = tk.Frame(dlg, bg="#7F1D1D", pady=14); hdr.pack(fill='x')
    tk.Label(hdr, text="🔒  CAJA CERRADA", font=(FONT,14,'bold'),
             bg="#7F1D1D", fg="#fff").pack(anchor='w', padx=20)
    tk.Label(hdr, text="La caja no está abierta. No se pueden realizar ventas.",
             font=(FONT,9), bg="#7F1D1D", fg="#FECACA").pack(anchor='w', padx=22)

    body = tk.Frame(dlg, bg=THEME["ct_bg"], padx=28, pady=20)
    body.pack(fill='both', expand=True)
    msg = "Para comenzar a vender, un Administrador o Supervisor debe abrir el arqueo de caja primero."
    tk.Label(body, text=msg, font=(FONT,10), bg=THEME["ct_bg"], fg=THEME["txt_primary"],
             wraplength=380, justify='center').pack(pady=(0,10))

    btn_bar = tk.Frame(dlg, bg=THEME["card_bg"], padx=16, pady=12)
    btn_bar.pack(fill='x', side='bottom')
    tk.Frame(dlg, bg=THEME["card_border"], height=1).pack(fill='x', side='bottom')
    bc = _btn(btn_bar, "Entendido", dlg.destroy, THEME["btn_secondary"], "✓")
    bc.enable(); bc.pack()


def _mostrar_bloqueo(db, root, arq):
    """Muestra diálogo de bloqueo cuando hay arqueo vencido."""
    dlg = tk.Toplevel(root)
    _set_icon(dlg)
    dlg.title("⚠ Caja sin cerrar")
    dlg.configure(bg=THEME["ct_bg"])
    dlg.resizable(False, False)
    dlg.transient(root)
    dlg.grab_set()
    dlg.protocol("WM_DELETE_WINDOW", lambda: None)  # no se puede cerrar con X
    _center(dlg, 480, 380)

    # Header rojo urgente
    hdr = tk.Frame(dlg, bg="#7F1D1D", pady=14); hdr.pack(fill='x')
    tk.Label(hdr, text="🔒  CAJA SIN CERRAR", font=(FONT,14,'bold'),
             bg="#7F1D1D", fg="#fff").pack(anchor='w', padx=20)
    tk.Label(hdr, text="No se pueden realizar ventas hasta cerrar el arqueo anterior.",
             font=(FONT,9), bg="#7F1D1D", fg="#FECACA").pack(anchor='w', padx=22)

    body = tk.Frame(dlg, bg=THEME["ct_bg"], padx=24, pady=20)
    body.pack(fill='both', expand=True)

    fecha_arq = arq.get('fecha_apertura','')[:10]
    tk.Label(body,
             text=f"Existe un arqueo del {fecha_arq} que no fue cerrado.\n\n"
                  f"Para continuar vendiendo debés cerrar ese arqueo\n"
                  f"ingresando el monto de efectivo contado.",
             font=(FONT,10), bg=THEME["ct_bg"], fg=THEME["txt_primary"],
             justify='center').pack(pady=(0,16))

    # Formulario rápido de cierre
    tk.Label(body, text="Efectivo contado en caja:", font=(FONT,10,'bold'),
             bg=THEME["ct_bg"], fg=THEME["txt_secondary"]).pack(anchor='w', pady=(0,6))

    ef_outer = tk.Frame(body, bg=THEME["input_brd"]); ef_outer.pack(fill='x')
    ef_inner = tk.Frame(ef_outer, bg=THEME["input_bg"]); ef_inner.pack(fill='x', padx=1, pady=1)
    ef_e = tk.Entry(ef_inner, font=(FONT,13), bg=THEME["input_bg"], fg=THEME["txt_primary"],
                    relief='flat', bd=0, insertbackground=THEME["acc_blue"], justify='center')
    ef_e.pack(fill='x', padx=12, pady=10)
    ef_e.insert(0,"0"); ef_e.focus()

    nota_lbl = tk.Label(body, text="", font=(FONT,9), bg=THEME["ct_bg"], fg=THEME["acc_rose"])
    nota_lbl.pack(anchor='w', pady=(6,0))

    def cerrar_rapido():
        try:
            mf = float(ef_e.get().replace('.','').replace(',','') or 0)
        except:
            nota_lbl.config(text="⚠  Ingrese un monto válido"); return
        db.cerrar_arqueo(arq['id'], mf, "Cierre automático — arqueo vencido")
        dlg.grab_release(); dlg.destroy()
        messagebox.showinfo("✅ Listo",
            "Arqueo cerrado. Ahora podés abrir la caja del día y continuar vendiendo.")

    ef_e.bind('<Return>', lambda e: cerrar_rapido())

    btn_bar = tk.Frame(dlg, bg=THEME["card_bg"], padx=16, pady=12)
    btn_bar.pack(fill='x', side='bottom')
    tk.Frame(dlg, bg=THEME["card_border"], height=1).pack(fill='x', side='bottom')

    b1 = _btn(btn_bar, "Cerrar Arqueo Anterior", cerrar_rapido, THEME["btn_danger"], "🔒")
    b1.enable(); b1.pack(side='left')
