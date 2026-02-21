# -*- coding: utf-8 -*-
"""
build_exe.py - Compilador PyInstaller
Venialgo Sistemas POS v1.1

USO: python build_exe.py
"""

import os, sys, shutil, subprocess
from pathlib import Path

APP_NAME    = "POS"
APP_VERSION = "1.1"
MAIN_SCRIPT = "main_comercial.py"
DIST_DIR    = "dist"
BUILD_DIR   = "build"

HIDDEN_IMPORTS = [
    "cryptography", "cryptography.fernet",
    "cryptography.hazmat", "cryptography.hazmat.primitives",
    "tkinter", "tkinter.ttk", "tkinter.messagebox", "tkinter.filedialog",
    "sqlite3", "hashlib", "hmac", "uuid", "zipfile", "threading",
    "PIL", "PIL.Image", "PIL.ImageTk",
]

DATAS = [
    ("assets", "assets"),
    ("config", "config"),
]

def linea(c="-", n=55): print(c * n)

def clean_build():
    for d in [DIST_DIR, BUILD_DIR]:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"  [X] Eliminado: {d}/")

def check_pyinstaller():
    try:
        import PyInstaller
        print(f"  [OK] PyInstaller {PyInstaller.__version__}")
        return True
    except ImportError:
        print("  [!] Instala PyInstaller: pip install pyinstaller")
        return False

def build():
    print()
    linea("=")
    print(f"  Compilando {APP_NAME} v{APP_VERSION} - Venialgo Sistemas")
    linea("=")
    print()

    if not check_pyinstaller():
        input("\n  Presiona Enter para salir...")
        sys.exit(1)

    clean_build()
    print()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",
        "--windowed",
        "--name", APP_NAME,
        "--clean",
        "--noconfirm",
    ]

    # Icono - solo agregar si existe Y es valido
    icon_path = os.path.join("assets", "venialgo.ico")
    if os.path.exists(icon_path):
        # Verificar que PIL puede abrirlo antes de pasarlo a PyInstaller
        try:
            from PIL import Image
            with Image.open(icon_path) as im:
                im.verify()
            cmd += ["--icon", icon_path]
            print(f"  [OK] Icono: {icon_path}")
        except Exception as e:
            print(f"  [!] Icono ignorado (formato incompatible): {e}")
            print(f"  [i] El .exe se compilara sin icono personalizado")
    else:
        print(f"  [i] Sin icono (se usara el predeterminado)")

    for hi in HIDDEN_IMPORTS:
        cmd += ["--hidden-import", hi]

    sep = ";" if sys.platform == "win32" else ":"
    for src, dst in DATAS:
        if os.path.exists(src):
            cmd += ["--add-data", f"{src}{sep}{dst}"]
            print(f"  [+] Datos: {src} -> {dst}")

    if not os.path.exists(MAIN_SCRIPT):
        print(f"\n  [ERROR] No se encontro: {MAIN_SCRIPT}")
        input("\n  Presiona Enter para salir...")
        sys.exit(1)

    cmd.append(MAIN_SCRIPT)

    print()
    linea()
    print("  Compilando... (1-3 minutos)")
    linea()
    print()

    result = subprocess.run(cmd)

    print()
    linea("=")
    if result.returncode == 0:
        exe = Path(DIST_DIR) / APP_NAME / f"{APP_NAME}.exe"
        print("  COMPILACION EXITOSA!")
        if exe.exists():
            mb = exe.stat().st_size / 1024 / 1024
            print(f"  Ejecutable: {exe}")
            print(f"  Tamano:     {mb:.1f} MB")
        print()
        print("  Siguiente paso:")
        print("  Inno Setup -> abrir setup_pos.iss -> F9")
    else:
        print("  ERROR en la compilacion.")
        print("  Lee los mensajes arriba para mas detalles.")
    linea("=")
    print()
    input("  Presiona Enter para cerrar...")

if __name__ == "__main__":
    build()