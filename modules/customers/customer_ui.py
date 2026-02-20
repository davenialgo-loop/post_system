"""
Módulo de Gestión de Clientes
Interfaz de usuario para CRUD de clientes
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config.settings import COLORS, FONTS, SPACING, BUTTON_STYLES
from utils.validators import validate_required_field, validate_phone, validate_email

class CustomerModule:
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db = db_manager
        self.selected_customer_id = None
        
        self.create_ui()
        self.load_customers()
    
    def create_ui(self):
        """Crea la interfaz del módulo de clientes"""
        
        header_frame = tk.Frame(self.parent, bg=COLORS['bg_main'])
        header_frame.pack(fill='x', padx=SPACING['lg'], pady=(SPACING['lg'], SPACING['md']))
        
        title = tk.Label(
            header_frame,
            text="👥 Gestión de Clientes",
            font=(FONTS['family'], FONTS['title'], 'bold'),
            bg=COLORS['bg_main'],
            fg=COLORS['text_primary']
        )
        title.pack(side='left')
        
        search_frame = tk.Frame(self.parent, bg=COLORS['bg_main'])
        search_frame.pack(fill='x', padx=SPACING['lg'], pady=SPACING['md'])
        
        tk.Label(
            search_frame,
            text="Buscar:",
            font=(FONTS['family'], FONTS['body']),
            bg=COLORS['bg_main'],
            fg=COLORS['text_primary']
        ).pack(side='left', padx=(0, SPACING['sm']))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.search_customers())
        
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=(FONTS['family'], FONTS['body']),
            width=30,
            relief='solid',
            borderwidth=1
        )
        search_entry.pack(side='left', padx=SPACING['sm'])
        
        btn_new = tk.Button(
            search_frame,
            text="➕ Nuevo Cliente",
            command=self.show_add_customer_dialog,
            **BUTTON_STYLES['primary']
        )
        btn_new.pack(side='right', padx=SPACING['sm'])
        
        table_frame = tk.Frame(self.parent, bg=COLORS['bg_card'])
        table_frame.pack(fill='both', expand=True, padx=SPACING['lg'], pady=SPACING['md'])
        
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side='right', fill='y')
        
        columns = ('ID', 'Nombre', 'Teléfono', 'Email', 'Dirección')
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            yscrollcommand=scrollbar.set,
            selectmode='browse'
        )
        
        self.tree.heading('ID', text='ID')
        self.tree.heading('Nombre', text='Nombre')
        self.tree.heading('Teléfono', text='Teléfono')
        self.tree.heading('Email', text='Email')
        self.tree.heading('Dirección', text='Dirección')
        
        self.tree.column('ID', width=50, anchor='center')
        self.tree.column('Nombre', width=200, anchor='w')
        self.tree.column('Teléfono', width=120, anchor='w')
        self.tree.column('Email', width=200, anchor='w')
        self.tree.column('Dirección', width=250, anchor='w')
        
        self.tree.pack(fill='both', expand=True)
        scrollbar.config(command=self.tree.yview)
        
        self.tree.bind('<<TreeviewSelect>>', self.on_customer_select)
        
        actions_frame = tk.Frame(self.parent, bg=COLORS['bg_main'])
        actions_frame.pack(fill='x', padx=SPACING['lg'], pady=SPACING['md'])
        
        self.btn_edit = tk.Button(
            actions_frame,
            text="✏️ Editar",
            command=self.show_edit_customer_dialog,
            state='disabled',
            **BUTTON_STYLES['secondary']
        )
        self.btn_edit.pack(side='left', padx=SPACING['sm'])
        
        self.btn_delete = tk.Button(
            actions_frame,
            text="🗑️ Eliminar",
            command=self.delete_customer,
            state='disabled',
            **BUTTON_STYLES['danger']
        )
        self.btn_delete.pack(side='left', padx=SPACING['sm'])
    
    def load_customers(self, search_term=''):
        """Carga los clientes en la tabla"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if search_term:
            customers = self.db.search_customers(search_term)
        else:
            customers = self.db.get_all_customers()
        
        for customer in customers:
            self.tree.insert('', 'end', values=(
                customer['id'],
                customer['name'],
                customer['phone'] or '',
                customer['email'] or '',
                customer['address'] or ''
            ))
    
    def search_customers(self):
        """Busca clientes según el término de búsqueda"""
        search_term = self.search_var.get()
        self.load_customers(search_term)
    
    def on_customer_select(self, event):
        """Maneja la selección de un cliente en la tabla"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            self.selected_customer_id = item['values'][0]
            self.btn_edit.config(state='normal')
            self.btn_delete.config(state='normal')
        else:
            self.selected_customer_id = None
            self.btn_edit.config(state='disabled')
            self.btn_delete.config(state='disabled')
    
    def show_add_customer_dialog(self):
        """Muestra diálogo para agregar cliente"""
        self.show_customer_dialog(mode='add')
    
    def show_edit_customer_dialog(self):
        """Muestra diálogo para editar cliente"""
        if not self.selected_customer_id:
            return
        self.show_customer_dialog(mode='edit', customer_id=self.selected_customer_id)
    
    def show_customer_dialog(self, mode='add', customer_id=None):
        """Muestra diálogo para agregar o editar cliente"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Nuevo Cliente" if mode == 'add' else "Editar Cliente")
        dialog.geometry("520x580")
        dialog.update_idletasks()
        _sw = dialog.winfo_screenwidth()
        _sh = dialog.winfo_screenheight()
        dialog.geometry(f"520x580+{(_sw-520)//2}+{(_sh-580)//2}")
        dialog.resizable(False, False)
        dialog.configure(bg=COLORS['bg_card'])
        dialog.transient(self.parent)
        dialog.grab_set()
        
        customer_data = None
        if mode == 'edit' and customer_id:
            customer_data = self.db.get_customer_by_id(customer_id)
        
        main_container = tk.Frame(dialog, bg=COLORS['bg_card'])
        main_container.pack(fill='both', expand=True)
        
        form_frame = tk.Frame(main_container, bg=COLORS['bg_card'], padx=SPACING['lg'], pady=SPACING['lg'])
        form_frame.pack(fill='both', expand=True)
        
        tk.Label(
            form_frame,
            text="Nuevo Cliente" if mode == 'add' else "Editar Cliente",
            font=(FONTS['family'], FONTS['heading'], 'bold'),
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        ).pack(anchor='w', pady=(0, SPACING['lg']))
        
        tk.Label(form_frame, text="Nombre del Cliente*", font=(FONTS['family'], FONTS['body']),
                bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 5))
        entry_name = tk.Entry(form_frame, font=(FONTS['family'], FONTS['body']))
        entry_name.pack(fill='x', pady=(0, SPACING['md']))
        if customer_data:
            entry_name.insert(0, customer_data['name'])
        entry_name.focus()
        
        tk.Label(form_frame, text="Teléfono", font=(FONTS['family'], FONTS['body']),
                bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 5))
        entry_phone = tk.Entry(form_frame, font=(FONTS['family'], FONTS['body']))
        entry_phone.pack(fill='x', pady=(0, SPACING['md']))
        if customer_data:
            entry_phone.insert(0, customer_data['phone'] or '')
        
        tk.Label(form_frame, text="Email", font=(FONTS['family'], FONTS['body']),
                bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 5))
        entry_email = tk.Entry(form_frame, font=(FONTS['family'], FONTS['body']))
        entry_email.pack(fill='x', pady=(0, SPACING['md']))
        if customer_data:
            entry_email.insert(0, customer_data['email'] or '')
        
        tk.Label(form_frame, text="Dirección", font=(FONTS['family'], FONTS['body']),
                bg=COLORS['bg_card'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 5))
        entry_address = tk.Text(form_frame, font=(FONTS['family'], FONTS['body']), height=4)
        entry_address.pack(fill='x', pady=(0, SPACING['md']))
        if customer_data:
            entry_address.insert('1.0', customer_data['address'] or '')
        
        buttons_frame = tk.Frame(main_container, bg=COLORS['bg_card'], padx=SPACING['lg'], pady=SPACING['md'])
        buttons_frame.pack(fill='x', side='bottom')
        
        def save_customer():
            is_valid, msg, name = validate_required_field(entry_name.get(), "Nombre")
            if not is_valid:
                messagebox.showerror("Error", msg)
                return
            
            phone = entry_phone.get().strip()
            is_valid, msg, phone = validate_phone(phone)
            if not is_valid:
                messagebox.showerror("Error", msg)
                return
            
            email = entry_email.get().strip()
            is_valid, msg, email = validate_email(email)
            if not is_valid:
                messagebox.showerror("Error", msg)
                return
            
            address = entry_address.get('1.0', 'end').strip()
            
            try:
                if mode == 'add':
                    self.db.add_customer(name, phone, email, address)
                    messagebox.showinfo("Exito", "Cliente agregado correctamente")
                else:
                    self.db.update_customer(customer_id, name, phone, email, address)
                    messagebox.showinfo("Exito", "Cliente actualizado correctamente")
                
                self.load_customers()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {str(e)}")
        
        tk.Button(buttons_frame, text="💾 Guardar", command=save_customer,
                 **BUTTON_STYLES['success']).pack(side='left', padx=SPACING['sm'])
        tk.Button(buttons_frame, text="❌ Cancelar", command=dialog.destroy,
                 **BUTTON_STYLES['secondary']).pack(side='left', padx=SPACING['sm'])
    
    def delete_customer(self):
        """Elimina el cliente seleccionado"""
        if not self.selected_customer_id:
            return
        
        response = messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este cliente?")
        
        if response:
            try:
                self.db.delete_customer(self.selected_customer_id)
                messagebox.showinfo("Exito", "Cliente eliminado correctamente")
                self.load_customers()
                self.selected_customer_id = None
                self.btn_edit.config(state='disabled')
                self.btn_delete.config(state='disabled')
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar: {str(e)}")