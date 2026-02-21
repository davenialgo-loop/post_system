"""Módulo Gestión de Créditos — Diseño moderno Venialgo POS"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from config.settings import COLORS, FONTS as _F, SPACING, BUTTON_STYLES, CREDIT
from utils.formatters import format_currency, format_date
try:
    from utils.window_icon import set_icon as _set_icon
except ImportError:
    def _set_icon(w): pass

THEME = {"ct_bg":"#F9FAFB","card_bg":"#FFFFFF","card_border":"#E5E7EB","sb_bg":"#111827",
    "txt_primary":"#111827","txt_secondary":"#6B7280","txt_white":"#FFFFFF",
    "acc_blue":"#2563EB","acc_green":"#059669","acc_amber":"#D97706","acc_rose":"#E11D48",
    "acc_purple":"#7C3AED","btn_danger":"#DC2626","btn_secondary":"#6B7280",
    "input_bg":"#FFFFFF","input_brd":"#D1D5DB","input_foc":"#2563EB",
    "row_odd":"#F9FAFB","row_even":"#FFFFFF"}
FONT="Segoe UI"

def _btn(parent, text, cmd, bg, icon="", **kw):
    t = (icon + "  " + text) if icon else text
    _DISABLED = "#9CA3AF"
    def _dk(c):
        r,g,b = int(c[1:3],16), int(c[3:5],16), int(c[5:7],16)
        return "#{:02x}{:02x}{:02x}".format(max(0,int(r*.82)),max(0,int(g*.82)),max(0,int(b*.82)))
    _state = {"on": False}
    lbl = tk.Label(parent, text=t, font=(FONT,10,"bold"),
                   bg=_DISABLED, fg="#ffffff",
                   cursor="arrow", padx=14, pady=8, **kw)
    def _on_enter(_=None):
        if _state["on"]: lbl.config(bg=_dk(bg))
    def _on_leave(_=None):
        lbl.config(bg=bg if _state["on"] else _DISABLED)
    def _on_click(_=None):
        if _state["on"] and cmd:
            lbl.config(bg=_dk(_dk(bg)))
            lbl.after(120, lambda: lbl.config(bg=bg))
            cmd()
    lbl.bind("<Enter>",           _on_enter)
    lbl.bind("<Leave>",           _on_leave)
    lbl.bind("<ButtonRelease-1>", _on_click)
    def enable():
        _state["on"] = True
        lbl.config(bg=bg, fg="#ffffff", cursor="hand2")
    def disable():
        _state["on"] = False
        lbl.config(bg=_DISABLED, fg="#ffffff", cursor="arrow")
    lbl.enable  = enable
    lbl.disable = disable
    return lbl

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
    win.update_idletasks()
    sw,sh=win.winfo_screenwidth(),win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

class CreditsModule:
    def __init__(self,parent,db_manager):
        self.parent=parent; self.db=db_manager
        self.selected_credit_id=None
        _setup_styles()
        self._build(); self.load_credits()

    def _stat_card(self,parent,title,value,accent):
        outer=tk.Frame(parent,bg=THEME["card_border"])
        inner=tk.Frame(outer,bg=THEME["card_bg"],padx=16,pady=14)
        inner.pack(fill='both',expand=True,padx=1,pady=1)
        tk.Label(inner,text=title,font=(FONT,9),bg=THEME["card_bg"],fg=THEME["txt_secondary"]).pack(anchor='w')
        lbl=tk.Label(inner,text=value,font=(FONT,18,'bold'),bg=THEME["card_bg"],fg=accent)
        lbl.pack(anchor='w',pady=(4,0))
        tk.Frame(inner,bg=accent,height=3).pack(fill='x',pady=(10,0))
        inner.value_label=lbl
        outer.value_label=lbl
        return outer

    def _build(self):
        bg=THEME["ct_bg"]
        # Header
        hdr=tk.Frame(self.parent,bg=bg)
        hdr.pack(fill='x',padx=28,pady=(20,0))
        tk.Label(hdr,text="💳  Gestión de Créditos",font=(FONT,16,'bold'),
                 bg=bg,fg=THEME["txt_primary"]).pack(side='left')
        tk.Frame(self.parent,bg=THEME["card_border"],height=1).pack(fill='x',padx=28,pady=(10,14))

        # Filtros
        flt=tk.Frame(self.parent,bg=bg,padx=28)
        flt.pack(fill='x',pady=(0,12))
        tk.Label(flt,text="Filtrar:",font=(FONT,10,'bold'),bg=bg,fg=THEME["txt_secondary"]).pack(side='left',padx=(0,10))
        self.status_var=tk.StringVar(value='all')
        for val,lbl in [('all','Todos'),('active','Activos'),('paid','Pagados'),('overdue','Vencidos')]:
            rb=tk.Radiobutton(flt,text=lbl,variable=self.status_var,value=val,
               font=(FONT,10),bg=bg,fg=THEME["txt_primary"],selectcolor=bg,
               command=self.load_credits)
            rb.pack(side='left',padx=(0,16))

        # Cards estadísticas
        stats_row=tk.Frame(self.parent,bg=bg)
        stats_row.pack(fill='x',padx=24,pady=(0,14))
        self.card_active  =self._stat_card(stats_row,"Créditos Activos","0",THEME["acc_blue"])
        self.card_active.grid(row=0,column=0,sticky='nsew',padx=4)
        self.card_pending =self._stat_card(stats_row,"Total por Cobrar","Gs. 0",THEME["acc_amber"])
        self.card_pending.grid(row=0,column=1,sticky='nsew',padx=4)
        self.card_overdue =self._stat_card(stats_row,"Vencidos","0",THEME["acc_rose"])
        self.card_overdue.grid(row=0,column=2,sticky='nsew',padx=4)
        for i in range(3): stats_row.columnconfigure(i,weight=1)

        # Tabla
        tbl_outer=tk.Frame(self.parent,bg=THEME["card_border"])
        tbl_outer.pack(fill='both',expand=True,padx=24,pady=(0,10))
        tbl=tk.Frame(tbl_outer,bg=THEME["card_bg"])
        tbl.pack(fill='both',expand=True,padx=1,pady=1)

        cols=('ID','Cliente','Total','Inicial','Saldo','Cuota','Pagadas','Cuotas','Próximo','Estado')
        self.tree=ttk.Treeview(tbl,columns=cols,show='headings',style='POS.Treeview')
        for col,w in zip(cols,[45,150,100,90,90,90,60,60,100,80]):
            self.tree.heading(col,text=col)
            self.tree.column(col,width=w,anchor='center' if col not in('Cliente',) else 'w')
        sb=ttk.Scrollbar(tbl,orient='vertical',command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side='right',fill='y',padx=(0,4),pady=4)
        self.tree.pack(fill='both',expand=True,padx=4,pady=4)
        self.tree.bind('<<TreeviewSelect>>',self._on_select)
        self.tree.bind('<Double-Button-1>',lambda _:self.show_credit_details())
        self.tree.tag_configure('active',background=THEME["row_even"])
        self.tree.tag_configure('paid',background='#F0FDF4')
        self.tree.tag_configure('overdue',background='#FFF1F2')

        # Botones acción
        act=tk.Frame(self.parent,bg=bg,padx=24,pady=10)
        act.pack(fill='x')
        self.btn_pay=_btn(act,"Registrar Pago",self.show_payment_dialog,THEME["acc_green"],"💰")
        self.btn_pay.pack(side='left',padx=(0,8))
        self.btn_hist=_btn(act,"Ver Historial",self.show_payment_history,THEME["acc_blue"],"📋")
        self.btn_hist.pack(side='left',padx=(0,8))
        self.btn_date=_btn(act,"Cambiar Fecha",self.show_change_date_dialog,THEME["btn_secondary"],"📅")
        self.btn_date.pack(side='left')

    def load_credits(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        sf=self.status_var.get()
        credits=self.db.get_all_credit_sales() if sf=='all' \
            else self.db.get_overdue_credits() if sf=='overdue' \
            else self.db.get_all_credit_sales(sf)
        active_count=0; total_pending=0; overdue_count=0
        today=datetime.now().strftime('%Y-%m-%d')
        for c in credits:
            status=c.get('status','active')
            nxt=c.get('next_payment_date','')
            is_overdue=status=='active' and nxt and nxt<today
            if is_overdue: overdue_count+=1; tag='overdue'
            elif status=='active': tag='active'
            else: tag='paid'
            if status=='active': active_count+=1; total_pending+=c.get('remaining_balance',0)
            status_txt='Vencido' if is_overdue else ('Activo' if status=='active' else 'Pagado')
            self.tree.insert('','end',tags=(tag,),values=(
                c.get('id',''),c.get('customer_name',''),
                format_currency(c.get('total_amount',0)),
                format_currency(c.get('down_payment',0)),
                format_currency(c.get('remaining_balance',0)),
                format_currency(c.get('installment_amount',0)),
                c.get('paid_installments',0),c.get('total_installments',0),
                nxt or '—',status_txt))
        self.card_active.value_label.config(text=str(active_count))
        self.card_pending.value_label.config(text=format_currency(total_pending))
        self.card_overdue.value_label.config(text=str(overdue_count))

    def _on_select(self,_=None):
        sel=self.tree.selection()
        if sel:
            self.selected_credit_id=self.tree.item(sel[0])['values'][0]
            status=self.tree.item(sel[0])['values'][9]
            can=status in('Activo','Vencido')
            self.btn_pay.enable() if can else self.btn_pay.disable()
            self.btn_date.enable() if can else self.btn_date.disable()
            self.btn_hist.enable()
        else:
            self.selected_credit_id=None
            for b in [self.btn_pay,self.btn_hist,self.btn_date]: b.disable()

    def show_credit_details(self):
        if not self.selected_credit_id: return
        c=self.db.get_credit_sale_by_id(self.selected_credit_id)
        if not c: return
        dlg=tk.Toplevel(self.parent)
        _set_icon(dlg); dlg.title(f"Crédito #{c['id']}")
        dlg.configure(bg=THEME["card_bg"]); dlg.resizable(False,False)
        dlg.transient(self.parent); _center(dlg,480,460)
        hdr=tk.Frame(dlg,bg=THEME["sb_bg"],pady=14)
        hdr.pack(fill='x')
        tk.Label(hdr,text=f"Crédito #{c['id']} — {c.get('customer_name','')}",
                 font=(FONT,13,'bold'),bg=THEME["sb_bg"],fg="#fff").pack(anchor='w',padx=20)
        content=tk.Frame(dlg,bg=THEME["card_bg"],padx=24,pady=16)
        content.pack(fill='both',expand=True)
        rows=[("Cliente:",c.get('customer_name','')),
              ("Total de venta:",format_currency(c.get('total_amount',0))),
              ("Cuota inicial:",format_currency(c.get('down_payment',0))),
              ("Saldo restante:",format_currency(c.get('remaining_balance',0))),
              ("Monto por cuota:",format_currency(c.get('installment_amount',0))),
              ("Cuotas pagadas:",f"{c.get('paid_installments',0)} de {c.get('total_installments',0)}"),
              ("Próximo pago:",c.get('next_payment_date','—')),
              ("Estado:",'Activo' if c.get('status')=='active' else 'Pagado')]
        for i,(lbl,val) in enumerate(rows):
            tk.Label(content,text=lbl,font=(FONT,9,'bold'),bg=THEME["card_bg"],
                     fg=THEME["txt_secondary"],anchor='w').grid(row=i,column=0,sticky='w',pady=5)
            tk.Label(content,text=str(val),font=(FONT,10),bg=THEME["card_bg"],
                     fg=THEME["txt_primary"],anchor='w').grid(row=i,column=1,sticky='w',padx=20,pady=5)
        _btn(dlg,"Cerrar",dlg.destroy,THEME["btn_secondary"]).pack(pady=12)

    def show_payment_dialog(self):
        if not self.selected_credit_id: return
        c=self.db.get_credit_sale_by_id(self.selected_credit_id)
        if not c: return
        dlg=tk.Toplevel(self.parent)
        _set_icon(dlg); dlg.title("Registrar Pago")
        dlg.configure(bg=THEME["ct_bg"]); dlg.resizable(False,False)
        dlg.transient(self.parent); dlg.grab_set(); _center(dlg,420,440)

        # Botones PRIMERO
        btn_bar=tk.Frame(dlg,bg=THEME["card_bg"],padx=16,pady=12)
        btn_bar.pack(fill='x',side='bottom')
        tk.Frame(dlg,bg=THEME["card_border"],height=1).pack(fill='x',side='bottom')

        hdr=tk.Frame(dlg,bg=THEME["sb_bg"],pady=12)
        hdr.pack(fill='x')
        tk.Label(hdr,text=f"💰  Registrar Pago — {c.get('customer_name','')}",
                 font=(FONT,12,'bold'),bg=THEME["sb_bg"],fg="#fff").pack(anchor='w',padx=16)

        canvas=tk.Canvas(dlg,bg=THEME["ct_bg"],highlightthickness=0)
        canvas.pack(fill='both',expand=True)
        body=tk.Frame(canvas,bg=THEME["ct_bg"],padx=20,pady=16)
        canvas.create_window((0,0),window=body,anchor='nw',tags='body')
        def _rsz(e): canvas.itemconfig('body',width=e.width)
        def _srg(e): canvas.configure(scrollregion=canvas.bbox('all'))
        canvas.bind('<Configure>',_rsz); body.bind('<Configure>',_srg)
        tk.Label(body,text=f"Saldo actual: {format_currency(c.get('remaining_balance',0))}",
                 font=(FONT,12,'bold'),bg=THEME["ct_bg"],fg=THEME["acc_rose"]).pack(anchor='w',pady=(0,4))
        tk.Label(body,text=f"Cuota sugerida: {format_currency(c.get('installment_amount',0))}",
                 font=(FONT,10),bg=THEME["ct_bg"],fg=THEME["acc_green"]).pack(anchor='w',pady=(0,14))
        tk.Label(body,text="Monto a Pagar",font=(FONT,10,'bold'),
                 bg=THEME["ct_bg"],fg=THEME["txt_secondary"]).pack(anchor='w',pady=(0,4))
        amt_outer=tk.Frame(body,bg=THEME["input_brd"])
        amt_inner=tk.Frame(amt_outer,bg=THEME["input_bg"])
        amt_inner.pack(fill='x',padx=1,pady=1)
        amt_e=tk.Entry(amt_inner,font=(FONT,13),bg=THEME["input_bg"],
                       fg=THEME["txt_primary"],relief='flat',bd=0)
        amt_e.pack(fill='x',padx=12,pady=10)
        amt_outer.pack(fill='x',pady=(0,14))
        amt_e.insert(0,str(int(c.get('installment_amount',0)))); amt_e.focus()
        tk.Label(body,text="Notas (opcional)",font=(FONT,10,'bold'),
                 bg=THEME["ct_bg"],fg=THEME["txt_secondary"]).pack(anchor='w',pady=(0,4))
        notes_t=tk.Text(body,font=(FONT,10),height=3,
                        bg=THEME["input_bg"],relief='solid',bd=1,fg=THEME["txt_primary"])
        notes_t.pack(fill='x')

        def register():
            try:
                amt=float(amt_e.get())
                if amt<=0: messagebox.showerror("Error","Monto debe ser mayor a 0",parent=dlg); return
                if amt>c.get('remaining_balance',0):
                    if not messagebox.askyesno("Confirmar",f"Monto mayor al saldo. ¿Continuar?",parent=dlg): return
                self.db.add_credit_payment(self.selected_credit_id,amt,notes_t.get('1.0','end').strip())
                messagebox.showinfo("✅ Pago registrado","Pago registrado correctamente",parent=dlg)
                self.load_credits(); dlg.destroy()
            except ValueError: messagebox.showerror("Error","Ingrese un monto válido",parent=dlg)
            except Exception as e: messagebox.showerror("Error",str(e),parent=dlg)

        _btn(btn_bar,"Registrar Pago",register,THEME["acc_green"],"💰").pack(side='left',padx=(0,8))
        _btn(btn_bar,"Cancelar",dlg.destroy,THEME["btn_secondary"],"✕").pack(side='left')

    def show_payment_history(self):
        if not self.selected_credit_id: return
        c=self.db.get_credit_sale_by_id(self.selected_credit_id)
        payments=self.db.get_credit_payments(self.selected_credit_id)
        dlg=tk.Toplevel(self.parent)
        _set_icon(dlg); dlg.title("Historial de Pagos")
        dlg.configure(bg=THEME["ct_bg"]); dlg.transient(self.parent); _center(dlg,600,440)
        hdr=tk.Frame(dlg,bg=THEME["sb_bg"],pady=12); hdr.pack(fill='x')
        tk.Label(hdr,text=f"📋  Historial — {c.get('customer_name','')}",
                 font=(FONT,12,'bold'),bg=THEME["sb_bg"],fg="#fff").pack(anchor='w',padx=16)
        tbl=tk.Frame(dlg,bg=THEME["card_bg"]); tbl.pack(fill='both',expand=True,padx=16,pady=16)
        cols=('Fecha','Monto','Notas')
        tree=ttk.Treeview(tbl,columns=cols,show='headings',height=10,style='POS.Treeview')
        for col,w in zip(cols,[160,120,280]):
            tree.heading(col,text=col); tree.column(col,width=w,anchor='w' if col=='Notas' else 'center')
        sb=ttk.Scrollbar(tbl,orient='vertical',command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side='right',fill='y'); tree.pack(fill='both',expand=True)
        total_paid=0
        for i,p in enumerate(payments):
            tree.insert('','end',tags=('odd' if i%2 else 'even',),values=(
                format_date(p.get('payment_date','')),format_currency(p.get('amount',0)),p.get('notes','') or '—'))
            total_paid+=p.get('amount',0)
        tree.tag_configure('odd',background=THEME["row_odd"]); tree.tag_configure('even',background=THEME["row_even"])
        sum_f=tk.Frame(dlg,bg=THEME["card_bg"],padx=16,pady=12); sum_f.pack(fill='x')
        tk.Label(sum_f,text=f"Total pagado: {format_currency(total_paid)}",font=(FONT,10,'bold'),
                 bg=THEME["card_bg"],fg=THEME["acc_green"]).pack(side='left')
        tk.Label(sum_f,text=f"Saldo restante: {format_currency(c.get('remaining_balance',0))}",
                 font=(FONT,10,'bold'),bg=THEME["card_bg"],fg=THEME["acc_rose"]).pack(side='right')
        _btn(dlg,"Cerrar",dlg.destroy,THEME["btn_secondary"]).pack(pady=8)

    def show_change_date_dialog(self):
        if not self.selected_credit_id: return
        c=self.db.get_credit_sale_by_id(self.selected_credit_id)
        dlg=tk.Toplevel(self.parent)
        _set_icon(dlg); dlg.title("Cambiar Fecha de Pago")
        dlg.configure(bg=THEME["ct_bg"]); dlg.resizable(False,False)
        dlg.transient(self.parent); dlg.grab_set(); _center(dlg,400,300)
        # Botones PRIMERO
        btn_bar=tk.Frame(dlg,bg=THEME["card_bg"],padx=16,pady=12)
        btn_bar.pack(fill='x',side='bottom')
        tk.Frame(dlg,bg=THEME["card_border"],height=1).pack(fill='x',side='bottom')
        hdr=tk.Frame(dlg,bg=THEME["sb_bg"],pady=12); hdr.pack(fill='x')
        tk.Label(hdr,text=f"📅  Cambiar Fecha — {c.get('customer_name','')}",
                 font=(FONT,12,'bold'),bg=THEME["sb_bg"],fg="#fff").pack(anchor='w',padx=16)
        body=tk.Frame(dlg,bg=THEME["ct_bg"],padx=20,pady=16); body.pack(fill='both',expand=True)
        tk.Label(body,text=f"Fecha actual: {c.get('next_payment_date','—')}",font=(FONT,10),
                 bg=THEME["ct_bg"],fg=THEME["txt_secondary"]).pack(anchor='w',pady=(0,12))
        tk.Label(body,text="Nueva Fecha (YYYY-MM-DD)",font=(FONT,10,'bold'),
                 bg=THEME["ct_bg"],fg=THEME["txt_secondary"]).pack(anchor='w',pady=(0,4))
        date_outer=tk.Frame(body,bg=THEME["input_brd"])
        date_inner=tk.Frame(date_outer,bg=THEME["input_bg"])
        date_inner.pack(fill='x',padx=1,pady=1)
        date_e=tk.Entry(date_inner,font=(FONT,12),bg=THEME["input_bg"],
                        fg=THEME["txt_primary"],relief='flat',bd=0)
        date_e.pack(fill='x',padx=12,pady=9)
        date_outer.pack(fill='x'); date_e.insert(0,c.get('next_payment_date','')); date_e.focus()
        def update():
            try:
                datetime.strptime(date_e.get(),'%Y-%m-%d')
                self.db.update_next_payment_date(self.selected_credit_id,date_e.get())
                messagebox.showinfo("✅","Fecha actualizada",parent=dlg)
                self.load_credits(); dlg.destroy()
            except ValueError: messagebox.showerror("Error","Use el formato YYYY-MM-DD",parent=dlg)
            except Exception as e: messagebox.showerror("Error",str(e),parent=dlg)
        _btn(btn_bar,"Actualizar",update,THEME["acc_green"],"💾").pack(side='left',padx=(0,8))
        _btn(btn_bar,"Cancelar",dlg.destroy,THEME["btn_secondary"],"✕").pack(side='left')
