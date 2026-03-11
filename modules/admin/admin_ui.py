try:
    from utils.window_icon import set_icon as _set_icon
except ImportError:
    def _set_icon(w): pass

"""Módulo Administración/Configuración — Diseño moderno Venialgo POS"""
import tkinter as tk
from tkinter import ttk, messagebox
import hashlib
from database.db_manager import DatabaseManager

THEME={"ct_bg":"#F9FAFB","card_bg":"#FFFFFF","card_border":"#E5E7EB","sb_bg":"#111827",
    "txt_primary":"#111827","txt_secondary":"#6B7280","txt_white":"#FFFFFF",
    "acc_blue":"#2563EB","acc_green":"#059669","acc_amber":"#D97706","acc_rose":"#E11D48",
    "acc_purple":"#7C3AED","btn_danger":"#DC2626","btn_secondary":"#6B7280",
    "input_bg":"#FFFFFF","input_brd":"#D1D5DB","input_foc":"#2563EB",
    "row_odd":"#F9FAFB","row_even":"#FFFFFF","tab_active":"#2563EB","tab_inactive":"#E5E7EB"}
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






def _entry(parent,show=None):
    outer=tk.Frame(parent,bg=THEME["input_brd"])
    inner=tk.Frame(outer,bg=THEME["input_bg"]); inner.pack(fill='x',padx=1,pady=1)
    var=tk.StringVar()
    kw=dict(textvariable=var,font=(FONT,11),bg=THEME["input_bg"],
            fg=THEME["txt_primary"],relief='flat',bd=0,insertbackground=THEME["acc_blue"])
    if show: kw['show']=show
    e=tk.Entry(inner,**kw); e.pack(fill='x',padx=12,pady=8)
    e.bind('<FocusIn>',lambda _:outer.config(bg=THEME["input_foc"]))
    e.bind('<FocusOut>',lambda _:outer.config(bg=THEME["input_brd"]))
    outer.get=var.get; outer.set=lambda v:var.set(v)
    outer.delete=lambda a,b:e.delete(a,b); outer.insert=lambda a,b:e.insert(a,b)
    outer.focus=e.focus
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

def _ensure_tables(): DatabaseManager()._ensure_tables()

