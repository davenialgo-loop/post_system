"""
Test simple del diálogo de crédito
Ejecuta esto para ver si el problema es del diálogo o de la integración
"""

import tkinter as tk
from tkinter import ttk

def test_simple_dialog():
    root = tk.Tk()
    root.title("Test")
    root.geometry("400x300")
    
    def open_credit_dialog():
        dialog = tk.Toplevel(root)
        dialog.title("Test - Diálogo de Crédito")
        dialog.geometry("520x700")
        dialog.configure(bg='white')
        dialog.transient(root)
        dialog.grab_set()
        
        # Forzar actualización
        dialog.update()
        
        # Contenedor principal
        container = tk.Frame(dialog, bg='white')
        container.pack(fill='both', expand=True)
        
        # Título
        tk.Label(
            container,
            text="Resumen de Venta",
            font=('Segoe UI', 16, 'bold'),
            bg='white'
        ).pack(anchor='w', padx=20, pady=(20, 10))
        
        tk.Label(
            container,
            text="Total a Pagar: ₲1.234.567",
            font=('Segoe UI', 14, 'bold'),
            bg='white',
            fg='#10b981'
        ).pack(anchor='w', padx=20, pady=(0, 10))
        
        # Separador
        tk.Frame(dialog, bg='#e2e8f0', height=2).pack(fill='x', padx=20, pady=10)
        
        # Tipo de venta
        tk.Label(
            container,
            text="Tipo de Venta*",
            font=('Segoe UI', 11, 'bold'),
            bg='white'
        ).pack(anchor='w', padx=20, pady=(10, 5))
        
        sale_type = tk.StringVar(value="cash")
        
        radio_frame = tk.Frame(container, bg='white')
        radio_frame.pack(fill='x', padx=20)
        
        tk.Radiobutton(
            radio_frame,
            text="💵 Venta al Contado",
            variable=sale_type,
            value="cash",
            font=('Segoe UI', 11),
            bg='white',
            selectcolor='white',
            command=lambda: toggle_options()
        ).pack(anchor='w', pady=2)
        
        tk.Radiobutton(
            radio_frame,
            text="💳 Venta a Crédito",
            variable=sale_type,
            value="credit",
            font=('Segoe UI', 11),
            bg='white',
            selectcolor='white',
            command=lambda: toggle_options()
        ).pack(anchor='w', pady=2)
        
        # Separador
        tk.Frame(dialog, bg='#e2e8f0', height=2).pack(fill='x', padx=20, pady=10)
        
        # Contenedor de opciones
        options_container = tk.Frame(container, bg='white')
        options_container.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Opciones de contado (pre-creadas)
        cash_frame = tk.Frame(options_container, bg='white')
        
        tk.Label(cash_frame, text="Método de Pago*", bg='white', font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))
        ttk.Combobox(cash_frame, values=["Efectivo", "Tarjeta"], state='readonly', width=40).pack(fill='x', pady=(0, 10))
        
        tk.Label(cash_frame, text="Monto Pagado*", bg='white', font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))
        entry_paid = tk.Entry(cash_frame, font=('Segoe UI', 11))
        entry_paid.pack(fill='x', pady=(0, 10))
        entry_paid.insert(0, "1234567")
        
        tk.Label(cash_frame, text="Cambio:", bg='white', font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))
        tk.Label(cash_frame, text="₲0", bg='white', font=('Segoe UI', 14, 'bold'), fg='#10b981').pack(anchor='w')
        
        # Opciones de crédito (pre-creadas)
        credit_frame = tk.Frame(options_container, bg='white')
        
        tk.Label(credit_frame, text="Cliente* (Requerido)", bg='white', font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))
        ttk.Combobox(credit_frame, values=["1 - Juan Pérez", "2 - María"], width=40).pack(fill='x', pady=(0, 10))
        
        tk.Label(credit_frame, text="Cuota Inicial*", bg='white', font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))
        entry_down = tk.Entry(credit_frame, font=('Segoe UI', 11))
        entry_down.pack(fill='x', pady=(0, 10))
        entry_down.insert(0, "123456")
        
        tk.Label(credit_frame, text="Frecuencia de Pago*", bg='white', font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))
        freq_frame = tk.Frame(credit_frame, bg='white')
        freq_frame.pack(fill='x', pady=(0, 10))
        
        freq_var = tk.StringVar(value="weekly")
        tk.Radiobutton(freq_frame, text="Semanal", variable=freq_var, value="weekly", bg='white', selectcolor='white').pack(side='left', padx=(0, 10))
        tk.Radiobutton(freq_frame, text="Quincenal", variable=freq_var, value="biweekly", bg='white', selectcolor='white').pack(side='left', padx=(0, 10))
        tk.Radiobutton(freq_frame, text="Mensual", variable=freq_var, value="monthly", bg='white', selectcolor='white').pack(side='left')
        
        tk.Label(credit_frame, text="Número de Cuotas*", bg='white', font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))
        entry_install = tk.Entry(credit_frame, font=('Segoe UI', 11))
        entry_install.pack(fill='x', pady=(0, 10))
        entry_install.insert(0, "4")
        
        def toggle_options():
            print(f"Toggle called - Current value: {sale_type.get()}")  # DEBUG
            if sale_type.get() == "credit":
                print("Showing credit options")  # DEBUG
                cash_frame.pack_forget()
                credit_frame.pack(fill='both', expand=True)
            else:
                print("Showing cash options")  # DEBUG
                credit_frame.pack_forget()
                cash_frame.pack(fill='both', expand=True)
            dialog.update_idletasks()  # Forzar actualización
        
        # Botones
        btn_frame = tk.Frame(dialog, bg='white')
        btn_frame.pack(fill='x', side='bottom', padx=20, pady=20)
        
        tk.Button(btn_frame, text="💾 CONFIRMAR", bg='#10b981', fg='white', 
                 font=('Segoe UI', 11, 'bold'), relief='flat', padx=20, pady=8).pack(side='left', padx=5)
        tk.Button(btn_frame, text="❌ Cancelar", bg='#64748b', fg='white', 
                 font=('Segoe UI', 11), relief='flat', padx=20, pady=8, 
                 command=dialog.destroy).pack(side='left', padx=5)
        
        # Mostrar opciones iniciales (IMPORTANTE)
        print("Showing initial options")  # DEBUG
        cash_frame.pack(fill='both', expand=True)
        dialog.update()
    
    tk.Label(
        root,
        text="Test de Diálogo de Crédito",
        font=('Segoe UI', 14, 'bold')
    ).pack(pady=30)
    
    tk.Button(
        root,
        text="Abrir Diálogo",
        font=('Segoe UI', 12),
        bg='#2563eb',
        fg='white',
        relief='flat',
        padx=20,
        pady=10,
        command=open_credit_dialog
    ).pack(pady=20)
    
    root.mainloop()

if __name__ == "__main__":
    test_simple_dialog()