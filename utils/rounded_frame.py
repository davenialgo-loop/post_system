# -*- coding: utf-8 -*-
"""
utils/rounded_frame.py — Venialgo POS
Widget con esquinas redondeadas usando Canvas.
No requiere dependencias externas.
"""
import tkinter as tk


class RoundedCard(tk.Frame):
    """
    Frame con bordes redondeados y sombra opcional.

    Uso:
        card = RoundedCard(parent, radius=10)
        card.pack(fill='x', padx=16, pady=8)
        tk.Label(card.inner, text="Contenido").pack()

    Para tarjetas que llenan espacio:
        card.pack(fill='both', expand=True)
    """

    def __init__(self, parent,
                 radius: int  = 10,
                 fill:   str  = '#FFFFFF',
                 outline: str = '#E5E7EB',
                 padx:   int  = 16,
                 pady:   int  = 12,
                 **kw):
        try:
            pbg = parent.cget('bg')
        except Exception:
            pbg = '#F9FAFB'

        super().__init__(parent, bg=pbg, **kw)

        self._r       = radius
        self._fill    = fill
        self._outline = outline

        # Canvas donde se dibuja el rectángulo redondeado
        self._cv = tk.Canvas(self, bg=pbg, highlightthickness=0, bd=0)
        self._cv.pack(fill='both', expand=True)

        # Frame interno donde va el contenido
        self.inner = tk.Frame(self._cv, bg=fill, padx=padx, pady=pady)
        self._wid  = self._cv.create_window(1, 1, anchor='nw', window=self.inner)

        self._cv.bind('<Configure>',   self._on_cv)
        self.inner.bind('<Configure>', self._on_inner)

    # ── dibujo ────────────────────────────────────────────────
    def _draw(self, w: int, h: int):
        self._cv.delete('_rr')
        if w < 6 or h < 6:
            return
        r = min(self._r, w // 2, h // 2)
        # Puntos del polígono suavizado (control points para bezier)
        pts = [
            r,    1,    w-r,  1,
            w-1,  1,    w-1,  r,
            w-1,  h-r,  w-1,  h-1,
            w-r,  h-1,  r,    h-1,
            1,    h-1,  1,    h-r,
            1,    r,    1,    1,
            r,    1,
        ]
        self._cv.create_polygon(
            pts, smooth=True,
            fill=self._fill, outline=self._outline, width=1,
            tags='_rr'
        )
        self._cv.tag_lower('_rr')
        self._cv.itemconfig(self._wid, width=w - 2, height=h - 2)

    # ── eventos ───────────────────────────────────────────────
    def _on_cv(self, event):
        # Sincronizar bg con el padre (si cambió)
        try:
            self._cv.config(bg=self.master.cget('bg'))
            self.config(bg=self.master.cget('bg'))
        except Exception:
            pass
        self._draw(event.width, event.height)

    def _on_inner(self, event):
        # Ajusta la altura al contenido (útil para fill='x')
        new_h = event.height + 2
        if self._cv.winfo_height() != new_h:
            self._cv.config(height=new_h)
        self.after_idle(lambda: self._draw(
            self._cv.winfo_width(), self._cv.winfo_height()
        ))

    # ── método de conveniencia ────────────────────────────────
    def update_colors(self, fill: str = None, outline: str = None):
        """Actualiza los colores sin reconstruir el widget."""
        if fill:    self._fill    = fill
        if outline: self._outline = outline
        self._draw(self._cv.winfo_width(), self._cv.winfo_height())
