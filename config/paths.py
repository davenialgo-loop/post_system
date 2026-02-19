# -*- coding: utf-8 -*-
"""
config/paths.py
===============
Gestor central de rutas del sistema POS.

PROBLEMA:
    C:\\Program Files\\VenialgoPOS\\  <- Windows NO permite escribir aqui
    
SOLUCION:
    C:\\Users\\Usuario\\AppData\\Roaming\\VenialgoPOS\\  <- Siempre escribible

Todos los modulos deben importar las rutas desde aqui:
    from config.paths import DB_FILE, BACKUP_DIR, LOGO_DIR, APP_DATA_DIR
"""

import os
import sys

# ── Nombre de la aplicacion ───────────────────────────────────
APP_NAME = "VenialgoPOS"


# ── Directorio de datos del usuario ──────────────────────────
# Windows: C:\Users\<usuario>\AppData\Roaming\VenialgoPOS\
# Linux:   /home/<usuario>/.VenialgoPOS/
# Mac:     /Users/<usuario>/Library/Application Support/VenialgoPOS/

def get_app_data_dir() -> str:
    """
    Retorna la carpeta de datos de la app, siempre con permisos de escritura.
    La crea si no existe.
    """
    if sys.platform == "win32":
        # %APPDATA% = C:\Users\<usuario>\AppData\Roaming
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.path.expanduser("~")

    app_dir = os.path.join(base, APP_NAME)
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


# ── Rutas principales ─────────────────────────────────────────
APP_DATA_DIR = get_app_data_dir()

# Base de datos
DB_FILE = os.path.join(APP_DATA_DIR, "pos_database.db")

# Backups
BACKUP_DIR = os.path.join(APP_DATA_DIR, "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

# Logos de empresa
LOGO_DIR = os.path.join(APP_DATA_DIR, "logos")
os.makedirs(LOGO_DIR, exist_ok=True)

# Logs
LOG_DIR = os.path.join(APP_DATA_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Archivos de control
LICENSE_FILE      = os.path.join(APP_DATA_DIR, "license.dat")
ACTIVATION_FILE   = os.path.join(APP_DATA_DIR, "activation.dat")
INTEGRITY_FILE    = os.path.join(APP_DATA_DIR, ".integrity")
FIRST_RUN_FLAG    = os.path.join(APP_DATA_DIR, ".first_run_done")
EULA_FILE         = os.path.join(APP_DATA_DIR, "contrato_uso.accepted")


# ── Directorio de instalacion (solo lectura) ──────────────────
# Donde esta el ejecutable POS.exe
def get_install_dir() -> str:
    if getattr(sys, "frozen", False):
        # Ejecutando como .exe compilado con PyInstaller
        return os.path.dirname(sys.executable)
    else:
        # Ejecutando como script Python normal
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INSTALL_DIR = get_install_dir()

# Assets (solo lectura - vienen con el instalador)
ASSETS_DIR = os.path.join(INSTALL_DIR, "assets")


if __name__ == "__main__":
    # Ejecutar este archivo directamente para ver las rutas configuradas
    print()
    print("=" * 55)
    print("  Rutas del Sistema POS - Venialgo Sistemas")
    print("=" * 55)
    print(f"  AppData dir : {APP_DATA_DIR}")
    print(f"  Base datos  : {DB_FILE}")
    print(f"  Backups     : {BACKUP_DIR}")
    print(f"  Logos       : {LOGO_DIR}")
    print(f"  Licencia    : {LICENSE_FILE}")
    print(f"  Instalacion : {INSTALL_DIR}")
    print(f"  Assets      : {ASSETS_DIR}")
    print()
    print("  Verificando permisos de escritura...")
    test_file = os.path.join(APP_DATA_DIR, "_test_write.tmp")
    try:
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        print("  [OK] Directorio de datos con permisos correctos")
    except Exception as e:
        print(f"  [ERROR] Sin permisos de escritura: {e}")
    print("=" * 55)
    print()
    input("  Presiona Enter para cerrar...")