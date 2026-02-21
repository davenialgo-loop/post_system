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

def _btn(parent,text,cmd,bg,icon="",**kw):
    t=f"{icon}  {text}" if icon else text
    def _dk(c):
        r,g,b=int(c[1:3],16),int(c[3:5],16),int(c[5:7],16)
        return f"#{max(0,int(r*.82)):02x}{max(0,int(g*.82)):02x}{max(0,int(b*.82)):02x}"
    lbl=tk.Label(parent,text=t,font=(FONT,10,'bold'),bg=bg,fg="#fff",cursor='hand2',padx=14,pady=8,**kw)
    lbl.bind('<Enter>',lambda _:lbl.config(bg=_dk(bg)))
    lbl.bind('<Leave>',lambda _:lbl.config(bg=bg))
    lbl.bind('<ButtonRelease-1>',lambda _:(lbl.config(bg=_dk(bg)),cmd()))
    return lbl

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
        outer=tk.Frame(self._tab_area,bg=THEME["card_border"])
        outer.pack(fill='both',expand=True)
        card=tk.Frame(outer,bg=THEME["card_bg"],padx=28,pady=24)
        card.pack(fill='both',expand=True,padx=1,pady=1)
        tk.Label(card,text="Datos de la Empresa",font=(FONT,13,'bold'),
                 bg=THEME["card_bg"],fg=THEME["txt_primary"]).pack(anchor='w',pady=(0,16))
        tk.Frame(card,bg=THEME["card_border"],height=1).pack(fill='x',pady=(0,16))

        try:
            from utils.company_header import get_company
            co=get_company()
        except: co={}

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

        def save_company():
            data={k:fields[k].get().strip() for k in fields}
            if not data.get('razon_social'):
                messagebox.showerror("Error","Razón Social es requerida"); return
            try:
                self.db.update_company_info(**data)
                messagebox.showinfo("✅","Datos de empresa guardados correctamente")
                if self.on_company_saved: self.on_company_saved()
            except Exception as e: messagebox.showerror("Error",str(e))

        btn_row=tk.Frame(card,bg=THEME["card_bg"]); btn_row.pack(anchor='w',pady=(20,0))
        _btn(btn_row,"Guardar Datos",save_company,THEME["acc_green"],"💾").pack(side='left')

    # ── TAB 2: USUARIOS ───────────────────────────────────────
    def _build_usuarios_tab(self):
        outer=tk.Frame(self._tab_area,bg=THEME["card_border"])
        outer.pack(fill='both',expand=True)
        card=tk.Frame(outer,bg=THEME["card_bg"]); card.pack(fill='both',expand=True,padx=1,pady=1)

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
        _btn(act,"Activar/Desactivar",lambda:self._toggle_user(),THEME["btn_secondary"],"⏻").pack(side='left')

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
        dlg=tk.Toplevel(self.parent); dlg.title(title)
        dlg.configure(bg=THEME["ct_bg"]); dlg.resizable(False,False)
        dlg.transient(self.parent); dlg.grab_set(); _center(dlg,440,460)

        btn_bar=tk.Frame(dlg,bg=THEME["card_bg"],padx=16,pady=12)
        btn_bar.pack(fill='x',side='bottom')
        tk.Frame(dlg,bg=THEME["card_border"],height=1).pack(fill='x',side='bottom')

        hdr=tk.Frame(dlg,bg=THEME["sb_bg"],pady=12); hdr.pack(fill='x')
        tk.Label(hdr,text=f"{'👤 Nuevo' if mode=='add' else '✏ Editar'} Usuario",
                 font=(FONT,13,'bold'),bg=THEME["sb_bg"],fg="#fff").pack(anchor='w',padx=16)

        body=tk.Frame(dlg,bg=THEME["ct_bg"],padx=24,pady=16); body.pack(fill='both',expand=True)
        fields={}
        for key,lbl in [('nombre','Nombre completo'),('usuario','Nombre de usuario'),
                        ('password','Contraseña'),('password2','Confirmar contraseña')]:
            tk.Label(body,text=lbl,font=(FONT,9,'bold'),bg=THEME["ct_bg"],
                     fg=THEME["txt_secondary"]).pack(anchor='w',pady=(0,3))
            e=_entry(body,show='●' if 'password' in key else None)
            e.pack(fill='x',pady=(0,10)); fields[key]=e

        tk.Label(body,text="Rol",font=(FONT,9,'bold'),bg=THEME["ct_bg"],
                 fg=THEME["txt_secondary"]).pack(anchor='w',pady=(0,3))
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

        _btn(btn_bar,"Guardar",save,THEME["acc_green"],"💾").pack(side='left',padx=(0,8))
        _btn(btn_bar,"Cancelar",dlg.destroy,THEME["btn_secondary"],"✕").pack(side='left')

    def _toggle_user(self):
        sel=self.user_tree.selection()
        if not sel: return
        uid=self.user_tree.item(sel[0])['values'][0]
        try:
            self.db.toggle_user_active(uid)
            self._load_users()
        except Exception as e: messagebox.showerror("Error",str(e))

    # ── TAB 3: PRECIOS ────────────────────────────────────────
    def _build_precios_tab(self):
        outer=tk.Frame(self._tab_area,bg=THEME["card_border"])
        outer.pack(fill='both',expand=True)
        card=tk.Frame(outer,bg=THEME["card_bg"],padx=28,pady=24)
        card.pack(fill='both',expand=True,padx=1,pady=1)
        tk.Label(card,text="Configuración de Precios",font=(FONT,13,'bold'),
                 bg=THEME["card_bg"],fg=THEME["txt_primary"]).pack(anchor='w',pady=(0,6))
        tk.Label(card,text="Defina los porcentajes de ganancia por modalidad de venta",
                 font=(FONT,9),bg=THEME["card_bg"],fg=THEME["txt_secondary"]).pack(anchor='w',pady=(0,16))
        tk.Frame(card,bg=THEME["card_border"],height=1).pack(fill='x',pady=(0,20))

        try: config=self.db.get_pricing_config()
        except: config={}

        fields={}
        price_labels=[
            ("contado_pct","Margen Contado (%)","Ganancia sobre precio costo para venta al contado",THEME["acc_green"]),
            ("credito_pct","Margen Crédito (%)","Ganancia adicional para ventas a crédito",THEME["acc_blue"]),
            ("cuota_pct","Recargo Cuotas (%)","Recargo por financiamiento en cuotas",THEME["acc_amber"]),
            ("mayoreo_pct","Descuento Mayoreo (%)","Descuento para ventas al por mayor",THEME["acc_purple"]),
        ]
        for key,lbl,desc,accent in price_labels:
            row=tk.Frame(card,bg=THEME["card_bg"])
            row.pack(fill='x',pady=(0,16))
            left=tk.Frame(row,bg=THEME["card_bg"])
            left.pack(side='left',fill='x',expand=True)
            tk.Label(left,text=lbl,font=(FONT,10,'bold'),bg=THEME["card_bg"],fg=THEME["txt_primary"]).pack(anchor='w')
            tk.Label(left,text=desc,font=(FONT,9),bg=THEME["card_bg"],fg=THEME["txt_secondary"]).pack(anchor='w')
            indicator=tk.Frame(left,bg=accent,width=4,height=40)
            indicator.pack(side='left',padx=(0,8))

            right=tk.Frame(row,bg=THEME["card_bg"],width=120)
            right.pack(side='right',padx=(20,0))
            right.pack_propagate(False)
            e=_entry(right); e.pack(fill='x')
            val=config.get(key,0)
            e.insert(0,str(val)); fields[key]=e

        def save_prices():
            try:
                data={k:float(fields[k].get()) for k in fields}
                self.db.update_pricing_config(**data)
                messagebox.showinfo("✅","Precios actualizados correctamente")
            except ValueError: messagebox.showerror("Error","Ingrese valores numéricos válidos")
            except Exception as e: messagebox.showerror("Error",str(e))

        _btn(card,"Guardar Precios",save_prices,THEME["acc_green"],"💾").pack(anchor='w',pady=(8,0))

    # ── TAB 4: LICENCIA ───────────────────────────────────────
    def _build_licencia_tab(self):
        outer=tk.Frame(self._tab_area,bg=THEME["card_border"])
        outer.pack(fill='both',expand=True)
        card=tk.Frame(outer,bg=THEME["card_bg"],padx=28,pady=24)
        card.pack(fill='both',expand=True,padx=1,pady=1)
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
