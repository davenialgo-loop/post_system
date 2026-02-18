"""
Script de prueba rápida para verificar que la interfaz funciona
Ejecuta este archivo para probar los componentes básicos
"""

import tkinter as tk
from tkinter import ttk

def test_headers():
    """Prueba los headers de las tablas"""
    root = tk.Tk()
    root.title("Test - Headers de Tablas")
    root.geometry("600x400")
    
    # Configurar estilo
    style = ttk.Style()
    try:
        style.theme_use('clam')
    except:
        pass
    
    # Configurar headers
    style.configure("Treeview.Heading",
                   background="#1e293b",
                   foreground="white",
                   relief="flat",
                   borderwidth=1,
                   font=('Segoe UI', 11, 'bold'))
    
    style.map('Treeview.Heading',
             background=[('active', '#2563eb')],
             foreground=[('active', 'white')])
    
    # Crear tabla
    tk.Label(root, text="Test de Headers de Tabla", font=('Segoe UI', 16, 'bold')).pack(pady=20)
    
    frame = tk.Frame(root)
    frame.pack(fill='both', expand=True, padx=20, pady=20)
    
    columns = ('ID', 'Nombre', 'Precio', 'Stock')
    tree = ttk.Treeview(frame, columns=columns, show='headings', height=8)
    
    tree.heading('ID', text='ID')
    tree.heading('Nombre', text='Nombre')
    tree.heading('Precio', text='Precio')
    tree.heading('Stock', text='Stock')
    
    tree.column('ID', width=50, anchor='center')
    tree.column('Nombre', width=200, anchor='w')
    tree.column('Precio', width=100, anchor='e')
    tree.column('Stock', width=80, anchor='center')
    
    # Datos de ejemplo
    tree.insert('', 'end', values=(1, 'Laptop HP', '₲850.000', 15))
    tree.insert('', 'end', values=(2, 'Mouse Logitech', '₲25.000', 50))
    tree.insert('', 'end', values=(3, 'Teclado Mecánico', '₲75.000', 30))
    
    tree.pack(fill='both', expand=True)
    
    tk.Label(
        root,
        text="¿Ves los headers con fondo oscuro y texto blanco?",
        font=('Segoe UI', 10)
    ).pack(pady=10)
    
    root.mainloop()

