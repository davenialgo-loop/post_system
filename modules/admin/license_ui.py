"""
UI de Activación de Licencia y Contrato de Uso
Venialgo Sistemas — POS  |  Diseño moderno consistente con el sistema
"""

import tkinter as tk
from tkinter import messagebox
import os, sys
from datetime import datetime
import json

# ── Paleta consistente con el sistema ─────────────────────────
THEME = {
    "sb_bg":        "#0D1B4B",
    "sb_mid":       "#1A3A8F",
    "card_bg":      "#FFFFFF",
    "ct_bg":        "#F9FAFB",
    "acc_blue":     "#2563EB",
    "acc_blue_dk":  "#1D4ED8",
    "acc_green":    "#059669",
    "acc_green_dk": "#047857",
    "acc_rose":     "#E11D48",
    "acc_amber":    "#D97706",
    "txt_primary":  "#111827",
    "txt_secondary":"#6B7280",
    "txt_white":    "#FFFFFF",
    "border":       "#E5E7EB",
    "input_brd":    "#D1D5DB",
    "footer_bg":    "#0F172A",
    "footer_fg":    "#64748B",
    "hw_bg":        "#EFF6FF",
    "hw_border":    "#BFDBFE",
    "hw_txt":       "#1D4ED8",
}
FONT = "Segoe UI"

CONTACT = {
    "email":    "davenialgo@proton.me",
    "whatsapp": "+595 994-686 493",
    "web":      "www.venialgosistemas.com",
}

# ── EULA ──────────────────────────────────────────────────────
def _get_eula_file():
    base = os.environ.get("APPDATA", os.path.expanduser("~")) if sys.platform=="win32" \
           else os.path.expanduser("~")
    d = os.path.join(base, "VenialgoPOS")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "contrato_uso.accepted")

EULA_FILE = _get_eula_file()

EULA_TEXT = """\
CONTRATO DE LICENCIA DE USO DE SOFTWARE
Sistema de Punto de Venta (POS)
© 2024 Venialgo Sistemas — Todos los derechos reservados
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. CONCESIÓN DE LICENCIA
   Venialgo Sistemas le otorga una licencia no exclusiva, intransferible
   y limitada para instalar y usar el Software en el número de equipos
   indicado en su licencia, exclusivamente para sus operaciones comerciales.

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
   que el Software sea libre de errores. La responsabilidad máxima se
   limita al valor pagado por la licencia.

7. TERMINACIÓN
   Esta licencia se termina automáticamente si incumple cualquiera de
   sus términos. Al terminar, debe destruir todas las copias del Software.

8. LEY APLICABLE
   Este contrato se rige por las leyes de la República del Paraguay.
   Cualquier disputa se someterá a los tribunales de Asunción.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Soporte técnico:
  ✉  davenialgo@proton.me
  📱 WhatsApp: +595 994-686 493
  🌐 www.venialgosistemas.com
"""

def eula_accepted() -> bool:
    return os.path.exists(EULA_FILE)

def mark_eula_accepted():
    try:
        with open(EULA_FILE, 'w') as f:
            json.dump({"accepted": True, "date": datetime.now().isoformat()}, f)
    except Exception:
        pass
    return True


# ── Helpers UI ────────────────────────────────────────────────

def _apply_icon(window):
    if getattr(sys, "frozen", False):
        start = os.path.dirname(sys.executable)
    else:
        start = os.path.dirname(os.path.abspath(__file__))
    cur = start
    for _ in range(4):
        for name in ["venialgosist.ico", "venialgo.ico", "app_icon.ico"]:
            p = os.path.join(cur, "assets", name)
            if os.path.isfile(p):
                try: window.iconbitmap(p); return
                except: pass
        cur = os.path.dirname(cur)

