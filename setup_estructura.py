"""
setup_estructura.py
Ejecutar UNA SOLA VEZ desde la carpeta raíz del proyecto:
    python setup_estructura.py

Crea todas las carpetas y archivos __init__.py necesarios.
"""

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

# ── Carpetas que deben existir ────────────────────────────────
CARPETAS = [
    "license",
    "security",
    "backup",
    "installer",
    "assets",
    "backups",
    "logs",
    "modules",
    "modules/admin",
    "modules/sales",
    "modules/credits",
    "modules/products",
    "modules/customers",
    "modules/reports",
    "config",
    "database",
]

# ── Paquetes Python que necesitan __init__.py ─────────────────
PAQUETES = [
    "license",
    "security",
    "backup",
    "modules",
    "modules/admin",
    "modules/sales",
    "modules/credits",
    "modules/products",
    "modules/customers",
    "modules/reports",
    "config",
    "database",
]

def crear_estructura():
    print("\n" + "═"*55)
    print("  📁  Configurando estructura del proyecto POS")
    print("  📍  Directorio:", ROOT)
    print("═"*55 + "\n")

    creadas   = []
    existentes = []

    # Crear carpetas
    for carpeta in CARPETAS:
        ruta = os.path.join(ROOT, carpeta.replace("/", os.sep))
        if not os.path.exists(ruta):
            os.makedirs(ruta)
            creadas.append(carpeta)
            print(f"  ✅ Carpeta creada:  {carpeta}/")
        else:
            existentes.append(carpeta)

    print()

    # Crear __init__.py en paquetes
    for paquete in PAQUETES:
        init = os.path.join(ROOT, paquete.replace("/", os.sep), "__init__.py")
        if not os.path.exists(init):
            with open(init, "w") as f:
                f.write(f"# {paquete} package\n")
            print(f"  ✅ Creado:  {paquete}/__init__.py")
        else:
            print(f"  ✓  Ya existe: {paquete}/__init__.py")

    print()

    # Verificar archivos principales
    archivos_requeridos = {
        "main_comercial.py":            "Archivo principal del sistema",
        "license/license_manager.py":   "Sistema de licencias",
        "license/keygen_tool.py":       "Generador de claves (privado)",
        "security/crypto_db.py":        "Encriptación de BD",
        "security/protection.py":       "Protección anti-copia",
        "backup/backup_manager.py":     "Backup automático",
        "modules/admin/admin_ui.py":    "Panel administrador",
        "modules/admin/login_window.py":"Ventana de login",
        "modules/admin/license_ui.py":  "UI de licencia",
    }

    print("  📋  Verificando archivos del sistema:\n")
    faltantes = []
    for archivo, descripcion in archivos_requeridos.items():
        ruta = os.path.join(ROOT, archivo.replace("/", os.sep))
        if os.path.exists(ruta):
            print(f"  ✅  {archivo}")
        else:
            print(f"  ❌  FALTA: {archivo}  ({descripcion})")
            faltantes.append(archivo)

    print()
    print("═"*55)

    if faltantes:
        print(f"\n  ⚠️  Faltan {len(faltantes)} archivo(s).")
        print("  Copiá los archivos faltantes a las rutas indicadas.")
        print()
        for f in faltantes:
            dest = os.path.join(ROOT, f.replace("/", os.sep))
            print(f"    → {dest}")
    else:
        print("\n  ✅  ¡Todo en orden! Podés ejecutar:")
        print("      python main_comercial.py")

    print()

    # Verificar dependencias Python
    print("  🐍  Verificando dependencias Python:\n")
    deps = [("cryptography", "pip install cryptography")]
    for modulo, install_cmd in deps:
        try:
            __import__(modulo)
            print(f"  ✅  {modulo}")
        except ImportError:
            print(f"  ❌  {modulo} — Ejecutá: {install_cmd}")

    print("\n" + "═"*55 + "\n")


if __name__ == "__main__":
    crear_estructura()
    input("  Presioná Enter para cerrar...")