class AdminModule:
    TABS=[("🏢","Empresa"),("👤","Usuarios"),("🔐","Precios"),("🔑","Licencia")]

    def __init__(self,parent,db_manager,current_user=None,on_company_saved=None):
        self.parent=parent; self.db=db_manager
        self.current_user=current_user or {}; self.on_company_saved=on_company_saved
        self._active_tab=0; self._tab_btns=[]; self._tab_frames=[]
        _setup_styles(); self._build()

    def _build(self):
        bg=THEME["ct_bg"]
        # Header
        hdr=tk.Frame(self.parent,bg=bg); hdr.pack(fill='x',padx=28,pady=(20,0))
        tk.Label(hdr,text="⚙️  Configuración",font=(FONT,16,'bold'),
                 bg=bg,fg=THEME["txt_primary"]).pack(side='left')
        tk.Frame(self.parent,bg=THEME["card_border"],height=1).pack(fill='x',padx=28,pady=(10,14))

        # Tab bar
        tab_bar=tk.Frame(self.parent,bg=bg,padx=24); tab_bar.pack(fill='x',pady=(0,14))
        for i,(icon,label) in enumerate(self.TABS):
            btn=tk.Label(tab_bar,text=f"{icon}  {label}",font=(FONT,10,'bold'),
                         cursor='hand2',padx=20,pady=10)
            btn.pack(side='left',padx=2)
            btn.bind('<Button-1>',lambda e,idx=i:self._switch_tab(idx))
            self._tab_btns.append(btn)

        # Área de tabs
        self._tab_area=tk.Frame(self.parent,bg=bg)
        self._tab_area.pack(fill='both',expand=True,padx=24,pady=(0,20))

        # Crear frames de cada tab
        self._tab_frames=[
            self._build_empresa_tab,
            self._build_usuarios_tab,
            self._build_precios_tab,
            self._build_licencia_tab,
        ]
        self._switch_tab(0)

    def _switch_tab(self,idx):
        self._active_tab=idx
        for i,btn in enumerate(self._tab_btns):
            if i==idx: btn.config(bg=THEME["acc_blue"],fg=THEME["txt_white"])
            else: btn.config(bg=THEME["tab_inactive"],fg=THEME["txt_secondary"])
        for w in self._tab_area.winfo_children(): w.destroy()
        self._tab_frames[idx]()

    # ── TAB 1: EMPRESA ────────────────────────────────────────
    def _build_empresa_tab(self):
        import os, sqlite3, shutil
        from tkinter import filedialog

        # ── Scroll container para pantallas pequeñas ──────────────
        _cv = tk.Canvas(self._tab_area, bg=THEME["ct_bg"], highlightthickness=0)
        _sb = ttk.Scrollbar(self._tab_area, orient='vertical', command=_cv.yview)
        _cv.configure(yscrollcommand=_sb.set)
        _sb.pack(side='right', fill='y')
        _cv.pack(side='left', fill='both', expand=True)
        _page = tk.Frame(_cv, bg=THEME["ct_bg"])
        _win_id = _cv.create_window((0,0), window=_page, anchor='nw')
        def _on_cv_resize(e): _cv.itemconfig(_win_id, width=e.width)
        def _on_page_resize(e): _cv.configure(scrollregion=_cv.bbox('all'))
        _cv.bind('<Configure>', _on_cv_resize)
        _page.bind('<Configure>', _on_page_resize)
        def _mwheel(e):
            try: _cv.yview_scroll(-1*(e.delta//120),'units')
            except Exception: pass
        _cv.bind('<Enter>', lambda e: _cv.bind_all('<MouseWheel>', _mwheel))
        _cv.bind('<Leave>', lambda e: _cv.unbind_all('<MouseWheel>'))

        outer=RoundedCard(_page,padx=28,pady=24,fill_mode=False)
        outer.pack(fill='x',expand=False,pady=(0,16))
        card=outer.body

        tk.Label(card,text="Datos de la Empresa",font=(FONT,13,'bold'),
                 bg=THEME["card_bg"],fg=THEME["txt_primary"]).pack(anchor='w',pady=(0,16))
        tk.Frame(card,bg=THEME["card_border"],height=1).pack(fill='x',pady=(0,16))

        try:
            from utils.company_header import get_company
            co=get_company()
        except: co={}

        # ── Sección logo ──────────────────────────────────────────
        logo_section=tk.Frame(card,bg=THEME["card_bg"])
        logo_section.pack(fill='x',pady=(0,20))

        # Panel izquierdo: preview
        preview_frame=tk.Frame(logo_section,bg=THEME["ct_bg"],
                               width=130,height=90,relief='groove',bd=1)
        preview_frame.pack(side='left',padx=(0,20))
        preview_frame.pack_propagate(False)

        self._logo_preview_lbl=tk.Label(preview_frame,bg=THEME["ct_bg"],
                                         text="Sin logo",font=(FONT,9),
                                         fg=THEME["txt_secondary"])
        self._logo_preview_lbl.pack(expand=True)
        self._logo_photo_ref=None

        def _refresh_logo_preview(path=""):
            """Carga y muestra el logo en el preview."""
            if not path:
                path=co.get("logo_path","")
            if path and os.path.isfile(path):
                try:
                    from PIL import Image, ImageTk
                    img=Image.open(path).convert("RGBA")
                    img.thumbnail((126,86),Image.LANCZOS)
                    # fondo blanco para PNG con transparencia
                    bg_img=Image.new("RGBA",(126,86),(240,242,245,255))
                    ox=(126-img.width)//2; oy=(86-img.height)//2
                    bg_img.paste(img,(ox,oy),img)
                    photo=ImageTk.PhotoImage(bg_img.convert("RGB"))
                    self._logo_photo_ref=photo
                    self._logo_preview_lbl.config(image=photo,text="")
                    return
                except Exception:
                    pass
            self._logo_photo_ref=None
            self._logo_preview_lbl.config(image="",text="Sin logo")

        _refresh_logo_preview()

        # Panel derecho: botones y nombre de archivo
        logo_right=tk.Frame(logo_section,bg=THEME["card_bg"])
        logo_right.pack(side='left',fill='both',expand=True)

        tk.Label(logo_right,text="Logo de la Empresa",font=(FONT,10,'bold'),
                 bg=THEME["card_bg"],fg=THEME["txt_primary"]).pack(anchor='w')
        tk.Label(logo_right,text="Formatos: PNG, JPG, WEBP · Recomendado: fondo transparente",
                 font=(FONT,8),bg=THEME["card_bg"],fg=THEME["txt_secondary"]).pack(anchor='w',pady=(2,10))

        self._logo_path_var=tk.StringVar(value=co.get("logo_path",""))
        lbl_path=tk.Label(logo_right,textvariable=self._logo_path_var,
                          font=(FONT,8),bg=THEME["card_bg"],fg=THEME["acc_blue"],
                          wraplength=260,justify='left',cursor='hand2')
        lbl_path.pack(anchor='w',pady=(0,8))

        def _choose_logo():
            path=filedialog.askopenfilename(
                title="Seleccionar logo",
                filetypes=[("Imágenes","*.png *.jpg *.jpeg *.webp *.bmp"),
                           ("Todos","*.*")])
            if not path: return
            # Copiar a assets/ para portabilidad
            try:
                assets_dir=os.path.join(os.path.dirname(
                    os.path.abspath(__file__)),"..","..","assets")
                os.makedirs(assets_dir,exist_ok=True)
                ext=os.path.splitext(path)[1].lower()
                dest=os.path.join(assets_dir,"company_logo"+ext)
                shutil.copy2(path,dest)
                path=os.path.abspath(dest)
            except Exception:
                pass  # si falla la copia, usar ruta original
            self._logo_path_var.set(path)
            _refresh_logo_preview(path)

        def _remove_logo():
            self._logo_path_var.set("")
            _refresh_logo_preview("")

        btn_logo_row=tk.Frame(logo_right,bg=THEME["card_bg"])
        btn_logo_row.pack(anchor='w')
        _btn(btn_logo_row,"Subir logo",_choose_logo,THEME["acc_blue"],"🖼").pack(side='left',padx=(0,4),fill='x',expand=True)
        _btn(btn_logo_row,"Quitar",_remove_logo,THEME["btn_secondary"],"✕").pack(side='left',fill='x',expand=True)

        # ── Separador ────────────────────────────────────────────
        tk.Frame(card,bg=THEME["card_border"],height=1).pack(fill='x',pady=(0,16))

        # ── Campos de texto ───────────────────────────────────────
        fields={}
        labels=[("razon_social","Razón Social / Nombre *"),("ruc","RUC / RUC-DV"),
                ("direccion","Dirección"),("ciudad","Ciudad / Departamento"),
                ("telefono","Teléfono"),("email","Email"),("web","Sitio Web")]

        form=tk.Frame(card,bg=THEME["card_bg"])
        form.pack(fill='x')
        form.columnconfigure(0,weight=1); form.columnconfigure(1,weight=1)

        for i,(key,lbl) in enumerate(labels):
            row,col=divmod(i,2)
            cell=tk.Frame(form,bg=THEME["card_bg"],padx=8,pady=4)
            cell.grid(row=row,column=col,sticky='ew')
            tk.Label(cell,text=lbl,font=(FONT,9,'bold'),bg=THEME["card_bg"],
                     fg=THEME["txt_secondary"]).pack(anchor='w',pady=(0,3))
            e=_entry(cell); e.pack(fill='x')
            if co.get(key): e.insert(0,str(co.get(key,'')))
            fields[key]=e

        # ── Guardar ───────────────────────────────────────────────
        def save_company():
            data={k:fields[k].get().strip() for k in fields}
            data["logo_path"]=self._logo_path_var.get().strip()
            if not data.get('razon_social'):
                messagebox.showerror("Error","Razón Social es requerida"); return
            try:
                # Migrar esquema: agregar columnas que puedan faltar en BD antigua
                _extra_cols = {
                    "ciudad":    "TEXT DEFAULT ''",
                    "email":     "TEXT DEFAULT ''",
                    "web":       "TEXT DEFAULT ''",
                    "logo_path": "TEXT DEFAULT ''",
                }
                with self.db._conn() as _mc:
                    _existing = [r[1] for r in
                                 _mc.execute("PRAGMA table_info(empresa)").fetchall()]
                    for _col, _typedef in _extra_cols.items():
                        if _col not in _existing:
                            _mc.execute(
                                f"ALTER TABLE empresa ADD COLUMN {_col} {_typedef}")
                    _mc.commit()

                # Construir UPDATE solo con columnas que existen en la BD
                with self.db._conn() as _mc:
                    _cols = [r[1] for r in
                             _mc.execute("PRAGMA table_info(empresa)").fetchall()]
                    _mapping = {
                        "razon_social": data.get("razon_social",""),
                        "ruc":          data.get("ruc",""),
                        "telefono":     data.get("telefono",""),
                        "direccion":    data.get("direccion",""),
                        "ciudad":       data.get("ciudad",""),
                        "email":        data.get("email",""),
                        "web":          data.get("web",""),
                        "logo_path":    data.get("logo_path",""),
                        "correo":       data.get("email",""),  # alias legacy
                    }
                    # Filtrar solo columnas que existen
                    _save = {k:v for k,v in _mapping.items() if k in _cols}
                    _set  = ", ".join(f"{k}=?" for k in _save)
                    _vals = list(_save.values())
                    _mc.execute(f"UPDATE empresa SET {_set} WHERE id=1", _vals)
                    _mc.commit()

                messagebox.showinfo("✅","Datos de empresa guardados correctamente")
                if self.on_company_saved: self.on_company_saved()
            except Exception as ex:
                messagebox.showerror("Error al guardar", str(ex))

        btn_row=tk.Frame(card,bg=THEME["card_bg"]); btn_row.pack(anchor='w',pady=(20,0))
        _btn(btn_row,"Guardar Datos",save_company,THEME["acc_green"],"💾").pack(side='left')

    # ── TAB 2: USUARIOS ───────────────────────────────────────
    def _build_usuarios_tab(self):
        # ── Scroll container ──────────────────────────────────────
        _cv = tk.Canvas(self._tab_area, bg=THEME["ct_bg"], highlightthickness=0)
        _sb = ttk.Scrollbar(self._tab_area, orient='vertical', command=_cv.yview)
        _cv.configure(yscrollcommand=_sb.set)
        _sb.pack(side='right', fill='y')
        _cv.pack(side='left', fill='both', expand=True)
        _page = tk.Frame(_cv, bg=THEME["ct_bg"])
        _win_id = _cv.create_window((0,0), window=_page, anchor='nw')
        def _on_cv_resize(e): _cv.itemconfig(_win_id, width=e.width)
        def _on_page_resize(e): _cv.configure(scrollregion=_cv.bbox('all'))
        _cv.bind('<Configure>', _on_cv_resize)
        _page.bind('<Configure>', _on_page_resize)
        def _mwheel(e):
            try: _cv.yview_scroll(-1*(e.delta//120),'units')
            except Exception: pass
        _cv.bind('<Enter>', lambda e: _cv.bind_all('<MouseWheel>', _mwheel))
        _cv.bind('<Leave>', lambda e: _cv.unbind_all('<MouseWheel>'))

        outer=tk.Frame(_page,bg=THEME["card_border"])
        outer.pack(fill='x',expand=False)
        card=tk.Frame(outer,bg=THEME["card_bg"]); card.pack(fill='x',expand=False,padx=1,pady=1)

        tb=tk.Frame(card,bg=THEME["card_bg"],padx=16,pady=12); tb.pack(fill='x')
        tk.Label(tb,text="Gestión de Usuarios",font=(FONT,13,'bold'),
                 bg=THEME["card_bg"],fg=THEME["txt_primary"]).pack(side='left')
        _btn(tb,"Nuevo Usuario",self._show_add_user,THEME["acc_blue"],"＋").pack(side='right')
        tk.Frame(card,bg=THEME["card_border"],height=1).pack(fill='x')

        cols=('ID','Usuario','Nombre','Rol','Estado')
        self.user_tree=ttk.Treeview(card,columns=cols,show='headings',
                                    height=12,style='POS.Treeview')
        for col,w in zip(cols,[50,140,200,120,80]):
            self.user_tree.heading(col,text=col)
            self.user_tree.column(col,width=w,anchor='center' if col in('ID','Estado') else 'w')
        usb=ttk.Scrollbar(card,orient='vertical',command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=usb.set)
        usb.pack(side='right',fill='y',padx=(0,4),pady=4)
        self.user_tree.pack(fill='both',expand=True,padx=4,pady=4)
        self.user_tree.tag_configure('active',foreground=THEME["acc_green"])
        self.user_tree.tag_configure('inactive',foreground=THEME["acc_rose"])

        act=tk.Frame(card,bg=THEME["card_bg"],padx=12,pady=10); act.pack(fill='x')
        _btn(act,"Editar",lambda:self._show_edit_user(),THEME["acc_amber"],"✏").pack(side='left',padx=(0,8))
        _btn(act,"Activar/Desactivar",lambda:self._toggle_user(),THEME["btn_secondary"],"⏻").pack(side='left',padx=(0,8))
        _btn(act,"Eliminar",lambda:self._delete_user(),THEME["btn_danger"],"🗑").pack(side='left')

        self._load_users()

    def _load_users(self):
        for i in self.user_tree.get_children(): self.user_tree.delete(i)
        users=self.db.get_all_users()
        for idx,u in enumerate(users):
            active=u.get('activo',u.get('active',1))
            tag='active' if active else 'inactive'
            self.user_tree.insert('','end',tags=(tag,),values=(
                u.get('id',''),u.get('usuario',u.get('username','')),
                u.get('nombre',u.get('name','')),
                u.get('rol',u.get('role','')),'Activo' if active else 'Inactivo'))

    def _show_add_user(self): self._user_dialog('add')
    def _show_edit_user(self):
        sel=self.user_tree.selection()
        if not sel: return
        uid=self.user_tree.item(sel[0])['values'][0]
        self._user_dialog('edit',uid)

    def _user_dialog(self,mode,user_id=None):
        title="Nuevo Usuario" if mode=='add' else "Editar Usuario"
        dlg=tk.Toplevel(self.parent)
        _set_icon(dlg); dlg.title(title)
        dlg.configure(bg=THEME["ct_bg"]); dlg.resizable(False,False)
        dlg.transient(self.parent); dlg.grab_set(); _center(dlg,440,540)

        btn_bar=tk.Frame(dlg,bg=THEME["card_bg"],padx=16,pady=12)
        btn_bar.pack(fill='x',side='bottom')
        tk.Frame(dlg,bg=THEME["card_border"],height=1).pack(fill='x',side='bottom')

        hdr=tk.Frame(dlg,bg=THEME["sb_bg"],pady=12); hdr.pack(fill='x')
        tk.Label(hdr,text=f"{'👤 Nuevo' if mode=='add' else '✏ Editar'} Usuario",
                 font=(FONT,13,'bold'),bg=THEME["sb_bg"],fg="#fff").pack(anchor='w',padx=16)

        # Canvas con scroll para que siempre sea visible todo el contenido
        canvas=tk.Canvas(dlg,bg=THEME["ct_bg"],highlightthickness=0)
        canvas.pack(fill='both',expand=True)
        body=tk.Frame(canvas,bg=THEME["ct_bg"],padx=24,pady=16)
        canvas.create_window((0,0),window=body,anchor='nw',tags='body')
        def _resize(e): canvas.itemconfig('body',width=e.width)
        def _scrollrgn(e): canvas.configure(scrollregion=canvas.bbox('all'))
        canvas.bind('<Configure>',_resize); body.bind('<Configure>',_scrollrgn)

        fields={}
        for key,lbl in [('nombre','Nombre completo'),('usuario','Nombre de usuario'),
                        ('password','Contraseña'),('password2','Confirmar contraseña')]:
            tk.Label(body,text=lbl,font=(FONT,9,'bold'),bg=THEME["ct_bg"],
                     fg=THEME["txt_secondary"]).pack(anchor='w',pady=(0,3))
            e=_entry(body,show='●' if 'password' in key else None)
            e.pack(fill='x',pady=(0,10)); fields[key]=e

        tk.Label(body,text="Rol",font=(FONT,9,'bold'),bg=THEME["ct_bg"],
                 fg=THEME["txt_secondary"]).pack(anchor='w',pady=(0,6))
        rol_var=tk.StringVar(value='Cajero')
        rol_f=tk.Frame(body,bg=THEME["ct_bg"]); rol_f.pack(fill='x',pady=(0,8))
        for rol in ['Administrador','Supervisor','Cajero']:
            tk.Radiobutton(rol_f,text=rol,variable=rol_var,value=rol,
               font=(FONT,10),bg=THEME["ct_bg"],selectcolor=THEME["ct_bg"]).pack(side='left',padx=(0,12))

        if mode=='edit' and user_id:
            u=self.db.get_user_by_id(user_id)
            if u:
                fields['nombre'].insert(0,u.get('nombre',u.get('name','')))
                fields['usuario'].insert(0,u.get('usuario',u.get('username','')))
                rol_var.set(u.get('rol',u.get('role','Cajero')))
        fields['nombre'].focus()

        def save():
            nombre=fields['nombre'].get().strip(); usuario=fields['usuario'].get().strip()
            pwd=fields['password'].get(); pwd2=fields['password2'].get()
            if not nombre or not usuario:
                messagebox.showerror("Error","Nombre y usuario son requeridos",parent=dlg); return
            if mode=='add' and not pwd:
                messagebox.showerror("Error","Ingrese una contraseña",parent=dlg); return
            if pwd and pwd!=pwd2:
                messagebox.showerror("Error","Las contraseñas no coinciden",parent=dlg); return
            try:
                hpwd=hashlib.sha256(pwd.encode()).hexdigest() if pwd else None
                if mode=='add': self.db.add_user(nombre,usuario,hpwd,rol_var.get())
                else: self.db.update_user(user_id,nombre,usuario,hpwd,rol_var.get())
                messagebox.showinfo("✅","Usuario guardado correctamente",parent=dlg)
                self._load_users(); dlg.destroy()
            except Exception as e: messagebox.showerror("Error",str(e),parent=dlg)

        _btn(btn_bar,"Guardar",save,THEME["acc_green"],"💾").pack(side='left',padx=(0,4),fill='x',expand=True)
        _btn(btn_bar,"Cancelar",dlg.destroy,THEME["btn_secondary"],"✕").pack(side='left',fill='x',expand=True)

    def _toggle_user(self):
        sel=self.user_tree.selection()
        if not sel: return
        uid=self.user_tree.item(sel[0])['values'][0]
        try:
            self.db.toggle_user_active(uid)
            self._load_users()
        except Exception as e: messagebox.showerror("Error",str(e))

    def _delete_user(self):
        sel=self.user_tree.selection()
        if not sel: return
        vals=self.user_tree.item(sel[0])['values']
        uid, uname = vals[0], vals[1]
        if str(uname).lower() == 'admin':
            messagebox.showerror("Error","No se puede eliminar el usuario admin principal.")
            return
        if not messagebox.askyesno("Confirmar eliminación",
            f"¿Eliminar al usuario '{uname}'?\n\nEsta acción no se puede deshacer."):
            return
        try:
            self.db.delete_user(uid)
            self._load_users()
            messagebox.showinfo("✅","Usuario eliminado correctamente.")
        except Exception as e:
            messagebox.showerror("Error",str(e))

    # ── TAB 3: PRECIOS / CUOTAS ─────────────────────────────
    def _build_precios_tab(self):
        # ── Scroll container ──────────────────────────────────
        _cv = tk.Canvas(self._tab_area, bg=THEME["ct_bg"], highlightthickness=0)
        _sb = ttk.Scrollbar(self._tab_area, orient="vertical", command=_cv.yview)
        _cv.configure(yscrollcommand=_sb.set)
        _sb.pack(side="right", fill="y")
        _cv.pack(side="left", fill="both", expand=True)
        _page = tk.Frame(_cv, bg=THEME["ct_bg"])
        _win_id = _cv.create_window((0,0), window=_page, anchor="nw")
        def _on_cv_resize(e): _cv.itemconfig(_win_id, width=e.width)
        def _on_page_resize(e): _cv.configure(scrollregion=_cv.bbox("all"))
        _cv.bind("<Configure>", _on_cv_resize)
        _page.bind("<Configure>", _on_page_resize)
        def _mwheel(e):
            try: _cv.yview_scroll(-1*(e.delta//120), "units")
            except Exception: pass
        _cv.bind("<Enter>", lambda e: _cv.bind_all("<MouseWheel>", _mwheel))
        _cv.bind("<Leave>", lambda e: _cv.unbind_all("<MouseWheel>"))

        # ── Card principal ────────────────────────────────────
        outer = tk.Frame(_page, bg=THEME["card_border"])
        outer.pack(fill="x", padx=0, pady=0)
        card = tk.Frame(outer, bg=THEME["card_bg"], padx=28, pady=24)
        card.pack(fill="x", padx=1, pady=1)

        tk.Label(card, text="Configuración de Precios y Cuotas",
                 font=(FONT,13,"bold"), bg=THEME["card_bg"],
                 fg=THEME["txt_primary"]).pack(anchor="w", pady=(0,4))
        tk.Label(card,
                 text="Defina el porcentaje de recargo para cada modalidad de cuotas. "
                      "Cada fila puede tener su propio porcentaje independiente.",
                 font=(FONT,9), bg=THEME["card_bg"],
                 fg=THEME["txt_secondary"], wraplength=560, justify="left"
                 ).pack(anchor="w", pady=(0,14))
        tk.Frame(card, bg=THEME["card_border"], height=1).pack(fill="x", pady=(0,18))

        # Colores por tipo
        TYPE_COLORS = {"contado": THEME["acc_green"], "credito": THEME["acc_amber"]}

        # ── Cabecera de tabla ─────────────────────────────────
        hdr = tk.Frame(card, bg=THEME["ct_bg"], pady=6)
        hdr.pack(fill="x")
        hdr.columnconfigure(0, weight=2)
        hdr.columnconfigure(1, weight=1)
        hdr.columnconfigure(2, weight=1)
        hdr.columnconfigure(3, weight=1)
        hdr.columnconfigure(4, weight=0)
        for col, (txt, anchor) in enumerate([
            ("Nombre / Descripción", "w"),
            ("Tipo", "center"),
            ("Cuotas", "center"),
            ("Recargo %", "center"),
            ("", "center"),
        ]):
            tk.Label(hdr, text=txt, font=(FONT,9,"bold"),
                     bg=THEME["ct_bg"], fg=THEME["txt_secondary"],
                     anchor=anchor).grid(row=0, column=col, sticky="ew", padx=6, pady=4)

        # ── Contenedor de filas ────────────────────────────────
        rows_frame = tk.Frame(card, bg=THEME["card_bg"])
        rows_frame.pack(fill="x", pady=(2,0))

        # Almacén de filas activas: lista de dicts con widgets y data
        self._price_rows = []

        TIPO_OPTS  = ["contado", "credito"]
        CUOTA_OPTS = [str(n) for n in [1,2,3,4,5,6,9,12,18,24,36,48]]

        def _add_row(data=None, flash=False):
            """Agrega una fila editable a la tabla."""
            d = data or {"id": None, "nombre": "Nueva modalidad",
                         "tipo": "credito", "cuotas": 1,
                         "porcentaje": 0.0, "activo": 1}

            row_bg = THEME["card_bg"]
            accent = TYPE_COLORS.get(d.get("tipo","credito"), THEME["acc_amber"])

            frm = tk.Frame(rows_frame, bg=row_bg, pady=4)
            frm.pack(fill="x")
            frm.columnconfigure(0, weight=2)
            frm.columnconfigure(1, weight=1)
            frm.columnconfigure(2, weight=1)
            frm.columnconfigure(3, weight=1)
            frm.columnconfigure(4, weight=0)

            # Barra de color según tipo
            bar_color = TYPE_COLORS.get(d.get("tipo","credito"), THEME["acc_amber"])
            bar = tk.Frame(frm, bg=bar_color, width=4)
            bar.grid(row=0, column=0, sticky="ns", padx=(0,0))

            # ── Nombre ────────────────────────────────────────
            v_nombre = tk.StringVar(value=str(d.get("nombre","")))
            e_nombre = tk.Entry(frm, textvariable=v_nombre,
                                font=(FONT,10), bg=THEME["input_bg"],
                                fg=THEME["txt_primary"], relief="flat",
                                bd=0, insertbackground=THEME["txt_primary"])
            e_nombre.grid(row=0, column=0, sticky="ew", padx=(8,4), ipady=5)

            # ── Tipo ──────────────────────────────────────────
            v_tipo = tk.StringVar(value=str(d.get("tipo","credito")))
            cb_tipo = ttk.Combobox(frm, textvariable=v_tipo,
                                   values=TIPO_OPTS, state="readonly",
                                   font=(FONT,9), width=9)
            cb_tipo.grid(row=0, column=1, padx=4, sticky="ew", ipady=3)

            def _on_tipo_change(*_, _bar=bar, _v=v_tipo):
                c = TYPE_COLORS.get(_v.get(), THEME["acc_amber"])
                _bar.config(bg=c)
            v_tipo.trace_add("write", _on_tipo_change)

            # ── Cuotas ────────────────────────────────────────
            v_cuotas = tk.StringVar(value=str(d.get("cuotas",1)))
            cb_cuotas = ttk.Combobox(frm, textvariable=v_cuotas,
                                     values=CUOTA_OPTS, font=(FONT,9), width=7)
            cb_cuotas.grid(row=0, column=2, padx=4, sticky="ew", ipady=3)

            # ── Porcentaje ────────────────────────────────────
            v_pct = tk.StringVar(value=str(d.get("porcentaje",0)))
            pct_outer = tk.Frame(frm, bg=accent, padx=2, pady=2)
            pct_outer.grid(row=0, column=3, padx=4, sticky="ew")
            e_pct = tk.Entry(pct_outer, textvariable=v_pct,
                             font=(FONT,11,"bold"), bg=THEME["input_bg"],
                             fg=accent, relief="flat", bd=0,
                             insertbackground=accent, justify="center", width=8)
            e_pct.pack(fill="x", ipady=4)

            # ── Botón eliminar ────────────────────────────────
            row_ref = [None]   # forward reference
            def _del_row(_r=row_ref):
                r = _r[0]
                if r and messagebox.askyesno("Eliminar", f"¿Eliminar '{r["v_nombre"].get()}'?"):
                    pid = r.get("id")
                    if pid:
                        try: self.db.delete_pricing_config(pid)
                        except Exception: pass
                    r["frame"].destroy()
                    self._price_rows.remove(r)

            btn_del = tk.Button(frm, text="✕", font=(FONT,9,"bold"),
                                bg=THEME["acc_rose"], fg="white",
                                relief="flat", cursor="hand2", width=3,
                                command=_del_row)
            btn_del.grid(row=0, column=4, padx=(4,0), pady=2)

            # Separador
            sep = tk.Frame(rows_frame, bg=THEME["card_border"], height=1)
            sep.pack(fill="x")

            row_data = {
                "id":       d.get("id"),
                "frame":    frm,
                "sep":      sep,
                "v_nombre": v_nombre,
                "v_tipo":   v_tipo,
                "v_cuotas": v_cuotas,
                "v_pct":    v_pct,
            }
            row_ref[0] = row_data
            self._price_rows.append(row_data)

            if flash:
                frm.config(bg="#fef9c3")
                frm.after(800, lambda: frm.config(bg=row_bg) if frm.winfo_exists() else None)

        # ── Cargar datos existentes ────────────────────────────
        try:
            configs = self.db.get_pricing_configs(solo_activos=False)
        except Exception:
            configs = []
        for c in configs:
            _add_row(c)

        # ── Botones de acción ──────────────────────────────────
        tk.Frame(card, bg=THEME["card_border"], height=1).pack(fill="x", pady=(18,14))

        action_row = tk.Frame(card, bg=THEME["card_bg"])
        action_row.pack(anchor="w")

        def _nueva_fila():
            _add_row(flash=True)
            # Scroll al final
            _page.update_idletasks()
            _cv.yview_moveto(1.0)

        def _guardar_todo():
            errores = []
            for i, r in enumerate(self._price_rows):
                try:
                    nombre  = r["v_nombre"].get().strip() or f"Modalidad {i+1}"
                    tipo    = r["v_tipo"].get().strip()
                    cuotas  = int(r["v_cuotas"].get())
                    pct     = float(r["v_pct"].get().replace(",","."))
                    data    = {"nombre": nombre, "tipo": tipo,
                               "cuotas": cuotas, "porcentaje": pct, "activo": 1}
                    pid     = r.get("id")
                    self.db.save_pricing_config(data, pid)
                    if pid is None:
                        # Obtener el id recién insertado
                        configs_now = self.db.get_pricing_configs(solo_activos=False)
                        if configs_now:
                            r["id"] = configs_now[-1]["id"]
                except Exception as ex:
                    errores.append(f"Fila {i+1}: {ex}")

            if errores:
                messagebox.showerror("Errores al guardar", "\n".join(errores))
            else:
                messagebox.showinfo("✅", "Configuración de precios guardada correctamente.")

        _btn(action_row, "+ Nueva cuota", _nueva_fila,
             THEME["acc_blue"], "").pack(side="left", padx=(0,8))
        _btn(action_row, "Guardar todo",  _guardar_todo,
             THEME["acc_green"], "💾").pack(side="left")

        # Nota informativa
        tk.Label(card,
                 text="💡  El porcentaje es el recargo total sobre el costo del producto.  "
                      "Ej: 60% significa que el precio de venta = costo × 1.60",
                 font=(FONT,8), bg=THEME["card_bg"],
                 fg=THEME["txt_secondary"], wraplength=560, justify="left"
                 ).pack(anchor="w", pady=(14,0))


    # ── TAB 4: LICENCIA ───────────────────────────────────────
    def _build_licencia_tab(self):
        # ── Scroll container ──────────────────────────────────────
        _cv = tk.Canvas(self._tab_area, bg=THEME["ct_bg"], highlightthickness=0)
        _sb = ttk.Scrollbar(self._tab_area, orient='vertical', command=_cv.yview)
        _cv.configure(yscrollcommand=_sb.set)
        _sb.pack(side='right', fill='y')
        _cv.pack(side='left', fill='both', expand=True)
        _page = tk.Frame(_cv, bg=THEME["ct_bg"])
        _win_id = _cv.create_window((0,0), window=_page, anchor='nw')
        def _on_cv_resize(e): _cv.itemconfig(_win_id, width=e.width)
        def _on_page_resize(e): _cv.configure(scrollregion=_cv.bbox('all'))
        _cv.bind('<Configure>', _on_cv_resize)
        _page.bind('<Configure>', _on_page_resize)
        def _mwheel(e):
            try: _cv.yview_scroll(-1*(e.delta//120),'units')
            except Exception: pass
        _cv.bind('<Enter>', lambda e: _cv.bind_all('<MouseWheel>', _mwheel))
        _cv.bind('<Leave>', lambda e: _cv.unbind_all('<MouseWheel>'))

        outer=tk.Frame(_page,bg=THEME["card_border"])
        outer.pack(fill='x',expand=False)
        card=tk.Frame(outer,bg=THEME["card_bg"],padx=28,pady=24)
        card.pack(fill='x',expand=False,padx=1,pady=1)
        tk.Label(card,text="Estado de Licencia",font=(FONT,13,'bold'),
                 bg=THEME["card_bg"],fg=THEME["txt_primary"]).pack(anchor='w',pady=(0,16))
        tk.Frame(card,bg=THEME["card_border"],height=1).pack(fill='x',pady=(0,20))
        try:
            from license.license_manager import is_licensed, get_license_info
            licensed=is_licensed(); info=get_license_info()
        except: licensed=False; info={}

        # Badge estado
        badge_f=tk.Frame(card,bg=THEME["acc_green"] if licensed else THEME["acc_rose"],
                         padx=20,pady=12)
        badge_f.pack(anchor='w',pady=(0,16))
        tk.Label(badge_f,text="✅  Sistema Licenciado" if licensed else "⚠️  Sin Licencia",
                 font=(FONT,12,'bold'),bg=THEME["acc_green"] if licensed else THEME["acc_rose"],
                 fg="#fff").pack()

        if info:
            for lbl,key in [("Nombre:",  "nombre"),("Email:","email"),
                            ("Expira:", "expiry"),("Clave:","key_display")]:
                row=tk.Frame(card,bg=THEME["card_bg"]); row.pack(anchor='w',pady=4)
                tk.Label(row,text=lbl,font=(FONT,9,'bold'),width=10,anchor='w',
                         bg=THEME["card_bg"],fg=THEME["txt_secondary"]).pack(side='left')
                tk.Label(row,text=str(info.get(key,'—')),font=(FONT,10),
                         bg=THEME["card_bg"],fg=THEME["txt_primary"]).pack(side='left',padx=8)

        if not licensed:
            tk.Frame(card,bg=THEME["card_border"],height=1).pack(fill='x',pady=16)
            tk.Label(card,text="Clave de Activación",font=(FONT,10,'bold'),
                     bg=THEME["card_bg"],fg=THEME["txt_secondary"]).pack(anchor='w',pady=(0,4))
            key_e=_entry(card); key_e.pack(fill='x',pady=(0,12))
            def activate():
                from license.license_manager import activate_license
                k=key_e.get().strip()
                if not k: messagebox.showerror("Error","Ingrese la clave de activación"); return
                ok,msg=activate_license(k)
                if ok: messagebox.showinfo("✅ Activado",msg); self._switch_tab(3)
                else: messagebox.showerror("Error",msg)
            _btn(card,"Activar Licencia",activate,THEME["acc_blue"],"🔑").pack(anchor='w')

        # Contacto
        tk.Frame(card,bg=THEME["card_border"],height=1).pack(fill='x',pady=(24,16))
        tk.Label(card,text="¿Necesitás una licencia?",font=(FONT,11,'bold'),
                 bg=THEME["card_bg"],fg=THEME["txt_primary"]).pack(anchor='w',pady=(0,8))
        for icon,text in [("✉","davenialgo@proton.me"),
                          ("📱","WhatsApp: +595 994-686 493"),
                          ("🌐","www.venialgosistemas.com")]:
            row=tk.Frame(card,bg=THEME["card_bg"]); row.pack(anchor='w',pady=2)
            tk.Label(row,text=icon,font=(FONT,11),bg=THEME["card_bg"]).pack(side='left',padx=(0,8))
            tk.Label(row,text=text,font=(FONT,10),bg=THEME["card_bg"],
                     fg=THEME["acc_blue"]).pack(side='left')
