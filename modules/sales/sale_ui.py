"""Módulo Punto de Venta — Diseño moderno Venialgo POS"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from config.settings import COLORS, FONTS as _F, SPACING, BUTTON_STYLES, BUSINESS
from utils.formatters import format_currency, generate_ticket

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
        tw.title(f"Ticket #{sale_id}")
        tw.geometry("440x580")
        tw.configure(bg='white')
        tw.update_idletasks()
        sw,sh=tw.winfo_screenwidth(),tw.winfo_screenheight()
        tw.geometry(f"440x580+{(sw-440)//2}+{(sh-580)//2}")
        ticket_data={'id':sale_id,'date':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'items':self.cart,'total':total,'payment_method':method,
            'amount_paid':paid,'change':change}
        txt=generate_ticket(ticket_data,BUSINESS['name'])
        st=scrolledtext.ScrolledText(tw,font=('Courier New',10),bg='white',padx=20,pady=20)
        st.pack(fill='both',expand=True,padx=16,pady=16)
        st.insert('1.0',txt); st.config(state='disabled')
        _btn(tw,"Cerrar",tw.destroy,THEME["btn_secondary"]).pack(pady=12)
