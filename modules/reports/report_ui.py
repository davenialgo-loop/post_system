"""Módulo Reportes — Diseño moderno Venialgo POS"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from utils.formatters import format_currency

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
    def __init__(self,parent,db_manager):
        self.parent=parent; self.db=db_manager
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

        cols=('ID','Fecha','Cliente','Total','Método','Estado')
        self.tree=ttk.Treeview(tbl,columns=cols,show='headings',style='POS.Treeview')
        widths={'ID':55,'Fecha':155,'Cliente':200,'Total':120,'Método':120,'Estado':80}
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
            self.tree.insert('','end',tags=tags,values=(
                s.get('id',''),
                s.get('sale_date','')[:16] if s.get('sale_date') else '',
                s.get('customer_name','') or 'Consumidor Final',
                format_currency(s.get('total',0)),
                s.get('payment_method',''),
                'Crédito' if s.get('payment_method')=='Crédito' else 'Contado'))
        self.lbl_count.config(text=f"({len(self.sales_data)} registros)")

    def _show_sale_detail(self,_=None):
        sel=self.tree.selection()
        if not sel: return
        sale_id=self.tree.item(sel[0])['values'][0]
        details=self.db.get_sale_details(sale_id)
        if not details: return
        sale=next((s for s in self.sales_data if s.get('id')==sale_id),{})
        dlg=tk.Toplevel(self.parent); dlg.title(f"Venta #{sale_id}")
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