def _gradient_header(parent, w, h, title, subtitle):
    """Canvas con degradado azul + textos centrados."""
    canvas = tk.Canvas(parent, width=w, height=h, highlightthickness=0, bd=0)
    canvas.pack(fill="x")
    r1,g1,b1 = 0x0D,0x1B,0x4B
    r2,g2,b2 = 0x1A,0x3A,0x8F
    for i in range(h):
        t = i/h
        r=int(r1+(r2-r1)*t); g=int(g1+(g2-g1)*t); b=int(b1+(b2-b1)*t)
        canvas.create_line(0,i,w,i, fill=f"#{r:02x}{g:02x}{b:02x}")
    canvas.create_text(w//2, h//2-10, text=title,
                       font=(FONT, 13, "bold"), fill=THEME["txt_white"], anchor="center")
    canvas.create_text(w//2, h//2+12, text=subtitle,
                       font=(FONT, 9), fill="#9DB4E0", anchor="center")
    return canvas

def _btn(parent, text, cmd, bg, hover=None):
    hover = hover or bg
    lbl = tk.Label(parent, text=text, font=(FONT, 10, "bold"),
                   bg=bg, fg=THEME["txt_white"], cursor="hand2",
                   padx=20, pady=10)
    lbl.bind("<Enter>",           lambda e: lbl.config(bg=hover))
    lbl.bind("<Leave>",           lambda e: lbl.config(bg=bg))
    lbl.bind("<ButtonRelease-1>", lambda e: cmd())
    return lbl

def _footer(parent):
    f = tk.Frame(parent, bg=THEME["footer_bg"])
    f.pack(fill="x", side="bottom")
    tk.Label(f, text=f"  ✉ {CONTACT['email']}   |   📱 {CONTACT['whatsapp']}   |   🌐 {CONTACT['web']}  ",
             font=(FONT, 7), bg=THEME["footer_bg"], fg=THEME["footer_fg"], pady=6).pack()
    return f

def _center_window(win, w, h):
    win.update_idletasks()
    sw = win.winfo_screenwidth(); sh = win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")


# ════════════════════════════════════════════════════════════
#  CONTRATO DE USO (EULA)
# ════════════════════════════════════════════════════════════

