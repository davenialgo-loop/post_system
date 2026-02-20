# -*- coding: utf-8 -*-
"""
fix_database.py
Corrige la base de datos existente agregando columnas faltantes.
Ejecutar UNA SOLA VEZ si hay errores de columnas:
    python fix_database.py
"""
import os, sys, sqlite3

def get_db():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.path.expanduser("~")
    return os.path.join(base, "VenialgoPOS", "pos_database.db")

def fix():
    db = get_db()
    print(f"\nBase de datos: {db}")

    if not os.path.exists(db):
        print("No existe la BD - se creara al iniciar el sistema.")
        return

    conn = sqlite3.connect(db)
    conn.execute("PRAGMA journal_mode=WAL")
    c = conn.cursor()

    # Columnas a agregar si no existen
    migrations = [
        ("productos", "costo",     "REAL DEFAULT 0"),
        ("productos", "stock_min", "INTEGER DEFAULT 0"),
        ("productos", "activo",    "INTEGER DEFAULT 1"),
        ("productos", "codigo",    "TEXT DEFAULT ''"),
        ("productos", "categoria", "TEXT DEFAULT ''"),
        ("clientes",  "activo",    "INTEGER DEFAULT 1"),
        ("clientes",  "ruc",       "TEXT DEFAULT ''"),
        ("clientes",  "correo",    "TEXT DEFAULT ''"),
        ("clientes",  "direccion", "TEXT DEFAULT ''"),
        ("ventas",    "descuento", "REAL DEFAULT 0"),
        ("ventas",    "cliente_nombre", "TEXT DEFAULT 'Consumidor Final'"),
        ("ventas",    "cajero_nombre",  "TEXT DEFAULT ''"),
        ("creditos",  "cliente_nombre", "TEXT DEFAULT ''"),
        ("creditos",  "cuotas",    "INTEGER DEFAULT 1"),
        ("creditos",  "venta_id",  "INTEGER DEFAULT 0"),
    ]

    ok = 0
    skip = 0
    for tabla, col, tipo in migrations:
        try:
            c.execute(f"ALTER TABLE {tabla} ADD COLUMN {col} {tipo}")
            print(f"  [+] {tabla}.{col} agregada")
            ok += 1
        except Exception:
            skip += 1  # ya existia

    conn.commit()
    conn.close()
    print(f"\n  Columnas agregadas: {ok}  |  Ya existian: {skip}")
    print("  Base de datos corregida exitosamente.")

fix()
print()
input("Presiona Enter para cerrar...")
