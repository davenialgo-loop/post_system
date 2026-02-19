"""
UI de Activación de Licencia y Contrato de Uso
Venialgo Sistemas — POS
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
from datetime import datetime

try:
    from config.settings import COLORS, FONTS, SPACING
except ImportError:
    COLORS  = {'primary': '#2563eb', 'bg_card': '#ffffff', 'bg_main': '#f1f5f9',
               'bg_sidebar': '#1e293b', 'text_white': '#ffffff',
               'text_secondary': '#64748b', 'success': '#16a34a', 'danger': '#dc2626'}
    FONTS   = {'family': 'Segoe UI', 'title': 16, 'subtitle': 13, 'body': 10, 'small': 9}
    SPACING = {'xs': 4, 'sm': 8, 'md': 12, 'lg': 16, 'xl': 24}

from license.license_manager import (
    activate_license, get_license_info, get_hardware_id,
    is_licensed, LicenseStatus
)

import sys as _sys_eula
def _get_eula_file():
    import os
    if _sys_eula.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.path.expanduser("~")
    d = os.path.join(base, "VenialgoPOS")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "contrato_uso.accepted")
EULA_FILE = _get_eula_file()
COMPANY_NAME = "Venialgo Sistemas"


# ════════════════════════════════════════════════════════
#  CONTRATO DE USO (EULA)
# ════════════════════════════════════════════════════════

EULA_TEXT = """
CONTRATO DE LICENCIA DE USO DE SOFTWARE
Sistema de Punto de Venta (POS)
© 2024 Venialgo Sistemas — Todos los derechos reservados

────────────────────────────────────────────────────────────

1. CONCESIÓN DE LICENCIA
   Venialgo Sistemas le otorga una licencia no exclusiva, intransferible y
   limitada para instalar y usar el Software en el número de equipos indicado
   en su licencia, exclusivamente para sus operaciones comerciales internas.

2. RESTRICCIONES
   Queda estrictamente prohibido:
   a) Copiar, modificar, descompilar o hacer ingeniería inversa del Software.
   b) Distribuir, vender, alquilar o sublicenciar el Software a terceros.
   c) Usar el Software en más equipos de los autorizados por su licencia.
   d) Remover o alterar avisos de derechos de autor o marcas registradas.
   e) Intentar eludir los mecanismos de protección o licenciamiento.

3. PROPIEDAD INTELECTUAL
   El Software, su código fuente, documentación y todos los materiales
   relacionados son propiedad exclusiva de Venialgo Sistemas y están
   protegidos por las leyes de derechos de autor aplicables.

4. ACTUALIZACIONES Y SOPORTE
   Las actualizaciones se proporcionarán según los términos del plan
   adquirido. Venialgo Sistemas no está obligado a ofrecer soporte técnico
   más allá de lo incluido en el contrato de servicio vigente.

5. DATOS DEL CLIENTE
   Los datos ingresados en el sistema son propiedad del cliente.
   Venialgo Sistemas no accede, comparte ni almacena datos del negocio
   del cliente en servidores propios sin autorización expresa.

6. GARANTÍA LIMITADA
   El Software se provee "tal como está". Venialgo Sistemas no garantiza
   que el Software sea libre de errores. La responsabilidad máxima de
   Venialgo Sistemas se limita al valor pagado por la licencia.

7. TERMINACIÓN
   Esta licencia se termina automáticamente si incumple cualquiera de
   sus términos. Al terminar, debe destruir todas las copias del Software.

8. LEY APLICABLE
   Este contrato se rige por las leyes de la República del Paraguay.
   Cualquier disputa se someterá a los tribunales de Asunción.

────────────────────────────────────────────────────────────

Para soporte técnico:
  📧 Email:     davenialgo@proton.me
  📱 WhatsApp:  +595 994-686 493
  🌐 Web:       www.venialgosistemas.com
