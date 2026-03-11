"""Módulo Gestión de Productos — Diseño moderno Venialgo POS"""
import tkinter as tk
try:
    from utils.window_icon import set_icon as _set_icon
except ImportError:
    def _set_icon(w): pass
from tkinter import ttk, messagebox
from config.settings import COLORS, FONTS as _F, SPACING, BUTTON_STYLES
from utils.validators import validate_required_field

THEME={"ct_bg":"#F9FAFB","card_bg":"#FFFFFF","card_border":"#E5E7EB","sb_bg":"#111827",
    "txt_primary":"#111827","txt_secondary":"#6B7280","txt_white":"#FFFFFF",
    "acc_blue":"#2563EB","acc_green":"#059669","acc_amber":"#D97706","acc_rose":"#E11D48",
    "btn_danger":"#DC2626","btn_secondary":"#6B7280",
    "input_bg":"#FFFFFF","input_brd":"#D1D5DB","input_foc":"#2563EB",
    "row_odd":"#F9FAFB","row_even":"#FFFFFF"}
FONT="Segoe UI"

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






def _entry(parent):
    outer=tk.Frame(parent,bg=THEME["input_brd"])
    inner=tk.Frame(outer,bg=THEME["input_bg"])
    inner.pack(fill='x',padx=1,pady=1)
    var=tk.StringVar()
    e=tk.Entry(inner,textvariable=var,font=(FONT,11),bg=THEME["input_bg"],
               fg=THEME["txt_primary"],relief='flat',bd=0,insertbackground=THEME["acc_blue"])
    e.pack(fill='x',padx=12,pady=8)
    e.bind('<FocusIn>',lambda _:outer.config(bg=THEME["input_foc"]))
    e.bind('<FocusOut>',lambda _:outer.config(bg=THEME["input_brd"]))
    outer.get=var.get; outer.set=lambda v:(var.set(v)); outer.focus=e.focus
    outer.delete=lambda a,b:e.delete(a,b); outer.insert=lambda a,b:e.insert(a,b)
    outer._e=e; outer._var=var
    return outer

def _setup_styles():
    s=ttk.Style()
    try: s.theme_use('clam')
    except: pass
    s.configure("POS.Treeview",background="#fff",foreground="#111827",
        fieldbackground="#fff",rowheight=34,font=(FONT,10),borderwidth=0)
    s.configure("POS.Treeview.Heading",background="#111827",foreground="#fff",
        font=(FONT,9,'bold'),relief='flat',padding=(8,6))
    s.map("POS.Treeview",background=[('selected','#2563EB')],foreground=[('selected','#fff')])

def _center(win,w,h):
    win.update_idletasks(); sw,sh=win.winfo_screenwidth(),win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