class EULAWindow:
    def __init__(self, root, on_accept, on_reject=None):
        self.root      = root
        self.on_accept = on_accept
        self.on_reject = on_reject or (lambda: root.destroy())

        self.win = tk.Toplevel(root)
        self.win.title("Contrato de Licencia de Uso — Venialgo Sistemas")
        self.win.configure(bg=THEME["ct_bg"])
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self._reject)
        self.win.grab_set()
        _apply_icon(self.win)
        self._build()
        _center_window(self.win, 700, 600)

    def _build(self):
        W = 700
        # Header degradado
        _gradient_header(self.win, W, 72,
                         "📜  Contrato de Licencia de Uso de Software",
                         "Debe leer y aceptar los términos para continuar usando el sistema")

        # Texto del contrato
        body = tk.Frame(self.win, bg=THEME["ct_bg"])
        body.pack(fill="both", expand=True, padx=20, pady=(12,0))

        txt_frame = tk.Frame(body, bg=THEME["border"], padx=1, pady=1)
        txt_frame.pack(fill="both", expand=True)

        txt = tk.Text(txt_frame, wrap="word", font=("Courier New", 9),
                      bg="#F8FAFC", fg=THEME["txt_primary"],
                      relief="flat", padx=14, pady=10,
                      selectbackground=THEME["acc_blue"])
        sb  = tk.Scrollbar(txt_frame, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", EULA_TEXT)
        txt.configure(state="disabled")

        # Checkbox
        self._var_chk = tk.IntVar()
        chk_row = tk.Frame(self.win, bg=THEME["ct_bg"])
        chk_row.pack(fill="x", padx=20, pady=10)
        tk.Checkbutton(chk_row,
                       text="  He leído y acepto los términos del Contrato de Licencia de Uso",
                       variable=self._var_chk,
                       bg=THEME["ct_bg"], activebackground=THEME["ct_bg"],
                       font=(FONT, 10, "bold"), fg=THEME["txt_primary"],
                       selectcolor=THEME["card_bg"],
                       cursor="hand2").pack(side="left")

        # Botones
        btn_row = tk.Frame(self.win, bg=THEME["ct_bg"], pady=8)
        btn_row.pack(fill="x", padx=20)
        _btn(btn_row, "✅  Acepto y Continuar",
             self._accept, THEME["acc_green"], THEME["acc_green_dk"]).pack(side="left", padx=(0,10))
        _btn(btn_row, "✖  No acepto / Salir",
             self._reject, THEME["acc_rose"], "#BE123C").pack(side="left")

        _footer(self.win)

    def _accept(self):
        if not self._var_chk.get():
            messagebox.showwarning("Atención",
                "Debe marcar la casilla para aceptar el contrato.", parent=self.win)
            return
        mark_eula_accepted()
        self.win.destroy()
        self.on_accept()

    def _reject(self):
        self.win.destroy()
        self.on_reject()


# ════════════════════════════════════════════════════════════
#  VENTANA DE ACTIVACIÓN
# ════════════════════════════════════════════════════════════

class ActivationWindow:
    def __init__(self, root, on_success, on_cancel=None):
        self.root       = root
        self.on_success = on_success
        self.on_cancel  = on_cancel or (lambda: None)

        self.win = root
        self.win.title("Activación de Licencia — Venialgo Sistemas")
        self.win.configure(bg=THEME["ct_bg"])
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self._cancelar)
        _apply_icon(self.win)
        self._build()
        _center_window(self.win, 580, 500)

    def _cancelar(self):
        self.win.destroy()
        self.on_cancel()

    def _build(self):
        W = 580
        # Header
        _gradient_header(self.win, W, 72,
                         "🔑  Activación de Licencia",
                         "Sistema de Punto de Venta — Venialgo Sistemas")

        body = tk.Frame(self.win, bg=THEME["ct_bg"], padx=28, pady=20)
        body.pack(fill="both", expand=True)

        # Hardware ID card
        from license.license_manager import get_hardware_id
        hwid = get_hardware_id()

        hw_card = tk.Frame(body, bg=THEME["hw_bg"],
                           highlightbackground=THEME["hw_border"],
                           highlightthickness=1, padx=16, pady=12)
        hw_card.pack(fill="x", pady=(0,18))

        tk.Label(hw_card, text="ID de Hardware de este equipo",
                 font=(FONT, 9, "bold"), bg=THEME["hw_bg"],
                 fg=THEME["hw_txt"]).pack(anchor="w")
        tk.Label(hw_card, text=hwid,
                 font=("Courier New", 12, "bold"),
                 bg=THEME["hw_bg"], fg=THEME["acc_blue"]).pack(anchor="w", pady=(4,2))
        tk.Label(hw_card, text="Proporcione este ID a Venialgo Sistemas para obtener su licencia.",
                 font=(FONT, 8), bg=THEME["hw_bg"],
                 fg=THEME["txt_secondary"]).pack(anchor="w")

        # Estado actual
        from license.license_manager import get_license_info, LicenseStatus
        info   = get_license_info()
        status = info.get("status", "")

        if status == LicenseStatus.VALID:
            st_bg, st_fg = "#ECFDF5", "#065F46"
            st_txt = f"✅  Licencia activa — {info.get('days_left','?')} días restantes | Vence: {info.get('expiry_date','')}"
        elif status == LicenseStatus.EXPIRED:
            st_bg, st_fg = "#FEF2F2", "#991B1B"
            st_txt = "❌  Licencia VENCIDA — Renueve su licencia"
        else:
            st_bg, st_fg = "#FFFBEB", "#92400E"
            st_txt = "⚠️  Sin licencia activa en este equipo"

        status_frame = tk.Frame(body, bg=st_bg,
                                highlightbackground=st_fg,
                                highlightthickness=1, padx=12, pady=8)
        status_frame.pack(fill="x", pady=(0,18))
        tk.Label(status_frame, text=st_txt, font=(FONT, 9, "bold"),
                 bg=st_bg, fg=st_fg).pack(anchor="w")

        # Campo clave
        tk.Label(body, text="Clave de Licencia",
                 font=(FONT, 10, "bold"), bg=THEME["ct_bg"],
                 fg=THEME["txt_primary"]).pack(anchor="w", pady=(0,4))

        self._var_key = tk.StringVar()
        key_frame = tk.Frame(body, bg=THEME["input_brd"], padx=1, pady=1)
        key_frame.pack(fill="x", pady=(0,4))
        key_ent = tk.Entry(key_frame, textvariable=self._var_key,
                           font=("Courier New", 11), relief="flat",
                           bg=THEME["card_bg"], fg=THEME["txt_primary"],
                           insertbackground=THEME["acc_blue"])
        key_ent.pack(fill="x", ipady=7, padx=2)
        key_ent.bind("<FocusIn>",  lambda e: key_frame.config(bg=THEME["acc_blue"]))
        key_ent.bind("<FocusOut>", lambda e: key_frame.config(bg=THEME["input_brd"]))

        tk.Label(body, text="Formato: XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX",
                 font=(FONT, 8), bg=THEME["ct_bg"],
                 fg=THEME["txt_secondary"]).pack(anchor="w", pady=(0,20))

        # Botones
        btn_row = tk.Frame(body, bg=THEME["ct_bg"])
        btn_row.pack(anchor="w")
        _btn(btn_row, "⚡  Activar Licencia",
             self._activate, THEME["acc_green"], THEME["acc_green_dk"]).pack(side="left", padx=(0,10))
        _btn(btn_row, "✖  Cancelar",
             self.on_cancel, "#6B7280", "#4B5563").pack(side="left")

        _footer(self.win)

    def _activate(self):
        from license.license_manager import activate_license
        key = self._var_key.get().strip()
        if not key:
            messagebox.showwarning("Atención", "Ingrese la clave de licencia.", parent=self.win)
            return
        ok, msg = activate_license(key)
        if ok:
            messagebox.showinfo("✅ Activación exitosa", msg, parent=self.win)
            self.win.destroy()
            self.on_success()
        else:
            messagebox.showerror("Error de activación",
                msg + "\n\nVerifique que la clave sea correcta.\n"
                      "Si el problema persiste contacte a Venialgo Sistemas:\n"
                      "+595 994-686 493",
                parent=self.win)


