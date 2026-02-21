"""Módulo Punto de Venta — Diseño moderno Venialgo POS"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from config.settings import COLORS, FONTS as _F, SPACING, BUTTON_STYLES, BUSINESS
from utils.formatters import format_currency, generate_ticket
try:
    from utils.window_icon import set_icon as _set_icon
except ImportError:
    def _set_icon(w): pass

THEME = {
    "ct_bg":"#F9FAFB","card_bg":"#FFFFFF","card_border":"#E5E7EB",
    "txt_primary":"#111827","txt_secondary":"#6B7280","txt_white":"#FFFFFF",
    "acc_blue":"#2563EB","acc_green":"#059669","acc_amber":"#D97706",
    "acc_rose":"#E11D48","btn_danger":"#DC2626","btn_secondary":"#6B7280",
    "input_bg":"#FFFFFF","input_brd":"#D1D5DB","input_foc":"#2563EB",
    "row_odd":"#F9FAFB","row_even":"#FFFFFF","sb_bg":"#111827",
}
FONT = "Segoe UI"

def _btn(parent, text, cmd, bg, icon=""):
    t = f"{icon}  {text}" if icon else text
    def _dk(c):
        r,g,b=int(c[1:3],16),int(c[3:5],16),int(c[5:7],16)
        return f"#{max(0,int(r*.82)):02x}{max(0,int(g*.82)):02x}{max(0,int(b*.82)):02x}"
    lbl=tk.Label(parent,text=t,font=(FONT,10,'bold'),bg=bg,fg="#fff",
                 cursor='hand2',padx=14,pady=8)
    lbl.bind('<Enter>',lambda _:lbl.config(bg=_dk(bg)))
    lbl.bind('<Leave>',lambda _:lbl.config(bg=bg))
    lbl.bind('<ButtonRelease-1>',lambda _:(lbl.config(bg=_dk(bg)),cmd()))
    return lbl

def _setup_tree_style():
    s=ttk.Style()
    try: s.theme_use('clam')
    except: pass
    s.configure("POS.Treeview",background="#fff",foreground="#111827",
        fieldbackground="#fff",rowheight=32,font=(FONT,10),borderwidth=0)
    s.configure("POS.Treeview.Heading",background="#111827",foreground="#fff",
        font=(FONT,9,'bold'),relief='flat',padding=(8,6))
    s.map("POS.Treeview",background=[('selected','#2563EB')],
          foreground=[('selected','#fff')])

class SalesModule:
    def __init__(self, parent, db_manager):
        self.parent=parent; self.db=db_manager
        self.cart=[]; self.selected_customer_id=None
        _setup_tree_style()
        self._build()
        self.load_products()
        self._update_totals()

    def _build(self):
        bg=THEME["ct_bg"]
        # Header
        hdr=tk.Frame(self.parent,bg=bg)
        hdr.pack(fill='x',padx=28,pady=(20,0))
        tk.Label(hdr,text="🛒  Punto de Venta",font=(FONT,16,'bold'),
                 bg=bg,fg=THEME["txt_primary"]).pack(side='left')
        tk.Frame(self.parent,bg=THEME["card_border"],height=1).pack(
            fill='x',padx=28,pady=(10,14))

        # Contenedor principal
        main=tk.Frame(self.parent,bg=bg)
        main.pack(fill='both',expand=True,padx=24,pady=(0,20))
        main.columnconfigure(0,weight=3)
        main.columnconfigure(1,weight=2)
        main.rowconfigure(0,weight=1)

        # ── Panel izquierdo: catálogo ─────────────────────────
        left_outer=tk.Frame(main,bg=THEME["card_border"])
        left_outer.grid(row=0,column=0,sticky='nsew',padx=(0,8))
        left=tk.Frame(left_outer,bg=THEME["card_bg"])
        left.pack(fill='both',expand=True,padx=1,pady=1)

        tk.Label(left,text="Buscar productos",font=(FONT,11,'bold'),
                 bg=THEME["card_bg"],fg=THEME["txt_primary"]).pack(
                 anchor='w',padx=16,pady=(14,8))
        tk.Frame(left,bg=THEME["card_border"],height=1).pack(fill='x')

        # Barra búsqueda
        sb_frm=tk.Frame(left,bg=THEME["card_bg"],padx=16,pady=10)
        sb_frm.pack(fill='x')
        srch_outer=tk.Frame(sb_frm,bg=THEME["input_brd"])
        srch_outer.pack(fill='x')
        srch_inner=tk.Frame(srch_outer,bg=THEME["input_bg"])
        srch_inner.pack(fill='x',padx=1,pady=1)
        tk.Label(srch_inner,text="🔍",bg=THEME["input_bg"],
                 font=(FONT,11),fg=THEME["txt_secondary"]).pack(side='left',padx=(10,4))
        self.search_var=tk.StringVar()
        self.search_var.trace('w',lambda *_:self.search_products())
        srch_e=tk.Entry(srch_inner,textvariable=self.search_var,
                        font=(FONT,11),bg=THEME["input_bg"],fg=THEME["txt_primary"],
                        relief='flat',bd=0,insertbackground=THEME["acc_blue"])
        srch_e.pack(fill='x',padx=4,pady=9)
        srch_e.bind('<FocusIn>',lambda _:srch_outer.config(bg=THEME["input_foc"]))
        srch_e.bind('<FocusOut>',lambda _:srch_outer.config(bg=THEME["input_brd"]))
        srch_e.focus()

        # Lista productos (cards)
        list_canvas=tk.Canvas(left,bg=THEME["card_bg"],highlightthickness=0)
        list_sb=ttk.Scrollbar(left,orient='vertical',command=list_canvas.yview)
        list_canvas.configure(yscrollcommand=list_sb.set)
        list_sb.pack(side='right',fill='y',padx=(0,4),pady=4)
        list_canvas.pack(fill='both',expand=True,padx=8,pady=4)
        self.list_frame=tk.Frame(list_canvas,bg=THEME["card_bg"])
        self._list_win=list_canvas.create_window((0,0),window=self.list_frame,anchor='nw')
        def _resize(e):
            list_canvas.itemconfig(self._list_win,width=e.width)
        def _scroll_region(e):
            list_canvas.configure(scrollregion=list_canvas.bbox('all'))
        list_canvas.bind('<Configure>',_resize)
        self.list_frame.bind('<Configure>',_scroll_region)
        list_canvas.bind_all('<MouseWheel>',
            lambda e:list_canvas.yview_scroll(-1*(e.delta//120),'units'))
        self._list_canvas=list_canvas

        # ── Panel derecho: carrito ────────────────────────────
        right_outer=tk.Frame(main,bg=THEME["card_border"])
        right_outer.grid(row=0,column=1,sticky='nsew',padx=(8,0))
        right=tk.Frame(right_outer,bg=THEME["card_bg"])
        right.pack(fill='both',expand=True,padx=1,pady=1)

        tk.Label(right,text="Carrito de compra",font=(FONT,11,'bold'),
                 bg=THEME["card_bg"],fg=THEME["txt_primary"]).pack(
                 anchor='w',padx=16,pady=(14,8))
        tk.Frame(right,bg=THEME["card_border"],height=1).pack(fill='x')

        # Treeview carrito
        cart_f=tk.Frame(right,bg=THEME["card_bg"])
        cart_f.pack(fill='both',expand=True,padx=8,pady=8)
        cols=('Producto','Cant','Precio','Subtotal')
        self.cart_tree=ttk.Treeview(cart_f,columns=cols,show='headings',
                                    height=8,style='POS.Treeview')
        for col,w in zip(cols,[160,50,90,90]):
            self.cart_tree.heading(col,text=col)
            self.cart_tree.column(col,width=w,
                anchor='center' if col in('Cant','Precio','Subtotal') else 'w')
        sb_cart=ttk.Scrollbar(cart_f,orient='vertical',command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=sb_cart.set)
        sb_cart.pack(side='right',fill='y')
        self.cart_tree.pack(fill='both',expand=True)

        # Total
        tk.Frame(right,bg=THEME["card_border"],height=1).pack(fill='x',padx=12)
        tot_f=tk.Frame(right,bg=THEME["card_bg"],padx=16,pady=12)
        tot_f.pack(fill='x')
        tk.Label(tot_f,text="TOTAL",font=(FONT,11,'bold'),
                 bg=THEME["card_bg"],fg=THEME["txt_secondary"]).pack(side='left')
        self.total_label=tk.Label(tot_f,text="Gs. 0",font=(FONT,16,'bold'),
                 bg=THEME["card_bg"],fg=THEME["acc_green"])
        self.total_label.pack(side='right')

        # Botones carrito
        btn_row=tk.Frame(right,bg=THEME["card_bg"],padx=12,pady=6)
        btn_row.pack(fill='x')
        _btn(btn_row,"Quitar",self.remove_from_cart,THEME["btn_danger"],"✕").pack(side='left',padx=(0,6))
        _btn(btn_row,"Vaciar",self.clear_cart,THEME["btn_secondary"],"🗑").pack(side='left')

        tk.Frame(right,bg=THEME["card_border"],height=1).pack(fill='x',padx=12)

        fin_btn=_btn(right,"FINALIZAR VENTA",self.show_checkout_dialog,
                     THEME["acc_green"],"☑")
        fin_btn.config(font=(FONT,12,'bold'),pady=14)
        fin_btn.pack(fill='x',padx=12,pady=12)

    # ── Cargar productos ──────────────────────────────────────
    def load_products(self):
        self.all_products=self.db.get_all_products()
        self._display_products(self.all_products)

    def _display_products(self,products):
        for w in self.list_frame.winfo_children():
            w.destroy()
        for p in products:
            self._product_card(p)
        if not products:
            tk.Label(self.list_frame,text="Sin resultados",font=(FONT,10),
                     bg=THEME["card_bg"],fg=THEME["txt_muted"] if "txt_muted" in THEME else "#9CA3AF"
                     ).pack(pady=20)

    def _product_card(self,p):
        stock=p.get('stock',p.get('quantity',0))
        row=tk.Frame(self.list_frame,bg=THEME["card_bg"],cursor='hand2')
        row.pack(fill='x',pady=1)
        tk.Frame(row,bg=THEME["card_border"],height=1).pack(fill='x')
        inner=tk.Frame(row,bg=THEME["card_bg"],padx=12,pady=10)
        inner.pack(fill='x')
        left=tk.Frame(inner,bg=THEME["card_bg"])
        left.pack(side='left',fill='x',expand=True)
        name=p.get('name',p.get('nombre',''))
        price=p.get('price',p.get('precio',0))
        tk.Label(left,text=name,font=(FONT,10,'bold'),
                 bg=THEME["card_bg"],fg=THEME["txt_primary"],anchor='w').pack(anchor='w')
        tk.Label(left,text=f"{format_currency(price)}  ·  Stock: {stock}",
                 font=(FONT,9),bg=THEME["card_bg"],
                 fg=THEME["acc_green"] if stock>0 else THEME["acc_rose"]).pack(anchor='w',pady=(2,0))
        add=_btn(inner,"Agregar",lambda pr=p:self._add_product(pr),
                 THEME["acc_blue"],"＋")
        add.config(font=(FONT,9,'bold'),pady=5,padx=10)
        add.pack(side='right')

    def _add_product(self,product):
        stock=product.get('stock',product.get('quantity',0))
        pid=product['id']
        for item in self.cart:
            if item['product_id']==pid:
                if item['quantity']>=stock:
                    messagebox.showwarning("Stock",f"Stock máximo: {stock}"); return
                item['quantity']+=1
                item['subtotal']=item['quantity']*item['unit_price']
                self._update_cart_display(); return
        if stock<=0:
            messagebox.showwarning("Sin stock","Producto sin stock disponible"); return
        self.cart.append({'product_id':pid,'name':product.get('name',product.get('nombre','')),
            'unit_price':product.get('price',product.get('precio',0)),
            'quantity':1,'subtotal':product.get('price',product.get('precio',0)),
            'max_stock':stock})
        self._update_cart_display()

    def search_products(self):
        t=self.search_var.get().lower()
        f=[p for p in self.all_products if t in p.get('name','').lower()
           or t in (p.get('barcode','') or '').lower()] if t else self.all_products
        self._display_products(f)

    def remove_from_cart(self):
        sel=self.cart_tree.selection()
        if not sel: return
        vals=self.cart_tree.item(sel[0])['values']
        self.cart=[i for i in self.cart if i['name']!=vals[0]]
        self._update_cart_display()

    def clear_cart(self):
        if self.cart and messagebox.askyesno("Vaciar","¿Vaciar el carrito?"):
            self.cart=[]; self._update_cart_display()

    def _update_cart_display(self):
        for i in self.cart_tree.get_children():
            self.cart_tree.delete(i)
        for idx,item in enumerate(self.cart):
            tag='odd' if idx%2 else 'even'
            self.cart_tree.insert('','end',values=(
                item['name'],item['quantity'],
                format_currency(item['unit_price']),
                format_currency(item['subtotal'])),tags=(tag,))
        self.cart_tree.tag_configure('odd',background=THEME["row_odd"])
        self.cart_tree.tag_configure('even',background=THEME["row_even"])
        self._update_totals()

    def _update_totals(self):
        total=sum(i['subtotal'] for i in self.cart)
        self.total_label.config(text=format_currency(total))

    def show_checkout_dialog(self):
        if not self.cart:
            messagebox.showwarning("Carrito vacío","Agregue productos al carrito"); return
        total=sum(i['subtotal'] for i in self.cart)
        dlg=tk.Toplevel(self.parent)
        _set_icon(dlg)
        dlg.title("Finalizar Venta")
        dlg.resizable(False,False)
        dlg.configure(bg=THEME["ct_bg"])
        dlg.transient(self.parent)
        dlg.grab_set()
        w,h=520,660
        dlg.update_idletasks()
        sw,sh=dlg.winfo_screenwidth(),dlg.winfo_screenheight()
        dlg.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        # Botones PRIMERO
        btn_bar=tk.Frame(dlg,bg=THEME["card_bg"],padx=20,pady=14)
        btn_bar.pack(fill='x',side='bottom')
        tk.Frame(dlg,bg=THEME["card_border"],height=1).pack(fill='x',side='bottom')

        # Contenido scrollable
        outer=tk.Frame(dlg,bg=THEME["ct_bg"])
        outer.pack(fill='both',expand=True)

        # Header
        hdr=tk.Frame(outer,bg=THEME["sb_bg"],pady=16)
        hdr.pack(fill='x')
        tk.Label(hdr,text="Resumen de Venta",font=(FONT,14,'bold'),
                 bg=THEME["sb_bg"],fg="#fff").pack(anchor='w',padx=20)
        tk.Label(hdr,text=format_currency(total),font=(FONT,20,'bold'),
                 bg=THEME["sb_bg"],fg=THEME["acc_green"]).pack(anchor='w',padx=20,pady=(4,0))

        body=tk.Frame(outer,bg=THEME["ct_bg"],padx=20,pady=16)
        body.pack(fill='both',expand=True)

        # Tipo de venta
        tk.Label(body,text="Tipo de Venta",font=(FONT,10,'bold'),
                 bg=THEME["ct_bg"],fg=THEME["txt_secondary"]).pack(anchor='w',pady=(0,6))
        sale_type=tk.StringVar(value="cash")
        type_f=tk.Frame(body,bg=THEME["ct_bg"])
        type_f.pack(fill='x',pady=(0,14))
        for val,lbl in [("cash","💵  Contado"),("credit","💳  Crédito")]:
            rb=tk.Radiobutton(type_f,text=lbl,variable=sale_type,value=val,
               font=(FONT,10),bg=THEME["ct_bg"],fg=THEME["txt_primary"],
               selectcolor=THEME["ct_bg"],command=lambda:toggle())
            rb.pack(side='left',padx=(0,20))

        options=tk.Frame(body,bg=THEME["ct_bg"])
        options.pack(fill='x')

        # Frame contado
        cash_f=tk.Frame(options,bg=THEME["ct_bg"])
        tk.Label(cash_f,text="Método de Pago",font=(FONT,10,'bold'),
                 bg=THEME["ct_bg"],fg=THEME["txt_secondary"]).pack(anchor='w',pady=(0,4))
        pay_var=tk.StringVar(value="Efectivo")
        pay_cb=ttk.Combobox(cash_f,textvariable=pay_var,
            values=["Efectivo","Tarjeta Crédito","Tarjeta Débito","Transferencia"],
            state='readonly',font=(FONT,10))
        pay_cb.pack(fill='x',pady=(0,10))
        tk.Label(cash_f,text="Monto Pagado",font=(FONT,10,'bold'),
                 bg=THEME["ct_bg"],fg=THEME["txt_secondary"]).pack(anchor='w',pady=(0,4))
        paid_outer=tk.Frame(cash_f,bg=THEME["input_brd"])
        paid_inner=tk.Frame(paid_outer,bg=THEME["input_bg"])
        paid_inner.pack(fill='x',padx=1,pady=1)
        paid_e=tk.Entry(paid_inner,font=(FONT,12),bg=THEME["input_bg"],
                        fg=THEME["txt_primary"],relief='flat',bd=0,
                        insertbackground=THEME["acc_blue"])
        paid_e.pack(fill='x',padx=12,pady=9)
        paid_outer.pack(fill='x',pady=(0,10))
        paid_e.insert(0,str(int(total)))
        tk.Label(cash_f,text="Cambio",font=(FONT,10,'bold'),
                 bg=THEME["ct_bg"],fg=THEME["txt_secondary"]).pack(anchor='w',pady=(0,4))
        chg_lbl=tk.Label(cash_f,text="Gs. 0",font=(FONT,14,'bold'),
                 bg=THEME["ct_bg"],fg=THEME["acc_green"])
        chg_lbl.pack(anchor='w')
        def calc_change(*_):
            try:
                paid=float(paid_e.get())
                chg=paid-total
                chg_lbl.config(text="INSUFICIENTE" if chg<0 else format_currency(chg),
                               fg=THEME["acc_rose"] if chg<0 else THEME["acc_green"])
            except: chg_lbl.config(text="—")
        paid_e.bind('<KeyRelease>',calc_change)
        calc_change()

        # Frame crédito
        cred_f=tk.Frame(options,bg=THEME["ct_bg"])
        customers=self.db.get_all_customers()
        tk.Label(cred_f,text="Cliente",font=(FONT,10,'bold'),
                 bg=THEME["ct_bg"],fg=THEME["txt_secondary"]).pack(anchor='w',pady=(0,4))
        cust_var=tk.StringVar()
        ttk.Combobox(cred_f,textvariable=cust_var,font=(FONT,10),
            values=[f"{c['id']} - {c.get('name',c.get('nombre',''))}" for c in customers]
            ).pack(fill='x',pady=(0,10))
        tk.Label(cred_f,text=f"Cuota Inicial (mín. {format_currency(int(total*.1))})",
                 font=(FONT,10,'bold'),bg=THEME["ct_bg"],fg=THEME["txt_secondary"]).pack(anchor='w',pady=(0,4))
        down_outer=tk.Frame(cred_f,bg=THEME["input_brd"])
        down_inner=tk.Frame(down_outer,bg=THEME["input_bg"])
        down_inner.pack(fill='x',padx=1,pady=1)
        down_e=tk.Entry(down_inner,font=(FONT,12),bg=THEME["input_bg"],
                        fg=THEME["txt_primary"],relief='flat',bd=0)
        down_e.pack(fill='x',padx=12,pady=9)
        down_outer.pack(fill='x',pady=(0,10))
        down_e.insert(0,str(int(total*.1)))
        freq_var=tk.StringVar(value="monthly")
        tk.Label(cred_f,text="Frecuencia",font=(FONT,10,'bold'),
                 bg=THEME["ct_bg"],fg=THEME["txt_secondary"]).pack(anchor='w',pady=(0,4))
        freq_f=tk.Frame(cred_f,bg=THEME["ct_bg"])
        freq_f.pack(fill='x',pady=(0,10))
        from config.settings import CREDIT
        for key,val in CREDIT['payment_frequencies'].items():
            tk.Radiobutton(freq_f,text=val['name'],variable=freq_var,value=key,
               font=(FONT,10),bg=THEME["ct_bg"],selectcolor=THEME["ct_bg"]).pack(side='left',padx=(0,12))
        tk.Label(cred_f,text="Cuotas (1-24)",font=(FONT,10,'bold'),
                 bg=THEME["ct_bg"],fg=THEME["txt_secondary"]).pack(anchor='w',pady=(0,4))
        inst_outer=tk.Frame(cred_f,bg=THEME["input_brd"])
        inst_inner=tk.Frame(inst_outer,bg=THEME["input_bg"])
        inst_inner.pack(fill='x',padx=1,pady=1)
        inst_e=tk.Entry(inst_inner,font=(FONT,12),bg=THEME["input_bg"],
                        fg=THEME["txt_primary"],relief='flat',bd=0)
        inst_e.pack(fill='x',padx=12,pady=9)
        inst_outer.pack(fill='x')
        inst_e.insert(0,"6")

        def toggle():
            if sale_type.get()=="credit":
                cash_f.pack_forget(); cred_f.pack(fill='x')
            else:
                cred_f.pack_forget(); cash_f.pack(fill='x')
        cash_f.pack(fill='x')

        def finalize():
            try:
                from datetime import timedelta
                if sale_type.get()=="cash":
                    paid=float(paid_e.get())
                    if paid<total:
                        messagebox.showerror("Error","Monto insuficiente",parent=dlg); return
                    items=[{'product_id':i['product_id'],'quantity':i['quantity'],
                            'unit_price':i['unit_price'],'subtotal':i['subtotal']} for i in self.cart]
                    sid=self.db.create_sale(self.selected_customer_id,total,pay_var.get(),
                                            paid,paid-total,items,False)
                    self._show_ticket(sid,total,pay_var.get(),paid,paid-total)
                    messagebox.showinfo("✅ Venta registrada",f"Venta #{sid} completada")
                else:
                    if not cust_var.get():
                        messagebox.showerror("Error","Seleccione un cliente",parent=dlg); return
                    cid=int(cust_var.get().split(' - ')[0])
                    down=float(down_e.get())
                    inst=int(inst_e.get())
                    if down<total*.1:
                        messagebox.showerror("Error",f"Mínimo {format_currency(total*.1)}",parent=dlg); return
                    if not 1<=inst<=24:
                        messagebox.showerror("Error","Cuotas deben ser 1-24",parent=dlg); return
                    rem=total-down; inst_amt=rem/inst
                    freq_days=CREDIT['payment_frequencies'][freq_var.get()]['days']
                    first_date=(datetime.now()+timedelta(days=freq_days)).strftime('%Y-%m-%d')
                    items=[{'product_id':i['product_id'],'quantity':i['quantity'],
                            'unit_price':i['unit_price'],'subtotal':i['subtotal']} for i in self.cart]
                    sid=self.db.create_sale(cid,total,"Crédito",down,0,items,True)
                    self.db.create_credit_sale(sid,cid,total,down,freq_var.get(),inst_amt,inst,first_date)
                    messagebox.showinfo("✅ Crédito registrado",
                        f"Total: {format_currency(total)}\nInicial: {format_currency(down)}\n"
                        f"Saldo: {format_currency(rem)}\n{inst} cuotas de {format_currency(inst_amt)}")
                self.cart=[]; self._update_cart_display(); dlg.destroy()
            except Exception as e:
                messagebox.showerror("Error",str(e),parent=dlg)

        _btn(btn_bar,"CONFIRMAR",finalize,THEME["acc_green"],"☑").pack(side='left',padx=(0,8))
        _btn(btn_bar,"Cancelar",dlg.destroy,THEME["btn_secondary"],"✕").pack(side='left')

    def _show_ticket(self,sale_id,total,method,paid,change):
        tw=tk.Toplevel(self.parent)
        _set_icon(tw)
        tw.title("Ticket #"+str(sale_id))
        tw.configure(bg='white')
        tw.transient(self.parent)
        tw.grab_set()
        tw.withdraw()  # ocultar mientras se construye
        tw.attributes('-topmost',True)
        tw.geometry("440x620")

        # Obtener datos reales de la empresa desde la base de datos
        try:
            from utils.company_header import get_company
            co=get_company()
        except Exception:
            co={}

        empresa  = co.get('razon_social') or BUSINESS.get('name','Venialgo Sistemas')
        ruc      = co.get('ruc','')
        telefono = co.get('telefono','')
        direccion= co.get('direccion','')
        ciudad   = co.get('ciudad','')
        email    = co.get('email','')
        web      = co.get('web','')

        from utils.formatters import format_currency

        # Rollo 75mm — 44 caracteres por línea a Courier New 10pt
        W        = 44
        SEP      = '-' * W
        SEP2     = '=' * W
        now      = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        # Columnas: Producto 18 | Cant 4 | Precio 11 | Sub 11 = 44
        COL_PROD = 18
        COL_CANT =  4
        COL_PREC = 11
        COL_SUB  = 11

        def fmt_num(n):
            try: return "{:,}".format(int(n)).replace(",",".")
            except: return str(n)

        def fmt_row(nombre, cant, precio, sub):
            n = nombre[:COL_PROD].ljust(COL_PROD)
            c = str(cant).rjust(COL_CANT)
            p = fmt_num(precio).rjust(COL_PREC)
            s = fmt_num(sub).rjust(COL_SUB)
            return n + c + p + s

        def fmt_total_row(label, value):
            return label.rjust(W - COL_SUB) + format_currency(value).rjust(COL_SUB)

        lines=[]
        lines.append(SEP2)
        lines.append(empresa.center(W))
        if ruc:       lines.append(("RUC: " + ruc).center(W))
        if direccion: lines.append(direccion[:W].center(W))
        if ciudad:    lines.append(ciudad[:W].center(W))
        if telefono:  lines.append(("Tel: " + telefono).center(W))
        if email:     lines.append(email[:W].center(W))
        if web:       lines.append(web[:W].center(W))
        lines.append(SEP2)
        lines.append(("TICKET DE VENTA #" + str(sale_id)).center(W))
        lines.append(("Fecha: " + now).center(W))
        lines.append(("Metodo: " + method).center(W))
        lines.append(SEP)

        # Cabecera columnas con separador visual
        hdr = "PRODUCTO".ljust(COL_PROD) + "CANT".rjust(COL_CANT) + "PRECIO".rjust(COL_PREC) + "SUBTOTAL".rjust(COL_SUB)
        lines.append(hdr)
        # Separadores por columna
        lines.append('-'*COL_PROD + '-'*COL_CANT + '-'*COL_PREC + '-'*COL_SUB)

        for item in self.cart:
            lines.append(fmt_row(item['name'], item['quantity'],
                                 item['unit_price'], item['subtotal']))
            # Si el nombre es largo, segunda línea con continuación
            if len(item['name']) > COL_PROD:
                resto = item['name'][COL_PROD:][:COL_PROD]
                lines.append(' ' + resto)

        lines.append(SEP)
        lines.append(fmt_total_row("TOTAL:", total))
        lines.append(fmt_total_row("Pagado:", paid))
        chg = paid - total
        lines.append(fmt_total_row("Cambio:", max(0, chg)))
        lines.append(SEP2)
        lines.append("  Gracias por su compra!  ".center(W))
        lines.append(SEP)
        lines.append("Venialgo Sistemas POS".center(W))
        lines.append("davenialgo@proton.me".center(W))
        lines.append("WhatsApp: +595 994-686 493".center(W))
        lines.append("www.venialgosistemas.com".center(W))
        lines.append(SEP2)

        txt="\n".join(lines)

        # Detectar impresora de tickets al abrir la ventana
        printer_name=self._detect_ticket_printer()

        # Mostrar ticket
        st=scrolledtext.ScrolledText(tw,font=('Courier New',10),bg='white',padx=16,pady=12)
        st.pack(fill='both',expand=True,padx=12,pady=12)
        st.insert('1.0',txt); st.config(state='disabled')

        # Barra inferior con info de impresora
        info_bar=tk.Frame(tw,bg='#F9FAFB',pady=6)
        info_bar.pack(fill='x',padx=12)
        if printer_name:
            tk.Label(info_bar,text=f"🖨  {printer_name}",
                     font=('Segoe UI',8),bg='#F9FAFB',fg='#059669').pack(side='left',padx=8)
        else:
            tk.Label(info_bar,text="⚠  Sin impresora detectada",
                     font=('Segoe UI',8),bg='#F9FAFB',fg='#D97706').pack(side='left',padx=8)

        btn_row=tk.Frame(tw,bg='white'); btn_row.pack(pady=(4,12))

        # Selector de impresora
        printers=self._get_all_printers()
        if printers:
            printer_var=tk.StringVar(value=printer_name or printers[0])
            printer_cb=ttk.Combobox(btn_row,textvariable=printer_var,
                                    values=printers,state='readonly',
                                    font=('Segoe UI',9),width=28)
            printer_cb.pack(side='left',padx=(0,8))
            _btn(btn_row,"Imprimir",
                 lambda:self._print_ticket(txt,printer_var.get()),
                 THEME["acc_blue"],"🖨").pack(side='left',padx=(0,4))
        else:
            _btn(btn_row,"Imprimir",
                 lambda:self._print_ticket(txt,None),
                 THEME["acc_blue"],"🖨").pack(side='left',padx=(0,4))

        _btn(btn_row,"Cerrar",tw.destroy,THEME["btn_secondary"],"✕").pack(side='left',padx=4)

    # ── Detección de impresoras ───────────────────────────────

    def _get_all_printers(self):
        """Devuelve lista de todas las impresoras instaladas en Windows."""
        printers=[]
        try:
            import winreg
            key=winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Print\Printers")
            i=0
            while True:
                try:
                    printers.append(winreg.EnumKey(key,i)); i+=1
                except OSError: break
            winreg.CloseKey(key)
        except Exception:
            # Fallback: win32print si está disponible
            try:
                import win32print
                printers=[p[2] for p in win32print.EnumPrinters(
                    win32print.PRINTER_ENUM_LOCAL|win32print.PRINTER_ENUM_CONNECTIONS)]
            except Exception:
                pass
        return printers

    def _detect_ticket_printer(self):
        """
        Detecta automáticamente la impresora de tickets térmica.
        Prioridad:
          1. Impresoras con palabras clave de ticket/térmica en el nombre
          2. Impresora predeterminada del sistema si no hay ninguna específica
        """
        # Palabras clave que indican impresoras de tickets
        TICKET_KEYWORDS = [
            'pos','receipt','ticket','thermal','termic',
            'epson tm','star','bixolon','citizen','sewoo',
            'xprinter','rongta','gprinter','80mm','58mm',
            'tsp','rp-','tmt','pos-',
        ]
        printers=self._get_all_printers()
        if not printers:
            return None

        # Buscar por palabras clave (case-insensitive)
        for p in printers:
            pl=p.lower()
            if any(kw in pl for kw in TICKET_KEYWORDS):
                return p

        # Si no encontró térmica, retornar la impresora predeterminada
        try:
            import winreg
            key=winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows NT\CurrentVersion\Windows")
            default,_=winreg.QueryValueEx(key,"Device")
            winreg.CloseKey(key)
            default_name=default.split(',')[0].strip()
            if default_name in printers:
                return default_name
        except Exception:
            pass

        # Último recurso: primera impresora de la lista
        return printers[0] if printers else None

    def _print_ticket(self, txt, printer_name=None):
        """
        Imprime el ticket directo a la impresora térmica.
        Intenta 3 métodos en orden de confiabilidad.
        """
        import sys, os, tempfile, subprocess

        # Preparar bytes del ticket (cp1252 para Windows, utf-8 para Linux)
        encoding = 'cp1252' if sys.platform == 'win32' else 'utf-8'
        raw_bytes = (txt + '\n\n\n\n').encode(encoding, errors='replace')

        # ── MÉTODO 1: win32print — más directo y confiable ────
        if sys.platform == 'win32':
            if self._print_win32(raw_bytes, printer_name):
                return

        # ── MÉTODO 2: PowerShell Out-Printer ──────────────────
        if sys.platform == 'win32':
            if self._print_powershell(txt, printer_name):
                return

        # ── MÉTODO 3: Notepad /p (siempre disponible en Win) ──
        if sys.platform == 'win32':
            if self._print_notepad(txt, printer_name):
                return

        # ── MÉTODO 4: lp (Linux/Mac) ──────────────────────────
        if sys.platform != 'win32':
            try:
                with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt',
                                                 delete=False) as f:
                    f.write(raw_bytes); path=f.name
                cmd = ['lp'] + (['-d', printer_name] if printer_name else []) + [path]
                subprocess.run(cmd, check=True)
                messagebox.showinfo("✅ Impreso", "Ticket enviado a la impresora")
                return
            except Exception as e:
                messagebox.showerror("Error", str(e))
                return

        messagebox.showerror("Error al imprimir",
            "No se pudo imprimir. Verificá que la impresora esté encendida y conectada.")

    def _print_win32(self, raw_bytes, printer_name=None):
        """Impresión RAW directa con win32print. Más compatible con térmicas."""
        try:
            import win32print
            printer = printer_name or win32print.GetDefaultPrinter()
            if not printer:
                return False
            handle = win32print.OpenPrinter(printer)
            try:
                job = win32print.StartDocPrinter(handle, 1,
                    ("Ticket POS", None, "RAW"))
                try:
                    win32print.StartPagePrinter(handle)
                    win32print.WritePrinter(handle, raw_bytes)
                    win32print.EndPagePrinter(handle)
                finally:
                    win32print.EndDocPrinter(handle)
            finally:
                win32print.ClosePrinter(handle)
            messagebox.showinfo("✅ Impreso", f"Ticket enviado a:\n{printer}")
            return True
        except ImportError:
            return False   # win32print no instalado
        except Exception as e:
            messagebox.showerror("Error win32print", str(e))
            return False

    def _print_powershell(self, txt, printer_name=None):
        """Impresión via PowerShell Out-Printer."""
        import tempfile, subprocess
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                             delete=False, encoding='utf-8') as f:
                f.write(txt); path = f.name

            ps_cmd = f'Get-Content -Path "{path}" | '
            if printer_name:
                ps_cmd += f'Out-Printer -Name "{printer_name}"'
            else:
                ps_cmd += 'Out-Printer'

            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', ps_cmd],
                capture_output=True, timeout=15)

            try: os.unlink(path)
            except: pass

            if result.returncode == 0:
                messagebox.showinfo("✅ Impreso", "Ticket enviado a la impresora")
                return True
            return False
        except Exception:
            return False

    def _print_notepad(self, txt, printer_name=None):
        """Último recurso: imprimir via Notepad silencioso."""
        import tempfile, subprocess, os, time
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                             delete=False, encoding='cp1252',
                                             errors='replace') as f:
                f.write(txt); path = f.name

            if printer_name:
                # Notepad con impresora específica
                subprocess.Popen(
                    ['notepad.exe', '/pt', path, printer_name],
                    creationflags=0x08000000)  # CREATE_NO_WINDOW
            else:
                subprocess.Popen(
                    ['notepad.exe', '/p', path],
                    creationflags=0x08000000)

            # Esperar que notepad envíe el job y luego borrar el archivo
            def _cleanup():
                time.sleep(5)
                try: os.unlink(path)
                except: pass
            import threading
            threading.Thread(target=_cleanup, daemon=True).start()

            messagebox.showinfo("✅ Impreso", "Ticket enviado a la impresora")
            return True
        except Exception:
            return False
