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

def _btn(parent,text,cmd,bg,icon="",**kw):
    t=f"{icon}  {text}" if icon else text
    def _dk(c):
        r,g,b=int(c[1:3],16),int(c[3:5],16),int(c[5:7],16)
        return f"#{max(0,int(r*.82)):02x}{max(0,int(g*.82)):02x}{max(0,int(b*.82)):02x}"
    _en=[True]
    lbl=tk.Label(parent,text=t,font=(FONT,10,'bold'),bg=bg,fg="#fff",
                 cursor='hand2',padx=14,pady=8,**kw)
    def _click(_=None):
        if _en[0]: lbl.config(bg=_dk(bg)); lbl.after(120,lambda:lbl.config(bg=bg)); cmd()
    lbl.bind('<Enter>',lambda _:(lbl.config(bg=_dk(bg)) if _en[0] else None))
    lbl.bind('<Leave>',lambda _:lbl.config(bg=bg if _en[0] else "#9CA3AF"))
    lbl.bind('<ButtonRelease-1>',_click)
    lbl.enable =lambda:(setattr(type(lbl),'_e',True) or _en.__setitem__(0,True)  or lbl.config(bg=bg,    fg="#fff",cursor='hand2'))
    lbl.disable=lambda:(setattr(type(lbl),'_e',False)or _en.__setitem__(0,False) or lbl.config(bg="#9CA3AF",fg="#fff",cursor='arrow'))
    return lbl

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
        tbl_outer=tk.Frame(self.parent,bg=THEME["card_border"])
        tbl_outer.pack(fill='both',expand=True,padx=24,pady=(0,10))
        tbl=tk.Frame(tbl_outer,bg=THEME["card_bg"]); tbl.pack(fill='both',expand=True,padx=1,pady=1)
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
        self.btn_edit=_btn(act,"Editar",self.show_edit_dialog,THEME["acc_amber"],"✏")
        self.btn_edit.disable(); self.btn_edit.pack(side='left',padx=(0,8))
        self.btn_del=_btn(act,"Eliminar",self.delete_product,THEME["btn_danger"],"🗑")
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

    def show_add_dialog(self): self._show_dialog('add')
    def show_edit_dialog(self):
        if self.selected_product_id: self._show_dialog('edit',self.selected_product_id)

    def _show_dialog(self,mode,product_id=None):
        title="Nuevo Producto" if mode=='add' else "Editar Producto"
        dlg=tk.Toplevel(self.parent)
        _set_icon(dlg)
        _set_icon(dlg); dlg.title(title)
        dlg.configure(bg=THEME["ct_bg"]); dlg.resizable(False,False)
        dlg.transient(self.parent); dlg.grab_set(); _center(dlg,500,720)

        # Botones PRIMERO
        btn_bar=tk.Frame(dlg,bg=THEME["card_bg"],padx=16,pady=12)
        btn_bar.pack(fill='x',side='bottom')
        tk.Frame(dlg,bg=THEME["card_border"],height=1).pack(fill='x',side='bottom')

        # Header
        hdr=tk.Frame(dlg,bg=THEME["sb_bg"],pady=12); hdr.pack(fill='x')
        tk.Label(hdr,text=f"{'📦 Nuevo' if mode=='add' else '✏ Editar'} Producto",
                 font=(FONT,13,'bold'),bg=THEME["sb_bg"],fg="#fff").pack(anchor='w',padx=16)

        canvas=tk.Canvas(dlg,bg=THEME["ct_bg"],highlightthickness=0)
        canvas.pack(fill='both',expand=True)
        body=tk.Frame(canvas,bg=THEME["ct_bg"],padx=24,pady=16)
        canvas.create_window((0,0),window=body,anchor='nw',tags='body')
        def _rsz(e): canvas.itemconfig('body',width=e.width)
        def _srg(e): canvas.configure(scrollregion=canvas.bbox('all'))
        canvas.bind('<Configure>',_rsz); body.bind('<Configure>',_srg)

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
        lbl_entry('codigo','Código de Barras')

        # Tabla de precios (calculada automáticamente)
        prices_card=tk.Frame(body,bg=THEME["card_border"]); prices_card.pack(fill='x',pady=(4,0))
        prices_inner=tk.Frame(prices_card,bg=THEME["card_bg"],padx=12,pady=10)
        prices_inner.pack(fill='x',padx=1,pady=1)
        tk.Label(prices_inner,text="Precios por modalidad (auto)",font=(FONT,9,'bold'),
                 bg=THEME["card_bg"],fg=THEME["acc_blue"]).pack(anchor='w',pady=(0,6))
        prices_cols=('Modalidad','Ganancia','Precio Venta','Cuota')
        ptree=ttk.Treeview(prices_inner,columns=prices_cols,show='headings',
                           height=4,style='POS.Treeview')
        for col,w in zip(prices_cols,[110,70,110,90]):
            ptree.heading(col,text=col); ptree.column(col,width=w,anchor='center')
        ptree.pack(fill='x')

        def update_prices(*_):
            try:
                costo=float(fields['costo'].get().replace(',','').replace('.','').replace('Gs','').strip() or '0')
                if costo<=0: return
                precios=self.db.calcular_precios_producto(costo)
                from utils.formatters import format_currency
                for i in ptree.get_children(): ptree.delete(i)
                for p in precios:
                    cuota=format_currency(p.get('cuota',0)) if p.get('cuota',0)>0 else '—'
                    tag='cash' if p.get('tipo')=='contado' else 'credit'
                    ptree.insert('','end',tags=(tag,),values=(
                        p.get('nombre',''),f"{p.get('porcentaje',0):.0f}%",
                        format_currency(p.get('precio',0)),cuota))
                    if p.get('tipo')=='contado':
                        fields['precio'].delete(0,'end')
                        fields['precio'].insert(0,str(int(p.get('precio',0))))
                ptree.tag_configure('cash',foreground=THEME["acc_green"])
                ptree.tag_configure('credit',foreground=THEME["acc_blue"])
            except Exception: pass

        fields['costo']._e.bind('<FocusOut>',update_prices)
        fields['costo']._e.bind('<Return>',update_prices)

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
        fields['nombre'].focus()

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
                if mode=='add': self.db.add_product(nombre,precio,stock,cat,cod,costo=costo)
                else: self.db.update_product(product_id,nombre,precio,stock,cat,cod,costo=costo)
                messagebox.showinfo("✅","Producto guardado correctamente",parent=dlg)
                self.load_products(); dlg.destroy()
            except Exception as e: messagebox.showerror("Error",str(e),parent=dlg)

        _btn(btn_bar,"Guardar",save,THEME["acc_green"],"💾").pack(side='left',padx=(0,8))
        _btn(btn_bar,"Cancelar",dlg.destroy,THEME["btn_secondary"],"✕").pack(side='left')

    def delete_product(self):
        if not self.selected_product_id: return
        if messagebox.askyesno("Confirmar","¿Eliminar este producto?"):
            try:
                self.db.delete_product(self.selected_product_id)
                messagebox.showinfo("✅","Producto eliminado")
                self.load_products(); self.selected_product_id=None
                self.btn_edit.disable(); self.btn_del.disable()
            except Exception as e: messagebox.showerror("Error",str(e))
