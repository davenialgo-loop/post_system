"""
╔══════════════════════════════════════════════════════════╗
║   GENERADOR DE LICENCIAS — Venialgo Sistemas             ║
║   HERRAMIENTA EXCLUSIVA DEL DESARROLLADOR                ║
║   *** NO DISTRIBUIR AL CLIENTE ***                       ║
╚══════════════════════════════════════════════════════════╝

Uso:
    python keygen_tool.py

Genera claves de licencia para distribuir a clientes.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timedelta

# Asegurarse de que el path raíz esté disponible
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from license.license_manager import generate_license_key, _decode_key, get_hardware_id

# ── Clave maestra (misma que en license_manager.py) ──────
_MASTER_SECRET = b"VenialgoPOS2024#SecretMaster$Key!XYZ987"

COLORES = {
    "bg":      "#0f172a",
    "card":    "#1e293b",
    "accent":  "#6366f1",
    "success": "#22c55e",
    "danger":  "#ef4444",
    "text":    "#f1f5f9",
    "muted":   "#94a3b8",
}


class KeygenTool:
    def __init__(self, root):
        self.root = root
        self.root.title("🔑 Generador de Licencias — Venialgo Sistemas [PRIVADO]")
        self.root.geometry("700x620")
        self.root.configure(bg=COLORES["bg"])
        self.root.resizable(False, False)
        self._center()
        self._build()

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()  - 700) // 2
        y = (self.root.winfo_screenheight() - 620) // 2
        self.root.geometry(f"700x620+{x}+{y}")

    def _lbl(self, parent, text, size=10, bold=False, color=None):
        return tk.Label(parent, text=text,
                        bg=parent.cget('bg'),
                        fg=color or COLORES["text"],
                        font=("Segoe UI", size, 'bold' if bold else 'normal'))

    def _entry(self, parent, var, width=38):
        return tk.Entry(parent, textvariable=var,
                        bg="#334155", fg=COLORES["text"],
                        insertbackground=COLORES["text"],
                        font=("Segoe UI", 10),
                        relief='flat', width=width,
                        highlightthickness=1,
                        highlightbackground="#475569",
                        highlightcolor=COLORES["accent"])

    def _build(self):
        # Header
        hdr = tk.Frame(self.root, bg=COLORES["accent"], pady=14)
        hdr.pack(fill='x')
        self._lbl(hdr, "🔑  GENERADOR DE LICENCIAS — VENIALGO SISTEMAS",
                  14, True, "white").pack()
        self._lbl(hdr, "Herramienta privada del desarrollador — No distribuir",
                  9, color="#e0e7ff").pack()

        # Card principal
        card = tk.Frame(self.root, bg=COLORES["card"], padx=30, pady=20)
        card.pack(fill='both', expand=True, padx=20, pady=16)

        # ── Sección: Datos del cliente ────────────────────
        self._lbl(card, "DATOS DEL CLIENTE", 10, True,
                  COLORES["accent"]).grid(row=0, column=0, columnspan=2,
                                          sticky='w', pady=(0,8))

        campos = [
            ("ID / Nombre cliente *", "client_id"),
            ("Empresa",               "empresa"),
            ("RUC",                   "ruc"),
        ]
        self._vars = {}
        for i, (lbl, key) in enumerate(campos):
            self._lbl(card, lbl, 9, color=COLORES["muted"]).grid(
                row=i+1, column=0, sticky='w', pady=5, padx=(0,16))
            var = tk.StringVar()
            self._entry(card, var).grid(row=i+1, column=1, pady=5, sticky='w')
            self._vars[key] = var

        # ── Sección: Parámetros de licencia ──────────────
        self._lbl(card, "PARÁMETROS DE LICENCIA", 10, True,
                  COLORES["accent"]).grid(row=5, column=0, columnspan=2,
                                          sticky='w', pady=(16,8))

        # Días de validez
        self._lbl(card, "Validez", 9, color=COLORES["muted"]).grid(
            row=6, column=0, sticky='w', pady=5, padx=(0,16))
        self._var_dias = tk.StringVar(value="365")
        dias_opts = ["30 días (prueba)", "90 días", "180 días",
                     "365 días (1 año)", "730 días (2 años)", "Ilimitado (9999)"]
        self._dias_map = {
            "30 días (prueba)": 30, "90 días": 90, "180 días": 180,
            "365 días (1 año)": 365, "730 días (2 años)": 730, "Ilimitado (9999)": 9999
        }
        cb_dias = ttk.Combobox(card, values=list(self._dias_map.keys()),
                               width=36, state='readonly',
                               font=("Segoe UI", 10))
        cb_dias.current(3)
        cb_dias.grid(row=6, column=1, pady=5, sticky='w')
        cb_dias.bind("<<ComboboxSelected>>",
                     lambda e: self._var_dias.set(
                         str(self._dias_map[cb_dias.get()])))
        self._cb_dias = cb_dias

        # Activaciones
        self._lbl(card, "Máx. activaciones", 9, color=COLORES["muted"]).grid(
            row=7, column=0, sticky='w', pady=5, padx=(0,16))
        self._var_act = tk.StringVar(value="1")
        ttk.Combobox(card, textvariable=self._var_act,
                     values=["1","2","3","5"],
                     width=36, state='readonly',
                     font=("Segoe UI", 10)).grid(
            row=7, column=1, pady=5, sticky='w')

        # ── Botón Generar ─────────────────────────────────
        tk.Button(card, text="⚡  GENERAR CLAVE",
                  command=self._generate,
                  bg=COLORES["accent"], fg="white",
                  font=("Segoe UI", 11, 'bold'),
                  relief='flat', pady=10, cursor='hand2',
                  width=30).grid(row=8, column=0, columnspan=2,
                                  pady=(20,8))

        # ── Resultado ─────────────────────────────────────
        self._lbl(card, "CLAVE GENERADA", 10, True,
                  COLORES["success"]).grid(row=9, column=0, columnspan=2,
                                            sticky='w', pady=(8,4))

        self._var_key = tk.StringVar()
        key_entry = tk.Entry(card, textvariable=self._var_key,
                             bg="#0f2d0f", fg=COLORES["success"],
                             font=("Courier New", 11, 'bold'),
                             relief='flat', width=52,
                             state='readonly',
                             readonlybackground="#0f2d0f")
        key_entry.grid(row=10, column=0, columnspan=2, pady=4, sticky='w')

        frm_btns = tk.Frame(card, bg=COLORES["card"])
        frm_btns.grid(row=11, column=0, columnspan=2, pady=8, sticky='w')
        tk.Button(frm_btns, text="📋 Copiar",
                  command=self._copy,
                  bg="#334155", fg="white",
                  font=("Segoe UI", 9), relief='flat',
                  cursor='hand2', padx=12, pady=6).pack(side='left', padx=(0,8))
        tk.Button(frm_btns, text="💾 Guardar registro",
                  command=self._save_record,
                  bg="#334155", fg="white",
                  font=("Segoe UI", 9), relief='flat',
                  cursor='hand2', padx=12, pady=6).pack(side='left', padx=(0,8))
        tk.Button(frm_btns, text="🔍 Verificar clave",
                  command=self._verify,
                  bg="#334155", fg="white",
                  font=("Segoe UI", 9), relief='flat',
                  cursor='hand2', padx=12, pady=6).pack(side='left')

        # Hardware ID local
        hwid = get_hardware_id()
        self._lbl(card, f"Hardware ID de este equipo: {hwid}",
                  8, color=COLORES["muted"]).grid(
            row=12, column=0, columnspan=2, sticky='w', pady=(12,0))

    def _generate(self):
        cid = self._vars["client_id"].get().strip().replace(" ", "_").upper()
        if not cid:
            messagebox.showwarning("Atención", "El ID/Nombre del cliente es obligatorio.")
            return

        dias_str = self._var_dias.get()
        if not dias_str:
            dias = self._dias_map[self._cb_dias.get()]
        else:
            dias = int(dias_str)

        max_act = int(self._var_act.get() or 1)
        key     = generate_license_key(cid, "POS", dias, max_act, _MASTER_SECRET)
        self._var_key.set(key)
        self._last_meta = {
            "client_id":    cid,
            "empresa":      self._vars["empresa"].get().strip(),
            "ruc":          self._vars["ruc"].get().strip(),
            "dias":         dias,
            "max_act":      max_act,
            "key":          key,
            "generado_en":  datetime.now().isoformat(),
        }

    def _copy(self):
        key = self._var_key.get()
        if key:
            self.root.clipboard_clear()
            self.root.clipboard_append(key)
            messagebox.showinfo("✅", "Clave copiada al portapapeles.")

    def _save_record(self):
        if not hasattr(self, '_last_meta') or not self._last_meta:
            messagebox.showwarning("Atención", "Genere una clave primero.")
            return
        fname = "licencias_generadas.json"
        records = []
        if os.path.exists(fname):
            try:
                with open(fname) as f:
                    records = json.load(f)
            except Exception:
                records = []
        records.append(self._last_meta)
        with open(fname, 'w') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        messagebox.showinfo("✅", f"Registro guardado en {fname}")

    def _verify(self):
        key = self._var_key.get().strip()
        if not key:
            key = tk.simpledialog.askstring("Verificar", "Pegue la clave a verificar:") or ""
        if not key:
            return
        info = _decode_key(key, _MASTER_SECRET)
        if not info:
            messagebox.showerror("Invalida", "La clave no es valida o fue alterada.")
            return
        from datetime import datetime as dt
        exp_ts = info.get("expiry")
        exp = dt.fromtimestamp(exp_ts).strftime("%d/%m/%Y %H:%M") if exp_ts else "---"
        days_left = info.get("days_left", "?")
        max_act   = info.get("max_act", "?")
        # client_id en _decode_key es el hash de 4 bytes, no el texto original
        # mostramos lo que tenemos
        msg = (f"Clave valida\n\n"
               f"Expira:        {exp}\n"
               f"Dias restantes:{days_left}\n"
               f"Max activ.:    {max_act}")
        messagebox.showinfo("Verificacion OK", msg)


def main():
    root = tk.Tk()
    KeygenTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