class ProductModule:
    def __init__(self,parent,db_manager,current_user=None):
        self.parent=parent; self.db=db_manager
        self.current_user = current_user or {}
        self._rol = self.current_user.get('rol','').lower()
        self._is_cajero = self._rol == 'cajero'
        self.selected_product_id=None; _setup_styles()
        self._build(); self.load_products()

    def _build(self):
        bg=THEME["ct_bg"]
        # Header
        hdr=tk.Frame(self.parent,bg=bg); hdr.pack(fill='x',padx=28,pady=(20,0))
        tk.Label(hdr,text="📦  Gestión de Productos",font=(FONT,16,'bold'),
                 bg=bg,fg=THEME["txt_primary"]).pack(side='left')
        tk.Frame(self.parent,bg=THEME["card_border"],height=1).pack(fill='x',padx=28,pady=(10,14))

        # Toolbar
        tb=tk.Frame(self.parent,bg=bg,padx=24); tb.pack(fill='x',pady=(0,10))
        # Búsqueda
        srch_outer=tk.Frame(tb,bg=THEME["input_brd"])
        srch_inner=tk.Frame(srch_outer,bg=THEME["input_bg"]); srch_inner.pack(fill='x',padx=1,pady=1)
        tk.Label(srch_inner,text="🔍",bg=THEME["input_bg"],fg=THEME["txt_secondary"],
                 font=(FONT,11)).pack(side='left',padx=(10,4))
        HINT_P = "Buscar por nombre, código o categoría..."
        self.search_var=tk.StringVar()
        srch_e=tk.Entry(srch_inner,textvariable=self.search_var,font=(FONT,11),
                        bg=THEME["input_bg"],fg=THEME["txt_secondary"],relief='flat',bd=0)
        srch_e.insert(0, HINT_P)
        srch_e.pack(fill='x',padx=4,pady=8,side='left',expand=True)
        def _pin(e,h=HINT_P):
            if srch_e.get()==h:
                srch_e.delete(0,'end'); srch_e.config(fg=THEME["txt_primary"])
            srch_outer.config(bg=THEME["input_foc"])
        def _pout(e,h=HINT_P):
            srch_outer.config(bg=THEME["input_brd"])
            if not srch_e.get():
                srch_e.insert(0,h); srch_e.config(fg=THEME["txt_secondary"])
        srch_e.bind('<FocusIn>',  _pin)
        srch_e.bind('<FocusOut>', _pout)
        def _smart_srch_p(*_):
            t = self.search_var.get()
            if t == HINT_P: return
            self.search_products()
        self.search_var.trace('w', _smart_srch_p)
        srch_outer.pack(side='left',fill='x',expand=True,padx=(0,12))
        if not self._is_cajero:
            _btn(tb,"Nuevo Producto",self.show_add_dialog,THEME["acc_blue"],"＋").pack(side='right')

        # Stats row
        stats=tk.Frame(self.parent,bg=bg,padx=24); stats.pack(fill='x',pady=(0,6))
        self.lbl_total=tk.Label(stats,text="Total: 0 productos",font=(FONT,9),
                                bg=bg,fg=THEME["txt_secondary"]); self.lbl_total.pack(side='left')
        self.lbl_search_hint=tk.Label(stats,
            text="  🔍 Busca por nombre, código o categoría",
            font=(FONT,8),bg=bg,fg=THEME["txt_secondary"])
        self.lbl_search_hint.pack(side='left',padx=(16,0))

        # Tabla
        tbl_outer=RoundedCard(self.parent,padx=0,pady=0,fill_mode=True)
        tbl_outer.pack(fill='both',expand=True,padx=24,pady=(0,10))
        tbl=tbl_outer.body
        cols=('ID','Nombre','Precio Contado','Costo','Stock','Categoría','Código')
        self.tree=ttk.Treeview(tbl,columns=cols,show='headings',style='POS.Treeview')
        for col,w in zip(cols,[45,220,120,110,70,120,110]):
            self.tree.heading(col,text=col)
            self.tree.column(col,width=w,anchor='w' if col in('Nombre','Categoría') else 'center')
        sb=ttk.Scrollbar(tbl,orient='vertical',command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side='right',fill='y',padx=(0,4),pady=4); self.tree.pack(fill='both',expand=True,padx=4,pady=4)
        self.tree.bind('<<TreeviewSelect>>',self._on_select)
        self.tree.bind('<Double-Button-1>',lambda _:self.show_edit_dialog())

        # Botones acción
        act=tk.Frame(self.parent,bg=bg,padx=24,pady=8); act.pack(fill='x')
        self.btn_edit=_btn(act,"Editar",self.show_edit_dialog,THEME["acc_amber"],"✏", width=110)
        self.btn_edit.disable(); self.btn_edit.pack(side='left',padx=(0,8))
        self.btn_del=_btn(act,"Eliminar",self.delete_product,THEME["btn_danger"],"🗑", width=110)
        self.btn_del.disable(); self.btn_del.pack(side='left')

    def load_products(self,search_term=''):
        for i in self.tree.get_children(): self.tree.delete(i)
        products=self.db.search_products(search_term) if search_term else self.db.get_all_products()
        from utils.formatters import format_currency
        for idx,p in enumerate(products):
            tag='odd' if idx%2 else 'even'
            self.tree.insert('','end',tags=(tag,),values=(
                p.get('id',''),p.get('name',p.get('nombre','')),
                format_currency(p.get('price',p.get('precio',0))),
                format_currency(p.get('cost',p.get('costo',0))),
                p.get('stock',p.get('quantity',0)),
                p.get('category',p.get('categoria','')),
                p.get('barcode',p.get('codigo',''))))
        self.tree.tag_configure('odd',background=THEME["row_odd"])
        self.tree.tag_configure('even',background=THEME["row_even"])
        if hasattr(self,'lbl_total'):
            self.lbl_total.config(text=f"Total: {len(products)} producto{'s' if len(products)!=1 else ''}")
        if hasattr(self,'lbl_search_hint'):
            if search_term:
                self.lbl_search_hint.config(
                    text=f"  🔍 Filtrando por: '{search_term}'",
                    fg=THEME["acc_blue"])
            else:
                self.lbl_search_hint.config(
                    text="  🔍 Busca por nombre, código o categoría",
                    fg=THEME["txt_secondary"])

    def search_products(self):
        term = self.search_var.get()
        if term.startswith("Buscar por"): return
        self.load_products(term)

    def _on_select(self,_=None):
        sel=self.tree.selection()
        if sel:
            self.selected_product_id=self.tree.item(sel[0])['values'][0]
            self.btn_edit.enable(); self.btn_del.enable()
        else:
            self.selected_product_id=None
            self.btn_edit.disable(); self.btn_del.disable()

    def _on_scan_code(self, event=None):
        """Lector de código: busca producto, si no existe abre diálogo con código precargado."""
        SCAN_HINT = "Escanear código..."
        code = self._scan_var.get().strip()
        if not code or code == SCAN_HINT: return
        # Buscar producto por código exacto
        p = self.db.get_product_by_code(code)
        if p:
            # Resaltar en la tabla
            for item in self.tree.get_children():
                vals = self.tree.item(item)['values']
                if str(vals[0]) == str(p.get('id', p.get('product_id',''))):
                    self.tree.selection_set(item)
                    self.tree.see(item)
                    self._on_select()
                    break
            self._scan_var.set("")
            # Feedback: mostrar nombre brevemente en el campo
            nombre = p.get('name', p.get('nombre',''))
            self._scan_var.set(f"✔ {nombre[:25]}")
            self.tree.after(1500, lambda: self._scan_var.set(""))
        else:
            # No existe: abrir diálogo de nuevo producto con código precargado
            from tkinter import messagebox
            if messagebox.askyesno("Producto no encontrado",
                f"Código '{code}' no registrado.\n\n¿Crear nuevo producto con este código?"):
                self._scan_var.set("")
                self._show_dialog('add', barcode_preset=code)
            else:
                self._scan_var.set("")

    def show_add_dialog(self): self._show_dialog('add')
    def show_edit_dialog(self):
        if self.selected_product_id: self._show_dialog('edit',self.selected_product_id)

    def _show_dialog(self,mode,product_id=None,barcode_preset=None):
        title="Nuevo Producto" if mode=='add' else "Editar Producto"
        dlg=tk.Toplevel(self.parent)
        _set_icon(dlg)
        _set_icon(dlg); dlg.title(title)
        dlg.configure(bg=THEME["ct_bg"]); dlg.resizable(False,True)
        dlg.transient(self.parent); dlg.grab_set(); _center(dlg,500,720)

        # Botones PRIMERO
        btn_bar=tk.Frame(dlg,bg=THEME["card_bg"],padx=16,pady=12)
        btn_bar.pack(fill='x',side='bottom')
        tk.Frame(dlg,bg=THEME["card_border"],height=1).pack(fill='x',side='bottom')

        # Header
        hdr=tk.Frame(dlg,bg=THEME["sb_bg"],pady=12); hdr.pack(fill='x')
        tk.Label(hdr,text=f"{'📦 Nuevo' if mode=='add' else '✏ Editar'} Producto",
                 font=(FONT,13,'bold'),bg=THEME["sb_bg"],fg="#fff").pack(anchor='w',padx=16)

        scroll_frame=tk.Frame(dlg,bg=THEME["ct_bg"])
        scroll_frame.pack(fill='both',expand=True)
        canvas=tk.Canvas(scroll_frame,bg=THEME["ct_bg"],highlightthickness=0)
        vsb=ttk.Scrollbar(scroll_frame,orient='vertical',command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right',fill='y')
        canvas.pack(side='left',fill='both',expand=True)
        body=tk.Frame(canvas,bg=THEME["ct_bg"],padx=24,pady=16)
        canvas.create_window((0,0),window=body,anchor='nw',tags='body')
        def _rsz(e): canvas.itemconfig('body',width=e.width)
        def _srg(e): canvas.configure(scrollregion=canvas.bbox('all'))
        canvas.bind('<Configure>',_rsz); body.bind('<Configure>',_srg)
        def _mwheel(e):
            try: canvas.yview_scroll(-1*(e.delta//120),'units')
            except Exception: pass
        canvas.bind('<Enter>',lambda e: canvas.bind_all('<MouseWheel>',_mwheel))
        canvas.bind('<Leave>',lambda e: canvas.unbind_all('<MouseWheel>'))

        fields={}
        def lbl_entry(key,label,required=False):
            row=tk.Frame(body,bg=THEME["ct_bg"]); row.pack(anchor='w',pady=(0,3))
            tk.Label(row,text=label,font=(FONT,9,'bold'),bg=THEME["ct_bg"],fg=THEME["txt_secondary"]).pack(side='left')
            if required: tk.Label(row,text=" *",font=(FONT,9,'bold'),bg=THEME["ct_bg"],fg=THEME["acc_rose"]).pack(side='left')
            e=_entry(body); e.pack(fill='x',pady=(0,12)); fields[key]=e

        lbl_entry('nombre','Nombre del Producto',required=True)
        lbl_entry('costo','Precio de Costo',required=True)
        lbl_entry('precio','Precio Contado')
        lbl_entry('stock','Stock Inicial')
        lbl_entry('categoria','Categoría')
        lbl_entry('codigo','Código de Barras  📷  (escanear con lector)')

        # ── Precios por modalidad ──────────────────────────────────
        prices_card = tk.Frame(body, bg=THEME["card_border"])
        prices_card.pack(fill='x', pady=(8,0))
        prices_inner = tk.Frame(prices_card, bg=THEME["card_bg"], padx=12, pady=10)
        prices_inner.pack(fill='x', padx=1, pady=1)

        hdr_row = tk.Frame(prices_inner, bg=THEME["card_bg"])
        hdr_row.pack(fill='x', pady=(0,6))
        tk.Label(hdr_row, text="Precios por modalidad",
                 font=(FONT,9,'bold'), bg=THEME["card_bg"],
                 fg=THEME["acc_blue"]).pack(side='left')
        tk.Label(hdr_row,
                 text="  ✏ Editá el % para personalizar esta modalidad en este producto",
                 font=(FONT,8), bg=THEME["card_bg"],
                 fg=THEME["txt_secondary"]).pack(side='left')

        # Cabecera de columnas
        col_hdr = tk.Frame(prices_inner, bg=THEME["ct_bg"], pady=4)
        col_hdr.pack(fill='x')
        col_hdr.columnconfigure(0, weight=2)
        col_hdr.columnconfigure(1, weight=0)
        col_hdr.columnconfigure(2, weight=0)
        col_hdr.columnconfigure(3, weight=0)
        col_hdr.columnconfigure(4, weight=0)
        for ci, (ct, an) in enumerate([
            ("Modalidad","w"), ("Cuotas","center"),
            ("% Global","center"), ("% Este prod.","center"), ("Precio Venta","center")
        ]):
            tk.Label(col_hdr, text=ct, font=(FONT,8,'bold'),
                     bg=THEME["ct_bg"], fg=THEME["txt_secondary"],
                     anchor=an, width=[18,6,9,11,12][ci]
                     ).grid(row=0, column=ci, padx=4, sticky="ew")

        rows_frame = tk.Frame(prices_inner, bg=THEME["card_bg"])
        rows_frame.pack(fill='x', pady=(2,0))

        # price_widgets: list of {config_id, v_pct (StringVar), chk_var, lbl_precio}
        price_widgets = []

        def _parse_costo():
            raw = fields['costo'].get().replace(",","").replace("Gs","").strip()
            try:    return float(raw)
            except: return 0.0

        def _build_price_rows(precios, overrides):
            """Crea/recrea todas las filas de modalidad."""
            for w in rows_frame.winfo_children():
                w.destroy()
            price_widgets.clear()

            from utils.formatters import format_currency
            for idx, p in enumerate(precios):
                cid      = p["id"]
                pct_base = p["pct_base"]
                has_ov   = p["tiene_custom"]
                bg_row   = THEME["card_bg"] if idx%2==0 else THEME["ct_bg"]

                frm = tk.Frame(rows_frame, bg=bg_row, pady=3)
                frm.pack(fill='x')
                frm.columnconfigure(0, weight=2)

                accent = THEME["acc_green"] if p["tipo"]=="contado" else THEME["acc_amber"]

                # Barra lateral color
                tk.Frame(frm, bg=accent, width=3).grid(row=0, column=0, sticky="ns", padx=(0,2))

                # Nombre
                tk.Label(frm, text=p["nombre"], font=(FONT,9), bg=bg_row,
                         fg=THEME["txt_primary"], anchor='w', width=18
                         ).grid(row=0, column=0, sticky="ew", padx=(6,4))

                # Cuotas
                tk.Label(frm, text=str(p["cuotas"]), font=(FONT,9),
                         bg=bg_row, fg=THEME["txt_secondary"],
                         anchor='center', width=6
                         ).grid(row=0, column=1, padx=4)

                # % Global (solo lectura, referencia)
                tk.Label(frm, text=f"{pct_base:.0f}%", font=(FONT,9),
                         bg=bg_row, fg=THEME["txt_secondary"],
                         anchor='center', width=9
                         ).grid(row=0, column=2, padx=4)

                # % Override (editable)
                v_pct = tk.StringVar(value=f"{p['porcentaje']:.1f}")
                is_custom = [has_ov]  # mutable flag

                pct_outer = tk.Frame(frm,
                    bg=THEME["acc_amber"] if has_ov else THEME["card_border"],
                    padx=2, pady=2)
                pct_outer.grid(row=0, column=3, padx=4)
                e_pct = tk.Entry(pct_outer, textvariable=v_pct,
                                 font=(FONT,9,'bold'),
                                 bg=THEME["input_bg"],
                                 fg=THEME["acc_amber"] if has_ov else THEME["txt_secondary"],
                                 relief='flat', bd=0, justify='center', width=8,
                                 insertbackground=THEME["acc_amber"])
                e_pct.pack(ipady=3, padx=2)

                # Indicador visual de personalizado
                badge_var = tk.StringVar(value="★ custom" if has_ov else "")
                badge_lbl = tk.Label(frm, textvariable=badge_var,
                                     font=(FONT,7), bg=bg_row,
                                     fg=THEME["acc_amber"])
                # (no grideamos badge, va inline junto al entry)

                # Precio calculado
                lbl_precio = tk.Label(frm,
                    text=format_currency(p["precio"]),
                    font=(FONT,9,'bold'), bg=bg_row,
                    fg=accent, anchor='center', width=12)
                lbl_precio.grid(row=0, column=4, padx=4)

                # Al editar %, actualizar precio en tiempo real y marcar como custom
                def _on_pct_change(*_, _v=v_pct, _lp=lbl_precio,
                                   _c=p["cuotas"], _pbase=pct_base,
                                   _outer=pct_outer, _entry=e_pct,
                                   _is=is_custom):
                    try:
                        pct  = float(_v.get().replace(",","."))
                        cost = _parse_costo()
                        prec = round(cost * (1 + pct/100), 0)
                        _lp.config(text=format_currency(prec))
                        _is[0] = (abs(pct - _pbase) > 0.01)
                        if _is[0]:
                            _outer.config(bg=THEME["acc_amber"])
                            _entry.config(fg=THEME["acc_amber"])
                        else:
                            _outer.config(bg=THEME["card_border"])
                            _entry.config(fg=THEME["txt_secondary"])
                    except Exception:
                        pass

                v_pct.trace_add("write", _on_pct_change)

                # Botón "Reset" al % global
                def _reset_pct(_v=v_pct, _pb=pct_base, _cb=_on_pct_change):
                    _v.set(f"{_pb:.1f}")
                tk.Button(frm, text="↺", font=(FONT,8),
                          bg=bg_row, fg=THEME["txt_secondary"],
                          relief='flat', cursor='hand2',
                          command=_reset_pct
                          ).grid(row=0, column=5, padx=(0,4))

                sep = tk.Frame(rows_frame, bg=THEME["card_border"], height=1)
                sep.pack(fill='x')

                price_widgets.append({
                    "config_id": cid,
                    "v_pct":     v_pct,
                    "pct_base":  pct_base,
                    "is_custom": is_custom,
                    "lbl":       lbl_precio,
                })

                # Actualizar precio contado en el campo principal
                if p["tipo"] == "contado":
                    fields['precio'].delete(0, 'end')
                    fields['precio'].insert(0, str(int(p["precio"])))

        def update_prices(*_):
            costo = _parse_costo()
            if costo <= 0: return
            pid = product_id if mode == 'edit' else None
            precios   = self.db.calcular_precios_producto(costo, producto_id=pid)
            overrides = self.db.get_custom_precios(pid) if pid else {}
            _build_price_rows(precios, overrides)

        fields['costo']._e.bind('<FocusOut>', update_prices)
        fields['costo']._e.bind('<Return>', update_prices)

        # Cargar datos si editar
        if mode=='edit' and product_id:
            p=self.db.get_product_by_id(product_id)
            if p:
                fields['nombre'].insert(0,p.get('name',p.get('nombre','')))
                fields['costo'].insert(0,str(p.get('cost',p.get('costo',0))))
                fields['precio'].insert(0,str(p.get('price',p.get('precio',0))))
                fields['stock'].insert(0,str(p.get('stock',p.get('quantity',0))))
                fields['categoria'].insert(0,p.get('category',p.get('categoria','')))
                fields['codigo'].insert(0,p.get('barcode',p.get('codigo','')))
                update_prices()
        # Precargar código si viene de scan
        if barcode_preset:
            fields['codigo'].delete(0,'end')
            fields['codigo'].insert(0, barcode_preset)
            fields['nombre'].focus()
        else:
            fields['nombre'].focus()

        # Enter en campo código → saltar a nombre (lector termina con Enter)
        def _scan_to_next(e):
            if fields['codigo'].get().strip():
                fields['nombre']._e.focus()
            return "break"
        try:
            fields['codigo']._e.bind('<Return>', _scan_to_next)
        except Exception:
            pass

        def save():
            ok,msg,nombre=validate_required_field(fields['nombre'].get(),"Nombre")
            if not ok: messagebox.showerror("Error",msg,parent=dlg); return
            try:
                costo=float(fields['costo'].get() or 0)
                precio=float(fields['precio'].get() or 0)
                stock=int(fields['stock'].get() or 0)
            except ValueError: messagebox.showerror("Error","Valores numéricos inválidos",parent=dlg); return
            cat=fields['categoria'].get().strip(); cod=fields['codigo'].get().strip()
            try:
                if mode=='add':
                    pid = self.db.add_product(nombre,precio,stock,cat,cod,costo=costo)
                else:
                    self.db.update_product(product_id,nombre,precio,stock,cat,cod,costo=costo)
                    pid = product_id

                # Guardar porcentajes personalizados por modalidad
                if price_widgets:
                    custom = {}
                    for pw in price_widgets:
                        try:
                            pct = float(pw["v_pct"].get().replace(",","."))
                            if abs(pct - pw["pct_base"]) > 0.01:
                                custom[pw["config_id"]] = pct
                        except Exception:
                            pass
                    if pid:
                        self.db.save_custom_precios(int(pid), custom)

                messagebox.showinfo("✅","Producto guardado correctamente",parent=dlg)
                self.load_products(); dlg.destroy()
            except Exception as e: messagebox.showerror("Error",str(e),parent=dlg)

        _btn(btn_bar,"Guardar",save,THEME["acc_green"],"💾").pack(side='left',padx=(0,4),fill='x',expand=True)
        _btn(btn_bar,"Cancelar",dlg.destroy,THEME["btn_secondary"],"✕").pack(side='left',fill='x',expand=True)

    def delete_product(self):
        if not self.selected_product_id: return
        if messagebox.askyesno("Confirmar","¿Eliminar este producto?"):
            try:
                self.db.delete_product(self.selected_product_id)
                messagebox.showinfo("✅","Producto eliminado")
                self.load_products(); self.selected_product_id=None
                self.btn_edit.disable(); self.btn_del.disable()
            except Exception as e: messagebox.showerror("Error",str(e))
