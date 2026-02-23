"""Módulo Gestión de Clientes — Diseño moderno Venialgo POS"""
import tkinter as tk
try:
    from utils.window_icon import set_icon as _set_icon
except ImportError:
    def _set_icon(w): pass
from tkinter import ttk, messagebox
from config.settings import FONTS as _F
from utils.validators import validate_required_field

THEME={"ct_bg":"#F9FAFB","card_bg":"#FFFFFF","card_border":"#E5E7EB","sb_bg":"#111827","acc_purple":"#7C3AED",
    "txt_primary":"#111827","txt_secondary":"#6B7280","txt_white":"#FFFFFF",
    "acc_blue":"#2563EB","acc_green":"#059669","acc_rose":"#E11D48","acc_amber":"#D97706",
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
    outer.focus=e.focus; outer._e=e
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

class CustomerModule:
    def __init__(self,parent,db_manager):
        self.parent=parent; self.db=db_manager
        self.selected_customer_id=None; _setup_styles()
        self._build(); self.load_customers()

    def _build(self):
        bg=THEME["ct_bg"]
        # Header
        hdr=tk.Frame(self.parent,bg=bg); hdr.pack(fill='x',padx=28,pady=(20,0))
        tk.Label(hdr,text="👥  Gestión de Clientes",font=(FONT,16,'bold'),
                 bg=bg,fg=THEME["txt_primary"]).pack(side='left')
        tk.Frame(self.parent,bg=THEME["card_border"],height=1).pack(fill='x',padx=28,pady=(10,14))

        # Toolbar
        tb=tk.Frame(self.parent,bg=bg,padx=24); tb.pack(fill='x',pady=(0,10))
        srch_outer=tk.Frame(tb,bg=THEME["input_brd"])
        srch_inner=tk.Frame(srch_outer,bg=THEME["input_bg"]); srch_inner.pack(fill='x',padx=1,pady=1)
        tk.Label(srch_inner,text="🔍",bg=THEME["input_bg"],fg=THEME["txt_secondary"],
                 font=(FONT,11)).pack(side='left',padx=(10,4))
        self.search_var=tk.StringVar()
        srch_e=tk.Entry(srch_inner,textvariable=self.search_var,font=(FONT,11),
                        bg=THEME["input_bg"],fg=THEME["txt_primary"],relief='flat',bd=0)
        srch_e.pack(fill='x',padx=4,pady=8,side='left',expand=True)
        # Placeholder hint
        HINT="Buscar por nombre, RUC o N° de documento..."
        def _ph_in(e):
            if srch_e.get()==HINT:
                srch_e.delete(0,'end'); srch_e.config(fg=THEME["txt_primary"])
        def _ph_out(e):
            if not srch_e.get():
                srch_e.insert(0,HINT); srch_e.config(fg=THEME["txt_secondary"])
        _ph_out(None)
        srch_e.bind("<FocusIn>",  _ph_in)
        srch_e.bind("<FocusOut>", _ph_out)
        def _smart_search(*_):
            term = self.search_var.get()
            if term == HINT: return
            self.load_customers(term)
        self.search_var.trace('w', _smart_search)
        srch_outer.pack(side='left',fill='x',expand=True,padx=(0,12))
        _btn(tb,"Nuevo Cliente",self.show_add_dialog,THEME["acc_blue"],"＋").pack(side='right')

        # Stats row
        stats=tk.Frame(self.parent,bg=bg,padx=24); stats.pack(fill='x',pady=(0,12))
        self.lbl_total=tk.Label(stats,text="Total: 0 clientes",font=(FONT,9),
                                bg=bg,fg=THEME["txt_secondary"]); self.lbl_total.pack(side='left')
        self.lbl_search_hint=tk.Label(stats,
            text="  🔍 Busca por nombre, RUC o N° documento",
            font=(FONT,8),bg=bg,fg=THEME["txt_secondary"])
        self.lbl_search_hint.pack(side='left',padx=(16,0))

        # Tabla
        tbl_outer=tk.Frame(self.parent,bg=THEME["card_border"])
        tbl_outer.pack(fill='both',expand=True,padx=24,pady=(0,10))
        tbl=tk.Frame(tbl_outer,bg=THEME["card_bg"]); tbl.pack(fill='both',expand=True,padx=1,pady=1)
        cols=('ID','Nombre','RUC/CI','Teléfono','Email','Dirección','Créditos')
        self.tree=ttk.Treeview(tbl,columns=cols,show='headings',style='POS.Treeview')
        widths={'ID':45,'Nombre':180,'RUC/CI':110,'Teléfono':110,'Email':180,'Dirección':180,'Créditos':70}
        for col in cols:
            self.tree.heading(col,text=col)
            self.tree.column(col,width=widths[col],anchor='w' if col in('Nombre','Email','Dirección') else 'center')
        sb=ttk.Scrollbar(tbl,orient='vertical',command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side='right',fill='y',padx=(0,4),pady=4); self.tree.pack(fill='both',expand=True,padx=4,pady=4)
        self.tree.bind('<<TreeviewSelect>>',self._on_select)
        self.tree.bind('<Double-Button-1>',lambda _:self.show_edit_dialog())

        # Botones
        act=tk.Frame(self.parent,bg=bg,padx=24,pady=8); act.pack(fill='x')
        self.btn_edit=_btn(act,"Editar",self.show_edit_dialog,THEME["acc_amber"],"✏")
        self.btn_edit.pack(side='left',padx=(0,8)); self.btn_edit.disable()
        self.btn_del=_btn(act,"Eliminar",self.delete_customer,THEME["btn_danger"],"🗑")
        self.btn_del.pack(side='left',padx=(0,8)); self.btn_del.disable()
        self.btn_hist=_btn(act,"Ver Créditos",self.show_customer_credits,THEME["acc_purple"],"💳")
        self.btn_hist.pack(side='left'); self.btn_hist.disable()

    def load_customers(self,search_term=''):
        for i in self.tree.get_children(): self.tree.delete(i)
        customers=self.db.search_customers(search_term) if search_term else self.db.get_all_customers()
        for idx,c in enumerate(customers):
            tag='odd' if idx%2 else 'even'
            credits=self.db.get_all_credit_sales('active')
            cid=c.get('id',0)
            credit_count=len([x for x in credits if x.get('customer_id')==cid or x.get('cliente_id')==cid])
            self.tree.insert('','end',tags=(tag,),values=(
                c.get('id',''),c.get('name',c.get('nombre','')),
                c.get('ruc',''),c.get('phone',c.get('telefono','')),
                c.get('email',c.get('correo','')),
                c.get('address',c.get('direccion','')),
                credit_count or '—'))
        self.tree.tag_configure('odd',background=THEME["row_odd"])
        self.tree.tag_configure('even',background=THEME["row_even"])
        self.lbl_total.config(text=f"Total: {len(customers)} cliente{'s' if len(customers)!=1 else ''}")
        if hasattr(self,'lbl_search_hint'):
            if search_term:
                self.lbl_search_hint.config(
                    text=f"  🔍 Filtrando por: '{search_term}'",
                    fg=THEME["acc_blue"])
            else:
                self.lbl_search_hint.config(
                    text="  🔍 Busca por nombre, RUC o N° documento",
                    fg=THEME["txt_secondary"])

    def search_customers(self): self.load_customers(self.search_var.get())

    def _on_select(self,_=None):
        sel=self.tree.selection()
        if sel:
            self.selected_customer_id=self.tree.item(sel[0])['values'][0]
            for b in [self.btn_edit,self.btn_del,self.btn_hist]: b.enable()
        else:
            self.selected_customer_id=None
            for b in [self.btn_edit,self.btn_del,self.btn_hist]: b.disable()

    def show_add_dialog(self): self._show_dialog('add')
    def show_edit_dialog(self):
        if self.selected_customer_id: self._show_dialog('edit',self.selected_customer_id)

    def _show_dialog(self,mode,customer_id=None):
        title="Nuevo Cliente" if mode=='add' else "Editar Cliente"
        dlg=tk.Toplevel(self.parent)
        _set_icon(dlg)
        _set_icon(dlg); dlg.title(title)
        dlg.configure(bg=THEME["ct_bg"]); dlg.resizable(False,False)
        dlg.transient(self.parent); dlg.grab_set(); _center(dlg,480,560)

        btn_bar=tk.Frame(dlg,bg=THEME["card_bg"],padx=16,pady=12)
        btn_bar.pack(fill='x',side='bottom')
        tk.Frame(dlg,bg=THEME["card_border"],height=1).pack(fill='x',side='bottom')

        hdr=tk.Frame(dlg,bg=THEME["sb_bg"],pady=12); hdr.pack(fill='x')
        tk.Label(hdr,text=f"{'👥 Nuevo' if mode=='add' else '✏ Editar'} Cliente",
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
            if required: tk.Label(row,text=" *",font=(FONT,9),bg=THEME["ct_bg"],fg=THEME["acc_rose"]).pack(side='left')
            e=_entry(body); e.pack(fill='x',pady=(0,10)); fields[key]=e

        lbl_entry('nombre','Nombre',required=True)
        lbl_entry('ruc','RUC / C.I.')
        lbl_entry('telefono','Teléfono')
        lbl_entry('correo','Email')
        lbl_entry('direccion','Dirección')

        if mode=='edit' and customer_id:
            c=self.db.get_customer_by_id(customer_id)
            if c:
                fields['nombre'].insert(0,c.get('name',c.get('nombre','')))
                fields['ruc'].insert(0,c.get('ruc',''))
                fields['telefono'].insert(0,c.get('phone',c.get('telefono','')))
                fields['correo'].insert(0,c.get('email',c.get('correo','')))
                fields['direccion'].insert(0,c.get('address',c.get('direccion','')))
        fields['nombre'].focus()

        def save():
            ok,msg,nombre=validate_required_field(fields['nombre'].get(),"Nombre")
            if not ok: messagebox.showerror("Error",msg,parent=dlg); return
            ruc=fields['ruc'].get().strip(); tel=fields['telefono'].get().strip()
            correo=fields['correo'].get().strip(); dir_=fields['direccion'].get().strip()
            try:
                if mode=='add': self.db.add_customer(nombre,ruc,tel,correo,dir_)
                else: self.db.update_customer(customer_id,nombre,ruc,tel,correo,dir_)
                messagebox.showinfo("✅","Cliente guardado correctamente",parent=dlg)
                self.load_customers(); dlg.destroy()
            except Exception as e: messagebox.showerror("Error",str(e),parent=dlg)

        _btn(btn_bar,"Guardar",save,THEME["acc_green"],"💾").pack(side='left',padx=(0,8))
        _btn(btn_bar,"Cancelar",dlg.destroy,THEME["btn_secondary"],"✕").pack(side='left')

    def delete_customer(self):
        if not self.selected_customer_id: return
        if messagebox.askyesno("Confirmar","¿Eliminar este cliente?\nSe perderán sus datos."):
            try:
                self.db.delete_customer(self.selected_customer_id)
                messagebox.showinfo("✅","Cliente eliminado")
                self.load_customers(); self.selected_customer_id=None
                for b in [self.btn_edit,self.btn_del,self.btn_hist]: b.disable()
            except Exception as e: messagebox.showerror("Error",str(e))

    def show_customer_credits(self):
        if not self.selected_customer_id: return
        c=self.db.get_customer_by_id(self.selected_customer_id)
        credits=self.db.get_all_credit_sales()
        cid=self.selected_customer_id
        client_credits=[x for x in credits if x.get('customer_id')==cid or x.get('cliente_id')==cid]
        dlg=tk.Toplevel(self.parent)
        _set_icon(dlg)
        _set_icon(dlg); dlg.title(f"Créditos — {c.get('name',c.get('nombre',''))}")
        dlg.configure(bg=THEME["ct_bg"]); dlg.transient(self.parent); _center(dlg,620,400)
        hdr=tk.Frame(dlg,bg=THEME["sb_bg"],pady=12); hdr.pack(fill='x')
        tk.Label(hdr,text=f"💳  Créditos de {c.get('name',c.get('nombre',''))}",
                 font=(FONT,12,'bold'),bg=THEME["sb_bg"],fg="#fff").pack(anchor='w',padx=16)
        tbl=tk.Frame(dlg,bg=THEME["card_bg"]); tbl.pack(fill='both',expand=True,padx=16,pady=16)
        from utils.formatters import format_currency
        cols=('ID','Total','Saldo','Cuota','Próximo Pago','Estado')
        tree=ttk.Treeview(tbl,columns=cols,show='headings',height=8,style='POS.Treeview')
        for col,w in zip(cols,[50,110,110,100,130,80]):
            tree.heading(col,text=col); tree.column(col,width=w,anchor='center')
        sb=ttk.Scrollbar(tbl,orient='vertical',command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side='right',fill='y'); tree.pack(fill='both',expand=True)
        for i,cr in enumerate(client_credits):
            status='Activo' if cr.get('status')=='active' else 'Pagado'
            tree.insert('','end',tags=('odd' if i%2 else 'even',),values=(
                cr.get('id',''),format_currency(cr.get('total_amount',0)),
                format_currency(cr.get('remaining_balance',0)),
                format_currency(cr.get('installment_amount',0)),
                cr.get('next_payment_date','—'),status))
        tree.tag_configure('odd',background=THEME["row_odd"]); tree.tag_configure('even',background=THEME["row_even"])
        if not client_credits:
            tk.Label(tbl,text="Sin créditos registrados",font=(FONT,10),
                     bg=THEME["card_bg"],fg=THEME["txt_secondary"]).pack(pady=20)
        _btn(dlg,"Cerrar",dlg.destroy,THEME["btn_secondary"]).pack(pady=10)