# ════════════════════════════════════════════════════════════
#  PANEL DE LICENCIA (dentro del módulo Configuración)
# ════════════════════════════════════════════════════════════

class LicensePanel:
    def __init__(self, parent):
        self.parent = parent
        self._build()

    def _build(self):
        from license.license_manager import get_license_info, get_hardware_id, LicenseStatus

        frm = tk.Frame(self.parent, bg=THEME["ct_bg"])
        frm.pack(fill="both", expand=True, padx=24, pady=20)

        info   = get_license_info()
        status = info.get("status", LicenseStatus.NOT_FOUND)

        # ── Estado badge ──────────────────────────────────────
        if status == LicenseStatus.VALID:
            badge_bg, badge_fg = THEME["acc_green"], THEME["txt_white"]
            badge_txt = "✅  Sistema Licenciado"
            card_bg, card_border = "#ECFDF5", "#6EE7B7"
            card_fg = "#065F46"
        elif status == LicenseStatus.EXPIRED:
            badge_bg, badge_fg = THEME["acc_rose"], THEME["txt_white"]
            badge_txt = "❌  Licencia Vencida"
            card_bg, card_border = "#FEF2F2", "#FECACA"
            card_fg = "#991B1B"
        else:
            badge_bg, badge_fg = THEME["acc_amber"], THEME["txt_white"]
            badge_txt = "⚠️  Sin Licencia"
            card_bg, card_border = "#FFFBEB", "#FDE68A"
            card_fg = "#92400E"

        badge = tk.Frame(frm, bg=badge_bg, padx=20, pady=10)
        badge.pack(anchor="w", pady=(0,16))
        tk.Label(badge, text=badge_txt, font=(FONT, 12, "bold"),
                 bg=badge_bg, fg=badge_fg).pack()

        # ── Info card ─────────────────────────────────────────
        card = tk.Frame(frm, bg=card_bg,
                        highlightbackground=card_border,
                        highlightthickness=1, padx=20, pady=16)
        card.pack(fill="x", pady=(0,20))

        if status == LicenseStatus.VALID:
            detalles = [
                ("Cliente:",         info.get("client_id", "—")),
                ("Vence:",           info.get("expiry_date", "—")),
                ("Días restantes:",  str(info.get("days_left", "—"))),
                ("Hardware ID:",     info.get("hwid", get_hardware_id())),
            ]
        else:
            detalles = [
                ("Hardware ID:", get_hardware_id()),
                ("Estado:",      status),
            ]

        for lbl, val in detalles:
            row = tk.Frame(card, bg=card_bg)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=lbl, font=(FONT, 9, "bold"),
                     bg=card_bg, fg=card_fg, width=16, anchor="w").pack(side="left")
            tk.Label(row, text=val, font=("Courier New" if "ID" in lbl else FONT, 10),
                     bg=card_bg, fg=THEME["txt_primary"]).pack(side="left", padx=4)

        if status != LicenseStatus.VALID:
            tk.Label(card,
                     text="Contacte a Venialgo Sistemas para obtener o renovar su licencia.",
                     font=(FONT, 9), bg=card_bg, fg=THEME["txt_secondary"]).pack(anchor="w", pady=(8,0))

        # ── Botón activar ─────────────────────────────────────
        btn_txt = "🔑  Activar Licencia" if status != LicenseStatus.VALID else "🔄  Renovar / Cambiar Licencia"
        _btn(frm, btn_txt, self._open_activation,
             THEME["acc_blue"], THEME["acc_blue_dk"]).pack(anchor="w", pady=(0,24))

        # ── Contacto ──────────────────────────────────────────
        tk.Frame(frm, bg=THEME["border"], height=1).pack(fill="x", pady=(0,16))
        tk.Label(frm, text="¿Necesitás una licencia?",
                 font=(FONT, 11, "bold"), bg=THEME["ct_bg"],
                 fg=THEME["txt_primary"]).pack(anchor="w", pady=(0,10))

        for icon, label, val in [
            ("✉",  "Email:",    CONTACT["email"]),
            ("📱", "WhatsApp:", CONTACT["whatsapp"]),
            ("🌐", "Web:",      CONTACT["web"]),
        ]:
            row = tk.Frame(frm, bg=THEME["ct_bg"])
            row.pack(anchor="w", pady=3)
            tk.Label(row, text=f"{icon}  {label}",
                     font=(FONT, 10, "bold"), bg=THEME["ct_bg"],
                     fg=THEME["txt_secondary"], width=12, anchor="w").pack(side="left")
            tk.Label(row, text=val, font=(FONT, 10),
                     bg=THEME["ct_bg"], fg=THEME["acc_blue"],
                     cursor="hand2").pack(side="left")

    def _open_activation(self):
        win = tk.Toplevel(self.parent)
        win.withdraw()
        _apply_icon(win)
        ActivationWindow(win,
                         on_success=lambda: (win.destroy(), self._refresh()),
                         on_cancel=win.destroy)
        win.deiconify()

    def _refresh(self):
        for w in self.parent.winfo_children():
            w.destroy()
        self.__init__(self.parent)
