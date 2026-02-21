"""
window_icon.py — Helper para aplicar ícono de Venialgo a cualquier ventana
Uso: from utils.window_icon import set_icon; set_icon(my_toplevel)
"""
import os, sys

def set_icon(window):
    """Aplica el ícono venialgo.ico a una ventana Tk/Toplevel."""
    base = os.path.dirname(os.path.abspath(
        sys.executable if getattr(sys, 'frozen', False) else __file__))
    # Subir dos niveles desde utils/ hasta la raíz del proyecto
    root_dir = os.path.dirname(base)

    candidates_ico = [
        os.path.join(root_dir, 'assets', 'venialgosist.ico'),
        os.path.join(root_dir, 'assets', 'app_icon.ico'),
        os.path.join(base,     'assets', 'venialgosist.ico'),
        os.path.join(base,     'assets', 'app_icon.ico'),
    ]
    for path in candidates_ico:
        if os.path.isfile(path):
            try:
                window.iconbitmap(path)
                return
            except Exception:
                pass

    candidates_png = [
        os.path.join(root_dir, 'assets', 'VenialgoSistemasLogo.png'),
        os.path.join(base,     'assets', 'VenialgoSistemasLogo.png'),
    ]
    for path in candidates_png:
        if os.path.isfile(path):
            try:
                from PIL import Image, ImageTk
                img   = Image.open(path).resize((32, 32), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                window.iconphoto(True, photo)
                window._icon_ref = photo
                return
            except Exception:
                pass
