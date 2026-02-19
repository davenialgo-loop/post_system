# -*- coding: utf-8 -*-
"""
fix_paths.py
============
Actualiza todos los archivos del proyecto para usar
config/paths.py en lugar de rutas hardcodeadas.

Ejecutar UNA SOLA VEZ desde la raiz del proyecto:
    python fix_paths.py
"""

import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))

# ── Archivos a parchear ───────────────────────────────────────
FILES_TO_PATCH = [
    "modules/admin/admin_ui.py",
    "modules/admin/login_window.py",
    "modules/admin/license_ui.py",
    "modules/admin/first_run_wizard.py",
    "license/license_manager.py",
    "security/protection.py",
    "security/crypto_db.py",
    "backup/backup_manager.py",
    "utils/company_header.py",
    "main_comercial.py",
]

# ── Patrones a reemplazar ─────────────────────────────────────
# (buscar, reemplazar)
REPLACEMENTS = [
    # Quitar definicion hardcodeada de DB_FILE
    (
        'DB_FILE      = "pos_database.db"',
        'from config.paths import DB_FILE'
    ),
    (
        'DB_FILE = "pos_database.db"',
        'from config.paths import DB_FILE'
    ),
    (
        "DB_FILE      = 'pos_database.db'",
        'from config.paths import DB_FILE'
    ),
    (
        "DB_FILE = 'pos_database.db'",
        'from config.paths import DB_FILE'
    ),
    # Quitar definicion hardcodeada de LICENSE_FILE
    (
        'LICENSE_FILE    = "license.dat"',
        'from config.paths import LICENSE_FILE'
    ),
    (
        'LICENSE_FILE = "license.dat"',
        'from config.paths import LICENSE_FILE'
    ),
    # Quitar definicion hardcodeada de ACTIVATION_FILE
    (
        'ACTIVATION_FILE = "activation.dat"',
        'from config.paths import ACTIVATION_FILE'
    ),
    # Quitar definicion hardcodeada de BACKUP_DIR
    (
        'BACKUP_DIR   = Path("backups")',
        'from config.paths import BACKUP_DIR as _BD; BACKUP_DIR = Path(_BD)'
    ),
    (
        'BACKUP_DIR = Path("backups")',
        'from config.paths import BACKUP_DIR as _BD; BACKUP_DIR = Path(_BD)'
    ),
    # Quitar definicion hardcodeada de FIRST_RUN_FLAG
    (
        'FIRST_RUN_FLAG = ".first_run_done"',
        'from config.paths import FIRST_RUN_FLAG'
    ),
    # Quitar definicion hardcodeada de EULA_FILE
    (
        'EULA_FILE    = "contrato_uso.accepted"',
        'from config.paths import EULA_FILE'
    ),
    (
        'EULA_FILE = "contrato_uso.accepted"',
        'from config.paths import EULA_FILE'
    ),
    # Quitar definicion hardcodeada de LOGO_DIR
    (
        'LOGO_DIR     = Path("assets/logos")',
        'from config.paths import LOGO_DIR as _LD; LOGO_DIR = Path(_LD)'
    ),
    (
        'LOGO_DIR = Path("assets/logos")',
        'from config.paths import LOGO_DIR as _LD; LOGO_DIR = Path(_LD)'
    ),
    # Integrity file
    (
        '_INTEGRITY_FILE  = ".integrity"',
        'from config.paths import INTEGRITY_FILE as _INTEGRITY_FILE'
    ),
    (
        '_INTEGRITY_FILE = ".integrity"',
        'from config.paths import INTEGRITY_FILE as _INTEGRITY_FILE'
    ),
]


def patch_file(filepath):
    full = os.path.join(ROOT, filepath.replace("/", os.sep))
    if not os.path.exists(full):
        print(f"  [!] No encontrado: {filepath}")
        return False

    with open(full, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    original  = content
    changes   = 0

    for old, new in REPLACEMENTS:
        if old in content:
            content = content.replace(old, new)
            changes += 1

    # Evitar imports duplicados
    lines      = content.split("\n")
    seen       = set()
    clean      = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("from config.paths import"):
            if stripped in seen:
                continue
            seen.add(stripped)
        clean.append(line)
    content = "\n".join(clean)

    if content != original:
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  [OK] Actualizado ({changes} cambios): {filepath}")
        return True
    else:
        print(f"  [--] Sin cambios: {filepath}")
        return False


def main():
    print()
    print("=" * 55)
    print("  fix_paths.py - Actualizando rutas del proyecto")
    print("  Venialgo Sistemas POS")
    print("=" * 55)
    print()
    print("  Parcheando archivos...")
    print()

    patched = 0
    for f in FILES_TO_PATCH:
        if patch_file(f):
            patched += 1

    print()
    print("-" * 55)
    print(f"  Archivos actualizados: {patched} de {len(FILES_TO_PATCH)}")
    print()

    # Verificar que paths.py existe
    paths_file = os.path.join(ROOT, "config", "paths.py")
    if os.path.exists(paths_file):
        print("  [OK] config/paths.py existe")
    else:
        print("  [!] FALTA config/paths.py - copialo a config/")

    print()
    print("  Rutas de datos configuradas para:")
    import sys
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "~")
        print(f"  {appdata}\\VenialgoPOS\\")
    else:
        print(f"  ~/.VenialgoPOS/")

    print()
    print("  Listo. Ahora recompila con: python build_exe.py")
    print("=" * 55)
    print()
    input("  Presiona Enter para cerrar...")


if __name__ == "__main__":
    main()