def test_dialog():
    """Prueba el diálogo de venta"""
    root = tk.Tk()
    root.title("Test - Diálogo de Venta")
    root.geometry("300x200")
    
    def open_dialog():
        dialog = tk.Toplevel(root)
        dialog.title("Test - Opciones de Pago")
        dialog.geometry("500x600")
        dialog.configure(bg='white')
        
        # Título
        tk.Label(
            dialog,
            text="Resumen de Venta",
            font=('Segoe UI', 16, 'bold'),
            bg='white'
        ).pack(pady=20)
        
        tk.Label(
            dialog,
            text="Total a Pagar: ₲1.000.000",
            font=('Segoe UI', 14, 'bold'),
            bg='white',
            fg='#10b981'
        ).pack(pady=10)
        
        # Separador
        tk.Frame(dialog, bg='#e2e8f0', height=2).pack(fill='x', padx=20, pady=10)
        
        # Tipo de venta
        tk.Label(
            dialog,
            text="Tipo de Venta*",
            font=('Segoe UI', 11, 'bold'),
            bg='white'
        ).pack(anchor='w', padx=20, pady=(10, 5))
        
        sale_type = tk.StringVar(value="cash")
        
        radio_frame = tk.Frame(dialog, bg='white')
        radio_frame.pack(fill='x', padx=20)
        
        tk.Radiobutton(
            radio_frame,
            text="💵 Venta al Contado",
            variable=sale_type,
            value="cash",
            font=('Segoe UI', 11),
            bg='white',
            command=lambda: update_options()
        ).pack(anchor='w')
        
        tk.Radiobutton(
            radio_frame,
            text="💳 Venta a Crédito",
            variable=sale_type,
            value="credit",
            font=('Segoe UI', 11),
            bg='white',
            command=lambda: update_options()
        ).pack(anchor='w')
        
        # Separador
        tk.Frame(dialog, bg='#e2e8f0', height=2).pack(fill='x', padx=20, pady=10)
        
        # Contenedor de opciones
        options = tk.Frame(dialog, bg='white')
        options.pack(fill='both', expand=True, padx=20, pady=10)
        
        def update_options():
            for widget in options.winfo_children():
                widget.destroy()
            
            if sale_type.get() == "cash":
                tk.Label(options, text="Método de Pago*", bg='white', font=('Segoe UI', 11)).pack(anchor='w')
                ttk.Combobox(options, values=["Efectivo", "Tarjeta"], state='readonly').pack(fill='x', pady=5)
                
                tk.Label(options, text="Monto Pagado*", bg='white', font=('Segoe UI', 11)).pack(anchor='w', pady=(10, 0))
                tk.Entry(options, font=('Segoe UI', 11)).pack(fill='x', pady=5)
                
                tk.Label(options, text="Cambio: ₲0", bg='white', font=('Segoe UI', 14, 'bold'), fg='#10b981').pack(anchor='w', pady=10)
            else:
                tk.Label(options, text="Cliente*", bg='white', font=('Segoe UI', 11)).pack(anchor='w')
                ttk.Combobox(options, values=["1 - Juan Pérez", "2 - María González"], state='readonly').pack(fill='x', pady=5)
                
                tk.Label(options, text="Cuota Inicial*", bg='white', font=('Segoe UI', 11)).pack(anchor='w', pady=(10, 0))
                tk.Entry(options, font=('Segoe UI', 11)).pack(fill='x', pady=5)
                
                tk.Label(options, text="Frecuencia*", bg='white', font=('Segoe UI', 11)).pack(anchor='w', pady=(10, 0))
                freq_frame = tk.Frame(options, bg='white')
                freq_frame.pack(fill='x')
                
                freq = tk.StringVar(value="weekly")
                tk.Radiobutton(freq_frame, text="Semanal", variable=freq, value="weekly", bg='white').pack(side='left')
                tk.Radiobutton(freq_frame, text="Quincenal", variable=freq, value="biweekly", bg='white').pack(side='left')
                tk.Radiobutton(freq_frame, text="Mensual", variable=freq, value="monthly", bg='white').pack(side='left')
                
                tk.Label(options, text="Número de Cuotas*", bg='white', font=('Segoe UI', 11)).pack(anchor='w', pady=(10, 0))
                tk.Entry(options, font=('Segoe UI', 11)).pack(fill='x', pady=5)
        
        # Botones
        btn_frame = tk.Frame(dialog, bg='white')
        btn_frame.pack(fill='x', side='bottom', padx=20, pady=20)
        
        tk.Button(btn_frame, text="💾 CONFIRMAR", bg='#10b981', fg='white', font=('Segoe UI', 11, 'bold'), 
                 relief='flat', padx=20, pady=8).pack(side='left', padx=5)
        tk.Button(btn_frame, text="❌ Cancelar", bg='#64748b', fg='white', font=('Segoe UI', 11), 
                 relief='flat', padx=20, pady=8, command=dialog.destroy).pack(side='left', padx=5)
        
        update_options()
    
    tk.Label(
        root,
        text="Test de Diálogo de Venta",
        font=('Segoe UI', 14, 'bold')
    ).pack(pady=30)
    
    tk.Button(
        root,
        text="Abrir Diálogo de Prueba",
        font=('Segoe UI', 12),
        bg='#2563eb',
        fg='white',
        relief='flat',
        padx=20,
        pady=10,
        command=open_dialog
    ).pack(pady=20)
    
    root.mainloop()

if __name__ == "__main__":
    print("=== PRUEBAS DE INTERFAZ ===")
    print("1. Test de Headers")
    print("2. Test de Diálogo")
    print()
    
    choice = input("Selecciona (1 o 2): ")
    
    if choice == "1":
        test_headers()
    elif choice == "2":
        test_dialog()
    else:
        print("Opción inválida")