"""Módulo Reportes — Diseño moderno Venialgo POS"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from utils.formatters import format_currency
try:
    from utils.window_icon import set_icon as _set_icon
except ImportError:
    def _set_icon(w): pass


THEME={"ct_bg":"#F9FAFB","card_bg":"#FFFFFF","card_border":"#E5E7EB","sb_bg":"#111827",
    "txt_primary":"#111827","txt_secondary":"#6B7280","txt_white":"#FFFFFF",
    "acc_blue":"#2563EB","acc_green":"#059669","acc_amber":"#D97706","acc_rose":"#E11D48",
    "acc_purple":"#7C3AED","acc_cyan":"#0891B2","btn_secondary":"#6B7280",
    "input_bg":"#FFFFFF","input_brd":"#D1D5DB","input_foc":"#2563EB",
    "row_odd":"#F9FAFB","row_even":"#FFFFFF"}
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

class ReportsModule:
    def __init__(self,parent,db_manager,current_user=None):
        self.parent=parent; self.db=db_manager
        self.current_user=current_user or {}
        self._rol=(self.current_user.get('rol') or '').lower()
        self._is_admin=self._rol=='administrador'
        self.sales_data=[]; _setup_styles()
        self._build()
        self._quick_filter('today')

    def _stat_card(self,parent,title,value,accent,icon=""):
        outer=tk.Frame(parent,bg=THEME["card_border"])
        inner=tk.Frame(outer,bg=THEME["card_bg"],padx=16,pady=14)
        inner.pack(fill='both',expand=True,padx=1,pady=1)
        tk.Label(inner,text=f"{icon}  {title}" if icon else title,
                 font=(FONT,9),bg=THEME["card_bg"],fg=THEME["txt_secondary"]).pack(anchor='w')
        lbl=tk.Label(inner,text=value,font=(FONT,18,'bold'),bg=THEME["card_bg"],fg=accent)
        lbl.pack(anchor='w',pady=(4,0))
        tk.Frame(inner,bg=accent,height=3).pack(fill='x',pady=(10,0))
        inner.value_label=lbl; outer.value_label=lbl
        return outer

    def _build(self):
        bg=THEME["ct_bg"]
        # Header
        hdr=tk.Frame(self.parent,bg=bg); hdr.pack(fill='x',padx=28,pady=(20,0))
        tk.Label(hdr,text="📊  Reportes y Estadísticas",font=(FONT,16,'bold'),
                 bg=bg,fg=THEME["txt_primary"]).pack(side='left')
        tk.Frame(self.parent,bg=THEME["card_border"],height=1).pack(fill='x',padx=28,pady=(10,14))

        # Filtros rápidos
        flt_card_outer=tk.Frame(self.parent,bg=THEME["card_border"])
        flt_card_outer.pack(fill='x',padx=24,pady=(0,14))
        flt_card=tk.Frame(flt_card_outer,bg=THEME["card_bg"],padx=16,pady=12)
        flt_card.pack(fill='x',padx=1,pady=1)
        tk.Label(flt_card,text="Período:",font=(FONT,10,'bold'),
                 bg=THEME["card_bg"],fg=THEME["txt_secondary"]).pack(side='left',padx=(0,12))
        for val,lbl in [('today','Hoy'),('week','Esta semana'),('month','Este mes'),('year','Este año')]:
            b=tk.Label(flt_card,text=lbl,font=(FONT,9,'bold'),cursor='hand2',
                       padx=12,pady=6,bg=THEME["input_brd"],fg=THEME["txt_secondary"])
            b.pack(side='left',padx=2)
            b.bind('<Enter>',lambda e,w=b:w.config(bg=THEME["acc_blue"],fg="#fff"))
            b.bind('<Leave>',lambda e,w=b:w.config(bg=THEME["input_brd"],fg=THEME["txt_secondary"]))
            b.bind('<Button-1>',lambda e,v=val:self._quick_filter(v))

        # Rango personalizado
        tk.Frame(flt_card,bg=THEME["card_border"],width=1).pack(side='left',fill='y',padx=12,pady=2)
        tk.Label(flt_card,text="Desde:",font=(FONT,9,'bold'),bg=THEME["card_bg"],
                 fg=THEME["txt_secondary"]).pack(side='left',padx=(0,6))
        self.date_from=tk.Entry(flt_card,font=(FONT,10),width=11,
                                bg=THEME["input_bg"],fg=THEME["txt_primary"],
                                relief='solid',bd=1,insertbackground=THEME["acc_blue"])
        self.date_from.pack(side='left',padx=(0,8))
        tk.Label(flt_card,text="Hasta:",font=(FONT,9,'bold'),bg=THEME["card_bg"],
                 fg=THEME["txt_secondary"]).pack(side='left',padx=(0,6))
        self.date_to=tk.Entry(flt_card,font=(FONT,10),width=11,
                              bg=THEME["input_bg"],fg=THEME["txt_primary"],
                              relief='solid',bd=1,insertbackground=THEME["acc_blue"])
        self.date_to.pack(side='left',padx=(0,10))
        _btn(flt_card,"Buscar",self.load_report,THEME["acc_blue"],"🔍").pack(side='left')

        # ── Sección Reporte por Rol (solo Administrador) ──────────
        if self._is_admin:
            roles_card_outer=tk.Frame(self.parent,bg=THEME["card_border"])
            roles_card_outer.pack(fill='x',padx=24,pady=(0,14))
            roles_card=tk.Frame(roles_card_outer,bg=THEME["card_bg"],padx=16,pady=10)
            roles_card.pack(fill='x',padx=1,pady=1)
            # Fila superior: título + selector
            roles_hdr=tk.Frame(roles_card,bg=THEME["card_bg"]); roles_hdr.pack(fill='x',pady=(0,8))
            tk.Label(roles_hdr,text="👤  Filtrar por Usuario / Rol:",font=(FONT,10,'bold'),
                     bg=THEME["card_bg"],fg=THEME["txt_primary"]).pack(side='left')
            _btn(roles_hdr,"Ver Reporte por Rol",self._show_role_report,
                 THEME["acc_purple"],"📊").pack(side='right')
            # Fila de filtros
            roles_flt=tk.Frame(roles_card,bg=THEME["card_bg"]); roles_flt.pack(fill='x')
            # Filtro por rol
            tk.Label(roles_flt,text="Rol:",font=(FONT,9,'bold'),
                     bg=THEME["card_bg"],fg=THEME["txt_secondary"]).pack(side='left',padx=(0,6))
            self.rol_filter_var=tk.StringVar(value="Todos los roles")
            rol_cb=ttk.Combobox(roles_flt,textvariable=self.rol_filter_var,
                values=["Todos los roles","Administrador","Supervisor","Cajero"],
                state='readonly',font=(FONT,9),width=18)
            rol_cb.pack(side='left',padx=(0,16))
            # Filtro por usuario
            tk.Label(roles_flt,text="Usuario:",font=(FONT,9,'bold'),
                     bg=THEME["card_bg"],fg=THEME["txt_secondary"]).pack(side='left',padx=(0,6))
            self.user_filter_var=tk.StringVar(value="Todos los usuarios")
            users=[]
            try: users=self.db.get_all_users()
            except: pass
            user_names=["Todos los usuarios"]+[f"{u['nombre']} ({u['usuario']})" for u in users if u.get('activo',1)]
            self._users_list=users
            self.user_cb=ttk.Combobox(roles_flt,textvariable=self.user_filter_var,
                values=user_names,state='readonly',font=(FONT,9),width=24)
            self.user_cb.pack(side='left',padx=(0,16))
            # Al cambiar rol, filtrar usuarios
            def _filter_users_by_rol(*_):
                sel_rol=self.rol_filter_var.get()
                if sel_rol=="Todos los roles":
                    filtered=self._users_list
                else:
                    filtered=[u for u in self._users_list
                               if u.get('rol','').lower()==sel_rol.lower() and u.get('activo',1)]
                names=["Todos los usuarios"]+[f"{u['nombre']} ({u['usuario']})" for u in filtered]
                self.user_cb['values']=names
                self.user_filter_var.set("Todos los usuarios")
            rol_cb.bind('<<ComboboxSelected>>',_filter_users_by_rol)

        # Cards KPI
        kpi_row=tk.Frame(self.parent,bg=bg); kpi_row.pack(fill='x',padx=24,pady=(0,14))
        self.kpi_count  =self._stat_card(kpi_row,"Total Ventas","0",THEME["acc_blue"],"🛒")
        self.kpi_revenue=self._stat_card(kpi_row,"Ingresos Totales","Gs. 0",THEME["acc_green"],"💰")
        self.kpi_avg    =self._stat_card(kpi_row,"Ticket Promedio","Gs. 0",THEME["acc_amber"],"📈")
        self.kpi_items  =self._stat_card(kpi_row,"Productos Vendidos","0",THEME["acc_purple"],"📦")
        for i,w in enumerate([self.kpi_count,self.kpi_revenue,self.kpi_avg,self.kpi_items]):
            w.grid(row=0,column=i,sticky='nsew',padx=4); kpi_row.columnconfigure(i,weight=1)

        # Tabla ventas
        tbl_outer=tk.Frame(self.parent,bg=THEME["card_border"])
        tbl_outer.pack(fill='both',expand=True,padx=24,pady=(0,10))
        tbl=tk.Frame(tbl_outer,bg=THEME["card_bg"]); tbl.pack(fill='both',expand=True,padx=1,pady=1)

        tbl_hdr=tk.Frame(tbl,bg=THEME["card_bg"],padx=16,pady=10); tbl_hdr.pack(fill='x')
        tk.Label(tbl_hdr,text="Detalle de Ventas",font=(FONT,11,'bold'),
                 bg=THEME["card_bg"],fg=THEME["txt_primary"]).pack(side='left')
        self.lbl_count=tk.Label(tbl_hdr,text="",font=(FONT,9),
                                bg=THEME["card_bg"],fg=THEME["txt_secondary"]); self.lbl_count.pack(side='left',padx=8)
        _btn(tbl_hdr,"Exportar CSV",self.export_csv,THEME["acc_cyan"],"📥").pack(side='right')
        tk.Frame(tbl,bg=THEME["card_border"],height=1).pack(fill='x')

        cols=('ID','Fecha','Cliente','Total','Método','Usuario','Estado')
        self.tree=ttk.Treeview(tbl,columns=cols,show='headings',style='POS.Treeview')
        widths={'ID':50,'Fecha':145,'Cliente':170,'Total':110,'Método':110,'Usuario':120,'Estado':75}
        for col in cols:
            self.tree.heading(col,text=col)
            self.tree.column(col,width=widths[col],anchor='w' if col in('Fecha','Cliente') else 'center')
        sb=ttk.Scrollbar(tbl,orient='vertical',command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side='right',fill='y',padx=(0,4),pady=4); self.tree.pack(fill='both',expand=True,padx=4,pady=4)
        self.tree.bind('<Double-Button-1>',self._show_sale_detail)
        self.tree.tag_configure('odd',background=THEME["row_odd"])
        self.tree.tag_configure('even',background=THEME["row_even"])
        self.tree.tag_configure('credit',foreground=THEME["acc_purple"])

    def _quick_filter(self,period):
        today=datetime.now()
        if period=='today':
            d_from=d_to=today.strftime('%Y-%m-%d')
        elif period=='week':
            d_from=(today-timedelta(days=today.weekday())).strftime('%Y-%m-%d')
            d_to=today.strftime('%Y-%m-%d')
        elif period=='month':
            d_from=today.strftime('%Y-%m-01')
            d_to=today.strftime('%Y-%m-%d')
        else:
            d_from=today.strftime('%Y-01-01')
            d_to=today.strftime('%Y-%m-%d')
        self.date_from.delete(0,'end'); self.date_from.insert(0,d_from)
        self.date_to.delete(0,'end'); self.date_to.insert(0,d_to)
        self.load_report()

    def load_report(self):
        d_from=self.date_from.get().strip(); d_to=self.date_to.get().strip()
        if not d_from or not d_to: return
        try:
            datetime.strptime(d_from,'%Y-%m-%d'); datetime.strptime(d_to,'%Y-%m-%d')
        except ValueError: messagebox.showerror("Error","Use formato YYYY-MM-DD"); return

        for i in self.tree.get_children(): self.tree.delete(i)
        self.sales_data=self.db.get_sales_by_date(d_from,d_to)
        summary=self.db.get_sales_summary(d_from,d_to)

        self.kpi_count.value_label.config(text=str(summary.get('total_sales',0)))
        self.kpi_revenue.value_label.config(text=format_currency(summary.get('total_revenue',0)))
        self.kpi_avg.value_label.config(text=format_currency(summary.get('average_sale',0)))

        # Productos vendidos
        try:
            items=self.db.execute_scalar(
                """SELECT COALESCE(SUM(d.cantidad),0) FROM detalle_ventas d
                   JOIN ventas v ON d.venta_id=v.id
                   WHERE v.fecha BETWEEN ? AND ?""",(d_from,d_to+' 23:59:59')) or 0
            self.kpi_items.value_label.config(text=str(int(items)))
        except: pass

        for idx,s in enumerate(self.sales_data):
            tag_row='odd' if idx%2 else 'even'
            tags=(tag_row,'credit') if s.get('payment_method','')=='Crédito' else (tag_row,)
            cajero=s.get('cajero_nombre') or s.get('cashier_name','') or '—'
            self.tree.insert('','end',tags=tags,values=(
                s.get('id',''),
                s.get('sale_date','')[:16] if s.get('sale_date') else '',
                s.get('customer_name','') or 'Consumidor Final',
                format_currency(s.get('total',0)),
                s.get('payment_method',''),
                cajero,
                'Crédito' if s.get('payment_method')=='Crédito' else 'Contado'))
        self.lbl_count.config(text=f"({len(self.sales_data)} registros)")

    def _show_sale_detail(self,_=None):
        sel=self.tree.selection()
        if not sel: return
        sale_id=self.tree.item(sel[0])['values'][0]
        details=self.db.get_sale_details(sale_id)
        if not details: return
        sale=next((s for s in self.sales_data if s.get('id')==sale_id),{})
        dlg=tk.Toplevel(self.parent)
        _set_icon(dlg); dlg.title(f"Venta #{sale_id}")
        dlg.configure(bg=THEME["ct_bg"]); dlg.transient(self.parent); _center(dlg,580,460)
        hdr=tk.Frame(dlg,bg=THEME["sb_bg"],pady=12); hdr.pack(fill='x')
        tk.Label(hdr,text=f"🧾  Venta #{sale_id} — {sale.get('customer_name','') or 'Consumidor Final'}",
                 font=(FONT,12,'bold'),bg=THEME["sb_bg"],fg="#fff").pack(anchor='w',padx=16)
        tk.Label(hdr,text=f"Total: {format_currency(sale.get('total',0))}  ·  {sale.get('sale_date','')[:16]}",
                 font=(FONT,9),bg=THEME["sb_bg"],fg="#94A3B8").pack(anchor='w',padx=16)
        tbl=tk.Frame(dlg,bg=THEME["card_bg"]); tbl.pack(fill='both',expand=True,padx=16,pady=16)
        cols2=('Producto','Cantidad','Precio Unit.','Subtotal')
        tree2=ttk.Treeview(tbl,columns=cols2,show='headings',height=10,style='POS.Treeview')
        for col,w in zip(cols2,[240,80,120,120]):
            tree2.heading(col,text=col); tree2.column(col,width=w,anchor='w' if col=='Producto' else 'center')
        sb2=ttk.Scrollbar(tbl,orient='vertical',command=tree2.yview)
        tree2.configure(yscrollcommand=sb2.set)
        sb2.pack(side='right',fill='y'); tree2.pack(fill='both',expand=True)
        for i,d in enumerate(details):
            tree2.insert('','end',tags=('odd' if i%2 else 'even',),values=(
                d.get('product_name',''),d.get('quantity',0),
                format_currency(d.get('unit_price',0)),
                format_currency(d.get('quantity',0)*d.get('unit_price',0))))
        tree2.tag_configure('odd',background=THEME["row_odd"]); tree2.tag_configure('even',background=THEME["row_even"])
        _btn(dlg,"Cerrar",dlg.destroy,THEME["btn_secondary"]).pack(pady=10)

    def _show_role_report(self):
        """Ventana de reporte detallado por rol/usuario con KPIs y tabla."""
        d_from=self.date_from.get().strip(); d_to=self.date_to.get().strip()
        if not d_from or not d_to:
            messagebox.showinfo("Info","Seleccione un rango de fechas primero"); return

        # Obtener todas las ventas del período
        all_sales=self.db.get_sales_by_date(d_from,d_to)

        # Aplicar filtros
        sel_rol=self.rol_filter_var.get()
        sel_user=self.user_filter_var.get()

        filtered=[]
        for s in all_sales:
            cajero=s.get('cajero_nombre') or s.get('cashier_name','')
            # Filtro por nombre de usuario
            if sel_user!="Todos los usuarios":
                u_nombre=sel_user.split(' (')[0]
                if cajero!=u_nombre: continue
            elif sel_rol!="Todos los roles":
                # Filtrar por rol: buscar en lista de usuarios
                matched_names=[u['nombre'] for u in self._users_list
                               if u.get('rol','').lower()==sel_rol.lower()]
                if cajero not in matched_names: continue
            filtered.append(s)

        # Agrupar por usuario
        from collections import defaultdict
        by_user=defaultdict(list)
        for s in filtered:
            cajero=s.get('cajero_nombre') or s.get('cashier_name','') or 'Sin asignar'
            by_user[cajero].append(s)

        # Ventana
        dlg=tk.Toplevel(self.parent)
        _set_icon(dlg); dlg.title("Reporte por Rol/Usuario")
        dlg.configure(bg=THEME["ct_bg"]); dlg.resizable(True,True)
        dlg.transient(self.parent); _center(dlg,860,620); dlg.minsize(700,500)

        # Botones PRIMERO
        btn_bar=tk.Frame(dlg,bg=THEME["card_bg"],padx=16,pady=10)
        btn_bar.pack(fill='x',side='bottom')
        tk.Frame(dlg,bg=THEME["card_border"],height=1).pack(fill='x',side='bottom')

        # Header
        hdr=tk.Frame(dlg,bg=THEME["sb_bg"],pady=12); hdr.pack(fill='x')
        filtro_txt=(f"Rol: {sel_rol}" if sel_rol!="Todos los roles" else "") +                    ("  |  " if sel_rol!="Todos los roles" and sel_user!="Todos los usuarios" else "") +                    (f"Usuario: {sel_user.split(' (')[0]}" if sel_user!="Todos los usuarios" else "")
        filtro_txt=filtro_txt or "Todos los usuarios"
        tk.Label(hdr,text=f"📊  Reporte por Rol/Usuario",
                 font=(FONT,13,'bold'),bg=THEME["sb_bg"],fg="#fff").pack(anchor='w',padx=16)
        tk.Label(hdr,text=f"Período: {d_from}  →  {d_to}   |   Filtro: {filtro_txt}",
                 font=(FONT,9),bg=THEME["sb_bg"],fg="#8AABD4").pack(anchor='w',padx=18)

        # Canvas scroll
        canvas=tk.Canvas(dlg,bg=THEME["ct_bg"],highlightthickness=0)
        sbar=tk.Scrollbar(dlg,orient='vertical',command=canvas.yview)
        canvas.configure(yscrollcommand=sbar.set)
        sbar.pack(side='right',fill='y'); canvas.pack(fill='both',expand=True)
        body=tk.Frame(canvas,bg=THEME["ct_bg"],padx=20,pady=16)
        canvas.create_window((0,0),window=body,anchor='nw',tags='body')
        body.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',lambda e:canvas.itemconfig('body',width=e.width))
        def _mw(e):
            try: canvas.yview_scroll(-1*(e.delta//120),'units')
            except: canvas.unbind_all('<MouseWheel>')
        canvas.bind('<Enter>',lambda e:canvas.bind_all('<MouseWheel>',_mw))
        canvas.bind('<Leave>',lambda e:canvas.unbind_all('<MouseWheel>'))

        # ── Resumen global ──
        total_global=sum(s.get('total',0) for s in filtered)
        sec0=tk.Frame(body,bg=THEME["card_border"]); sec0.pack(fill='x',pady=(0,14))
        inn0=tk.Frame(sec0,bg=THEME["card_bg"],padx=16,pady=12); inn0.pack(fill='x',padx=1,pady=1)
        tk.Label(inn0,text="Resumen Global del Período",font=(FONT,10,'bold'),
                 bg=THEME["card_bg"],fg=THEME["acc_blue"]).pack(anchor='w',pady=(0,8))
        kpi_row=tk.Frame(inn0,bg=THEME["card_bg"]); kpi_row.pack(fill='x')
        for i,(lbl,val,col) in enumerate([
            ("Total Ventas",str(len(filtered)),THEME["acc_blue"]),
            ("Ingresos",format_currency(total_global),THEME["acc_green"]),
            ("Usuarios",str(len(by_user)),THEME["acc_purple"]),
            ("Promedio/Venta",format_currency(total_global/len(filtered)) if filtered else "—",THEME["acc_amber"]),
        ]):
            card=tk.Frame(kpi_row,bg=THEME["card_border"]); card.grid(row=0,column=i,sticky='nsew',padx=4)
            inn=tk.Frame(card,bg=THEME["card_bg"],padx=12,pady=10); inn.pack(fill='both',padx=1,pady=1)
            tk.Label(inn,text=lbl,font=(FONT,8),bg=THEME["card_bg"],fg=THEME["txt_secondary"]).pack(anchor='w')
            tk.Label(inn,text=val,font=(FONT,13,'bold'),bg=THEME["card_bg"],fg=col).pack(anchor='w')
            kpi_row.columnconfigure(i,weight=1)

        # ── Tarjeta por usuario ──
        for cajero_name,sales in sorted(by_user.items()):
            # Buscar rol del usuario
            u_rol='—'
            for u in self._users_list:
                if u.get('nombre')==cajero_name:
                    u_rol=u.get('rol','—').title(); break
            total_u=sum(s.get('total',0) for s in sales)
            contado=[s for s in sales if s.get('payment_method','')!='Crédito']
            credito=[s for s in sales if s.get('payment_method','')=='Crédito']

            sec=tk.Frame(body,bg=THEME["card_border"]); sec.pack(fill='x',pady=(0,12))
            inn=tk.Frame(sec,bg=THEME["card_bg"],padx=16,pady=12); inn.pack(fill='x',padx=1,pady=1)

            # Cabecera usuario
            uh=tk.Frame(inn,bg=THEME["card_bg"]); uh.pack(fill='x',pady=(0,10))
            ROL_COLORS={'administrador':THEME["acc_blue"],'supervisor':THEME["acc_amber"],
                        'cajero':THEME["acc_green"]}
            rol_col=ROL_COLORS.get(u_rol.lower(),THEME["acc_purple"])
            tk.Label(uh,text=f"👤  {cajero_name}",font=(FONT,11,'bold'),
                     bg=THEME["card_bg"],fg=THEME["txt_primary"]).pack(side='left')
            tk.Label(uh,text=f"  {u_rol}",font=(FONT,9,'bold'),
                     bg=rol_col,fg="#fff",padx=8,pady=2).pack(side='left',padx=8)

            # KPIs del usuario
            kpi_u=tk.Frame(inn,bg=THEME["card_bg"]); kpi_u.pack(fill='x',pady=(0,10))
            for i,(lbl,val,col) in enumerate([
                ("Ventas totales",str(len(sales)),THEME["acc_blue"]),
                ("Ingresos",format_currency(total_u),THEME["acc_green"]),
                ("Ventas contado",str(len(contado)),THEME["acc_amber"]),
                ("Ventas crédito",str(len(credito)),THEME["acc_purple"]),
                ("Ticket promedio",format_currency(total_u/len(sales)) if sales else "—",THEME["txt_secondary"]),
            ]):
                c2=tk.Frame(kpi_u,bg=THEME["card_border"]); c2.grid(row=0,column=i,sticky='nsew',padx=3)
                i2=tk.Frame(c2,bg=THEME["card_bg"],padx=10,pady=8); i2.pack(fill='both',padx=1,pady=1)
                tk.Label(i2,text=lbl,font=(FONT,7),bg=THEME["card_bg"],fg=THEME["txt_secondary"]).pack(anchor='w')
                tk.Label(i2,text=val,font=(FONT,11,'bold'),bg=THEME["card_bg"],fg=col).pack(anchor='w')
                kpi_u.columnconfigure(i,weight=1)

            # Tabla de ventas del usuario
            tk.Label(inn,text="Detalle de ventas:",font=(FONT,9,'bold'),
                     bg=THEME["card_bg"],fg=THEME["txt_secondary"]).pack(anchor='w',pady=(0,4))
            u_cols=('ID','Fecha','Cliente','Total','Método')
            u_tree=ttk.Treeview(inn,columns=u_cols,show='headings',
                                style='POS.Treeview',height=min(len(sales),5))
            for col,w in zip(u_cols,[50,145,180,110,110]):
                u_tree.heading(col,text=col)
                u_tree.column(col,width=w,anchor='w' if col in('Fecha','Cliente') else 'center')
            for si,s in enumerate(sorted(sales,key=lambda x:x.get('sale_date',''),reverse=True)):
                tag='odd' if si%2 else 'even'
                u_tree.insert('','end',tags=(tag,),values=(
                    s.get('id',''),
                    (s.get('sale_date','') or '')[:16],
                    s.get('customer_name','') or 'Consumidor Final',
                    format_currency(s.get('total',0)),
                    s.get('payment_method',''),
                ))
            u_tree.tag_configure('odd',background=THEME["row_odd"])
            u_tree.tag_configure('even',background=THEME["row_even"])
            u_tree.pack(fill='x')

        if not by_user:
            tk.Label(body,text="No hay ventas registradas para este filtro en el período seleccionado.",
                     font=(FONT,10),bg=THEME["ct_bg"],fg=THEME["txt_secondary"]).pack(pady=40)

        # Botón exportar + cerrar
        def _exp_role():
            self._export_role_report(by_user,d_from,d_to,filtro_txt)
        b1=_btn(btn_bar,"Exportar Excel",_exp_role,THEME["acc_green"],"📊"); b1.pack(side='left',padx=(0,8))
        b2=_btn(btn_bar,"Cerrar",dlg.destroy,THEME["btn_secondary"],"✕"); b2.pack(side='left')

    def _export_role_report(self,by_user,d_from,d_to,filtro_txt):
        """Exporta el reporte por roles a Excel."""
        try:
            import openpyxl
            from openpyxl.styles import Font,PatternFill,Alignment,Border,Side
            from openpyxl.utils import get_column_letter
            from datetime import datetime as _dt
            try: from utils.company_header import get_company as _get_company
            except: _get_company=lambda:{}
            co=_get_company()
            empresa=co.get("razon_social","Venialgo POS")
            thin=Side(style='thin',color='D1D5DB')
            brd=Border(left=thin,right=thin,top=thin,bottom=thin)
            def hdr_s(cell,bg="111827",fg="FFFFFF"):
                cell.font=Font(name='Arial',bold=True,color=fg,size=10)
                cell.fill=PatternFill('solid',start_color=bg)
                cell.alignment=Alignment(horizontal='center',vertical='center')
                cell.border=brd
            wb=openpyxl.Workbook()
            # ── Hoja resumen por usuario ──
            ws=wb.active; ws.title="Resumen por Usuario"
            ws.merge_cells("A1:G1"); ws["A1"]=empresa
            ws["A1"].font=Font(name='Arial',bold=True,size=14,color="2563EB")
            ws["A1"].alignment=Alignment(horizontal='center')
            ws.row_dimensions[1].height=24
            ws.merge_cells("A2:G2")
            ws["A2"]=f"REPORTE POR ROL/USUARIO  |  Período: {d_from} → {d_to}  |  Filtro: {filtro_txt}"
            ws["A2"].font=Font(name='Arial',size=9,color="6B7280",italic=True)
            ws["A2"].alignment=Alignment(horizontal='center')
            ws.row_dimensions[2].height=14
            ws.merge_cells("A3:G3")
            ws["A3"]=f"Generado: {_dt.now().strftime('%d/%m/%Y %H:%M')}   |   Usuarios: {len(by_user)}"
            ws["A3"].font=Font(name='Arial',size=9,color="6B7280",italic=True)
            ws["A3"].alignment=Alignment(horizontal='center')
            ws.row_dimensions[3].height=14
            for ci,h in enumerate(["Usuario","Rol","Total Ventas","Contado","Crédito","Ingresos","Ticket Prom."],1):
                hdr_s(ws.cell(row=4,column=ci,value=h))
            for ci,w in enumerate([22,14,13,12,12,16,14],1):
                ws.column_dimensions[get_column_letter(ci)].width=w
            ri=5
            for cajero_name,sales in sorted(by_user.items()):
                u_rol='—'
                for u in self._users_list:
                    if u.get('nombre')==cajero_name: u_rol=u.get('rol','—').title(); break
                total_u=sum(s.get('total',0) for s in sales)
                contado=len([s for s in sales if s.get('payment_method','')!='Crédito'])
                credito=len([s for s in sales if s.get('payment_method','')=='Crédito'])
                vals=[cajero_name,u_rol,len(sales),contado,credito,total_u,
                      total_u/len(sales) if sales else 0]
                bg="F0FDF4" if u_rol.lower()=='cajero' else ("EFF6FF" if u_rol.lower()=='administrador' else "FFFBEB")
                for ci,v in enumerate(vals,1):
                    cell=ws.cell(row=ri,column=ci,value=v)
                    cell.font=Font(name='Arial',size=9)
                    cell.fill=PatternFill('solid',start_color=bg)
                    cell.alignment=Alignment(horizontal='center' if ci>1 else 'left',vertical='center')
                    cell.border=brd
                ri+=1
                # Sub-tabla de ventas
                ws2=wb.create_sheet(cajero_name[:28])
                ws2.merge_cells("A1:F1"); ws2["A1"]=f"{empresa} — Ventas de: {cajero_name}"
                ws2["A1"].font=Font(name='Arial',bold=True,size=12,color="2563EB")
                ws2["A1"].alignment=Alignment(horizontal='center')
                for ci2,h2 in enumerate(["ID","Fecha","Cliente","Total","Método","Estado"],1):
                    hdr_s(ws2.cell(row=2,column=ci2,value=h2))
                for ci2,w2 in enumerate([8,18,22,14,14,12],1):
                    ws2.column_dimensions[get_column_letter(ci2)].width=w2
                for si,s in enumerate(sorted(sales,key=lambda x:x.get('sale_date',''),reverse=True),3):
                    bg2="F9FAFB" if si%2==1 else "FFFFFF"
                    for ci2,v2 in enumerate([
                        s.get('id',''),
                        (s.get('sale_date','') or '')[:16],
                        s.get('customer_name','') or 'Consumidor Final',
                        s.get('total',0),
                        s.get('payment_method',''),
                        'Crédito' if s.get('payment_method','')=='Crédito' else 'Contado'
                    ],1):
                        cell=ws2.cell(row=si,column=ci2,value=v2)
                        cell.font=Font(name='Arial',size=9)
                        cell.fill=PatternFill('solid',start_color=bg2)
                        cell.alignment=Alignment(horizontal='center' if ci2 not in(2,3) else 'left',vertical='center')
                        cell.border=brd
            import os,datetime
            docs=os.path.join(os.path.expanduser("~"),"Documents")
            os.makedirs(docs,exist_ok=True)
            ts=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path=os.path.join(docs,f"reporte_roles_{ts}.xlsx")
            wb.save(path)
            messagebox.showinfo("✅ Exportado",f"Archivo guardado en:\n{path}")
            os.startfile(os.path.dirname(path))
        except ImportError:
            messagebox.showerror("Error","Se requiere openpyxl: pip install openpyxl")
        except Exception as ex:
            messagebox.showerror("Error al exportar",str(ex))

    def export_csv(self):
        if not self.sales_data: messagebox.showinfo("Info","Sin datos para exportar"); return
        from tkinter import filedialog
        import csv
        path=filedialog.asksaveasfilename(defaultextension='.csv',
            filetypes=[('CSV','*.csv')],title="Guardar reporte")
        if not path: return
        try:
            with open(path,'w',newline='',encoding='utf-8-sig') as f:
                w=csv.writer(f)
                w.writerow(['ID','Fecha','Cliente','Total','Método'])
                for s in self.sales_data:
                    w.writerow([s.get('id',''),s.get('sale_date',''),
                        s.get('customer_name','') or 'Consumidor Final',
                        s.get('total',0),s.get('payment_method','')])
            messagebox.showinfo("✅ Exportado",f"Archivo guardado:\n{path}")
        except Exception as e: messagebox.showerror("Error",str(e))