"""


def eula_accepted() -> bool:
    return os.path.exists(EULA_FILE)


def mark_eula_accepted():
    try:
        with open(EULA_FILE, 'w') as f:
            json.dump({"accepted": True,
                       "date": datetime.now().isoformat()}, f)
        return True
    except Exception as e:
        print(f"Warning: no se pudo guardar EULA: {e}")
        return True  # Continuar de todas formas


class EULAWindow:
    """
    Muestra el contrato de uso. Bloquea el uso hasta que se acepte.
    on_accept() se llama si el usuario acepta.
    on_reject() se llama (o cierra app) si rechaza.
    """

    def __init__(self, root, on_accept, on_reject=None):
        self.root      = root
        self.on_accept = on_accept
        self.on_reject = on_reject or (lambda: root.destroy())

        self.win = tk.Toplevel(root)
        self.win.title("Contrato de Licencia de Uso — Venialgo Sistemas")
        self.win.geometry("680x580")
        self.win.configure(bg=COLORS['bg_card'])
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self._reject)
        self._center()
        self._build()

    def _center(self):
        self.win.update_idletasks()
        x = (self.win.winfo_screenwidth()  - 680) // 2
        y = (self.win.winfo_screenheight() - 580) // 2
        self.win.geometry(f"680x580+{x}+{y}")

    def _build(self):
        # Header
        hdr = tk.Frame(self.win, bg=COLORS['bg_sidebar'], pady=12)
        hdr.pack(fill='x')
        tk.Label(hdr, text="📜  Contrato de Licencia de Uso de Software",
                 font=(FONTS['family'], FONTS['subtitle'], 'bold'),
                 bg=COLORS['bg_sidebar'],
                 fg=COLORS['text_white']).pack()
        tk.Label(hdr, text="Debe aceptar los términos para continuar",
                 font=(FONTS['family'], FONTS['small']),
                 bg=COLORS['bg_sidebar'], fg='#94a3b8').pack()

        # Texto del contrato
        frm_txt = tk.Frame(self.win, bg=COLORS['bg_card'])
        frm_txt.pack(fill='both', expand=True, padx=16, pady=12)

        txt = tk.Text(frm_txt, wrap='word', font=("Courier New", 9),
                      bg='#f8fafc', fg='#1e293b', relief='solid', bd=1,
                      padx=12, pady=8)
        sb = ttk.Scrollbar(frm_txt, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        txt.pack(side='left', fill='both', expand=True)
        sb.pack(side='left', fill='y')
        txt.insert('1.0', EULA_TEXT)
        txt.configure(state='disabled')

        # Checkbox aceptar
        self._var_accept = tk.IntVar()
        frm_chk = tk.Frame(self.win, bg=COLORS['bg_card'])
        frm_chk.pack(fill='x', padx=16, pady=(0,8))
        tk.Checkbutton(frm_chk,
                       text="He leído y acepto los términos del Contrato de Licencia de Uso",
                       variable=self._var_accept,
                       bg=COLORS['bg_card'],
                       font=(FONTS['family'], FONTS['body'], 'bold'),
                       fg=COLORS['bg_sidebar']).pack(side='left')

        # Botones
        frm_btn = tk.Frame(self.win, bg=COLORS['bg_card'], pady=10)
        frm_btn.pack(fill='x', padx=16)
        tk.Button(frm_btn, text="✅  Acepto y Continuar",
                  command=self._accept,
                  bg=COLORS['success'], fg=COLORS['text_white'],
                  font=(FONTS['family'], FONTS['body'], 'bold'),
                  relief='flat', padx=16, pady=8, cursor='hand2',
                  width=22).pack(side='left', padx=(0,8))
        tk.Button(frm_btn, text="✖  No acepto / Salir",
                  command=self._reject,
                  bg=COLORS['danger'], fg=COLORS['text_white'],
                  font=(FONTS['family'], FONTS['body'], 'bold'),
                  relief='flat', padx=16, pady=8, cursor='hand2',
                  width=22).pack(side='left')

    def _accept(self):
        if not self._var_accept.get():
            messagebox.showwarning("Atención",
                "Debe marcar la casilla para aceptar el contrato.",
                parent=self.win)
            return
        mark_eula_accepted()
        self.win.destroy()
        self.on_accept()

    def _reject(self):
        self.win.destroy()
        self.on_reject()


# ════════════════════════════════════════════════════════
#  VENTANA DE ACTIVACIÓN
# ════════════════════════════════════════════════════════

class ActivationWindow:
    """
    Ventana para ingresar y activar la clave de licencia.
    on_success() se llama si la activacion es exitosa.
    on_cancel()  se llama si el usuario cancela.
    """

    def __init__(self, root, on_success, on_cancel=None):
        self.root       = root
        self.on_success = on_success
        self.on_cancel  = on_cancel or (lambda: None)

        # Usar root directamente como ventana (no crear Toplevel dentro)
        self.win = root
        self.win.title("Activacion de Licencia - Venialgo Sistemas")
        self.win.geometry("560x480")
        self.win.configure(bg=COLORS['bg_card'])
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self._cancelar)
        self._center()
        self._build()

    def _cancelar(self):
        self.win.destroy()
        self.on_cancel()

    def _center(self):
        self.win.update_idletasks()
        x = (self.win.winfo_screenwidth()  - 560) // 2
        y = (self.win.winfo_screenheight() - 480) // 2
        self.win.geometry(f"560x480+{x}+{y}")

    def _build(self):
        # Header
        hdr = tk.Frame(self.win, bg='#1e3a5f', pady=16)
        hdr.pack(fill='x')
        tk.Label(hdr, text="🔑  Activación de Licencia",
                 font=(FONTS['family'], 14, 'bold'),
                 bg='#1e3a5f', fg='white').pack()
        tk.Label(hdr, text="Sistema de Punto de Venta — Venialgo Sistemas",
                 font=(FONTS['family'], FONTS['small']),
                 bg='#1e3a5f', fg='#93c5fd').pack()

        # Card
        card = tk.Frame(self.win, bg=COLORS['bg_card'], padx=30, pady=20)
        card.pack(fill='both', expand=True, padx=20, pady=12)

        # Hardware ID
        hwid = get_hardware_id()
        frm_hw = tk.Frame(card, bg='#f0f9ff', pady=8, padx=12,
                          relief='solid', bd=1)
        frm_hw.pack(fill='x', pady=(0,16))
        tk.Label(frm_hw, text="ID de Hardware de este equipo",
                 font=(FONTS['family'], FONTS['small'], 'bold'),
                 bg='#f0f9ff', fg='#0369a1').pack(anchor='w')
        tk.Label(frm_hw, text=hwid,
                 font=("Courier New", 12, 'bold'),
                 bg='#f0f9ff', fg='#0284c7').pack(anchor='w', pady=(4,0))
        tk.Label(frm_hw,
                 text="Proporcione este ID a Venialgo Sistemas para obtener su licencia.",
                 font=(FONTS['family'], FONTS['small']),
                 bg='#f0f9ff', fg='#64748b').pack(anchor='w', pady=(4,0))

        # Ingreso de clave
        tk.Label(card, text="Ingrese su Clave de Licencia:",
                 font=(FONTS['family'], FONTS['body'], 'bold'),
                 bg=COLORS['bg_card'], fg='#1e293b').pack(anchor='w', pady=(8,4))

        self._var_key = tk.StringVar()
        tk.Entry(card, textvariable=self._var_key,
                 font=("Courier New", 11),
                 width=48, relief='solid', bd=1).pack(fill='x', pady=(0,6))
        tk.Label(card,
                 text="Formato: XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX",
                 font=(FONTS['family'], FONTS['small']),
                 bg=COLORS['bg_card'], fg='#94a3b8').pack(anchor='w')

        # Estado actual
        info = get_license_info()
        status = info.get('status', '')
        if status == LicenseStatus.VALID:
            state_text = (f"✅ Licencia activa — {info.get('days_left','?')} días restantes  "
                          f"| Vence: {info.get('expiry_date','')}")
            state_bg = '#f0fdf4'
            state_fg = '#16a34a'
        elif status == LicenseStatus.EXPIRED:
            state_text = "❌ Licencia VENCIDA — Renueve su licencia"
            state_bg = '#fef2f2'
            state_fg = '#dc2626'
        else:
            state_text = "⚠️ Sin licencia activa en este equipo"
            state_bg = '#fffbeb'
            state_fg = '#d97706'

        frm_status = tk.Frame(card, bg=state_bg, pady=6, padx=10)
        frm_status.pack(fill='x', pady=(16,0))
        tk.Label(frm_status, text=state_text,
                 font=(FONTS['family'], FONTS['small'], 'bold'),
                 bg=state_bg, fg=state_fg).pack(anchor='w')

        # Botones
        frm_btn = tk.Frame(card, bg=COLORS['bg_card'])
        frm_btn.pack(fill='x', pady=(20,0))
        tk.Button(frm_btn, text="⚡  Activar Licencia",
                  command=self._activate,
                  bg=COLORS['success'], fg=COLORS['text_white'],
                  font=(FONTS['family'], FONTS['body'], 'bold'),
                  relief='flat', padx=14, pady=9, cursor='hand2',
                  width=20).pack(side='left', padx=(0,8))
        tk.Button(frm_btn, text="✖  Cancelar",
                  command=self.on_cancel,
                  bg=COLORS['danger'], fg=COLORS['text_white'],
                  font=(FONTS['family'], FONTS['body'], 'bold'),
                  relief='flat', padx=14, pady=9, cursor='hand2',
                  width=14).pack(side='left')

        # Footer info
        tk.Label(card,
                 text="📧 davenialgo@proton.me  |  📱 +595 994-686 493",
                 font=(FONTS['family'], FONTS['small']),
                 bg=COLORS['bg_card'], fg='#94a3b8').pack(pady=(20,0))

    def _activate(self):
        key = self._var_key.get().strip()
        if not key:
            messagebox.showwarning("Atencion",
                "Ingrese la clave de licencia.", parent=self.win)
            return

        ok, msg = activate_license(key)
        if ok:
            messagebox.showinfo("Activacion exitosa", msg, parent=self.win)
            self.win.destroy()
            self.on_success()
        else:
            messagebox.showerror("Error de activacion",
                msg + "\n\nVerifique que la clave sea correcta.\n"
                      "Si el problema persiste contacte a Venialgo Sistemas:\n"
                      "+595 994-686 493",
                parent=self.win)


# ════════════════════════════════════════════════════════
#  PANEL DE LICENCIA (dentro del módulo admin)
# ════════════════════════════════════════════════════════

class LicensePanel:
    """
    Panel de información de licencia para incluir en AdminModule.
    Uso: LicensePanel(parent_frame)
    """

    def __init__(self, parent):
        self.parent = parent
        self._build()

    def _build(self):
        frm = tk.Frame(self.parent, bg=COLORS['bg_main'])
        frm.pack(fill='both', expand=True)

        # Header
        tk.Label(frm, text="🔑  Información de Licencia",
                 font=(FONTS['family'], FONTS['subtitle'], 'bold'),
                 bg=COLORS['bg_main'], fg=COLORS['primary']).pack(
            anchor='w', padx=20, pady=(16,4))
        ttk.Separator(frm).pack(fill='x', padx=20, pady=(0,12))

        info = get_license_info()
        status = info.get('status', LicenseStatus.NOT_FOUND)

        # Tarjeta de estado
        if status == LicenseStatus.VALID:
            card_bg, icon, state_lbl = '#f0fdf4', '✅', 'ACTIVA'
            lbl_fg = '#166534'
        elif status == LicenseStatus.EXPIRED:
            card_bg, icon, state_lbl = '#fef2f2', '❌', 'VENCIDA'
            lbl_fg = '#991b1b'
        else:
            card_bg, icon, state_lbl = '#fffbeb', '⚠️', 'NO ACTIVADA'
            lbl_fg = '#92400e'

        card = tk.Frame(frm, bg=card_bg, padx=24, pady=20,
                        relief='solid', bd=1)
        card.pack(fill='x', padx=20, pady=8)

        tk.Label(card, text=f"{icon}  Licencia {state_lbl}",
                 font=(FONTS['family'], 14, 'bold'),
                 bg=card_bg, fg=lbl_fg).pack(anchor='w')

        if status == LicenseStatus.VALID:
            detalles = [
                ("Cliente:",         info.get('client_id', '-')),
                ("Vence:",           info.get('expiry_date', '-')),
                ("Días restantes:",  str(info.get('days_left', '-'))),
                ("Hardware ID:",     info.get('hwid', get_hardware_id())),
            ]
            for lbl, val in detalles:
                rf = tk.Frame(card, bg=card_bg)
                rf.pack(fill='x', pady=2)
                tk.Label(rf, text=lbl,
                         font=(FONTS['family'], FONTS['body'], 'bold'),
                         bg=card_bg, fg='#374151', width=18, anchor='w').pack(side='left')
                tk.Label(rf, text=val,
                         font=(FONTS['family'], FONTS['body']),
                         bg=card_bg, fg='#1e293b').pack(side='left')
        else:
            tk.Label(card,
                     text="Hardware ID: " + get_hardware_id(),
                     font=("Courier New", 10),
                     bg=card_bg, fg='#374151').pack(anchor='w', pady=(8,0))
            tk.Label(card,
                     text="Contacte a Venialgo Sistemas para obtener su licencia.",
                     font=(FONTS['family'], FONTS['small']),
                     bg=card_bg, fg='#64748b').pack(anchor='w', pady=(4,0))

        # Botón activar / renovar
        btn_lbl = "🔑  Activar Licencia" if status != LicenseStatus.VALID else "🔄  Renovar / Cambiar Licencia"
        tk.Button(frm, text=btn_lbl,
                  command=self._open_activation,
                  bg=COLORS['primary'], fg=COLORS['text_white'],
                  font=(FONTS['family'], FONTS['body'], 'bold'),
                  relief='flat', padx=16, pady=9, cursor='hand2').pack(
            anchor='w', padx=20, pady=(8,0))

        # Contacto
        frm_contact = tk.LabelFrame(frm, text=" Soporte técnico ",
                                    bg=COLORS['bg_main'],
                                    font=(FONTS['family'], FONTS['small'], 'bold'),
                                    fg=COLORS['primary'], padx=16, pady=12)
        frm_contact.pack(fill='x', padx=20, pady=20)
        contactos = [
            ("📧 Email:",    "davenialgo@proton.me"),
            ("📱 WhatsApp:", "+595 994-686 493"),
            ("🌐 Web:",      "www.venialgosistemas.com"),
        ]
        for lbl, val in contactos:
            rf = tk.Frame(frm_contact, bg=COLORS['bg_main'])
            rf.pack(fill='x', pady=2)
            tk.Label(rf, text=lbl,
                     font=(FONTS['family'], FONTS['body'], 'bold'),
                     bg=COLORS['bg_main'], fg='#374151',
                     width=14, anchor='w').pack(side='left')
            tk.Label(rf, text=val,
                     font=(FONTS['family'], FONTS['body']),
                     bg=COLORS['bg_main'], fg=COLORS['primary']).pack(side='left')

    def _open_activation(self):
        win = tk.Toplevel(self.parent)
        win.withdraw()
        ActivationWindow(win,
                         on_success=lambda: (win.destroy(),
                                             self._refresh()),
                         on_cancel=win.destroy)
        win.deiconify()

    def _refresh(self):
        for w in self.parent.winfo_children():
            w.destroy()
        self.__init__(self.parent)
