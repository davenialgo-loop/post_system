# -*- coding: utf-8 -*-
"""
database/db_manager.py
DatabaseManager completo para Sistema POS Venialgo Sistemas
Almacena datos en AppData/VenialgoPOS/
"""
import os, sys, sqlite3
from datetime import datetime

def _get_db_path():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.path.expanduser("~")
    d = os.path.join(base, "VenialgoPOS")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "pos_database.db")

DB_PATH = _get_db_path()


def _product_aliases(d: dict) -> dict:
    """Agrega claves en ingles para compatibilidad con los módulos originales."""
    d['name']     = d.get('nombre', '')
    d['price']    = d.get('precio', 0)
    d['cost']     = d.get('costo', 0)
    d['quantity'] = d.get('stock', 0)
    d['stock']    = d.get('stock', 0)
    d['category'] = d.get('categoria', '')
    d['barcode']  = d.get('codigo', '')
    d['code']     = d.get('codigo', '')
    d['active']   = d.get('activo', 1)
    return d

def _client_aliases(d: dict) -> dict:
    """Agrega claves en ingles para compatibilidad."""
    d['name']    = d.get('nombre', '')
    d['phone']   = d.get('telefono', '')
    d['email']   = d.get('correo', '')
    d['address'] = d.get('direccion', '')
    return d

def _credit_aliases(d: dict) -> dict:
    """Mapea columnas de creditos a claves en ingles para credit_ui."""
    monto = d.get('monto_total') or d.get('monto') or 0
    d['total_amount']       = monto
    d['down_payment']       = d.get('cuota_inicial', 0)
    d['remaining_balance']  = d.get('saldo', 0)
    d['installment_amount'] = d.get('cuota_monto', 0)
    d['total_installments'] = d.get('cuotas', 1)
    d['paid_installments']  = d.get('cuotas_pagadas', 0)
    d['payment_frequency']  = d.get('frecuencia', 'monthly')
    d['next_payment_date']  = d.get('proximo_pago', '')
    d['customer_name']      = d.get('cliente_nombre', '')
    d['phone']              = d.get('telefono', '')
    # Mapear estado: 'pendiente'/'active' -> 'active', 'pagado'/'paid' -> 'paid'
    estado = d.get('estado', 'active')
    if estado in ('pendiente', 'active'):
        d['status'] = 'active'
    elif estado in ('pagado', 'paid'):
        d['status'] = 'paid'
    else:
        d['status'] = estado
    return d

def _payment_aliases(d: dict) -> dict:
    d['payment_date'] = d.get('fecha', '')
    d['amount']       = d.get('monto', 0)
    d['notes']        = d.get('nota', '')
    return d

def _sale_aliases(d: dict) -> dict:
    """Agrega claves en ingles para compatibilidad."""
    d['date']           = d.get('fecha', '')
    d['sale_date']      = d.get('fecha', '')
    d['total_amount']   = d.get('total', 0)
    d['client_id']      = d.get('cliente_id', 0)
    d['client_name']    = d.get('cliente_nombre', '')
    d['customer_name']  = d.get('cliente_nombre', '')
    d['cashier']        = d.get('cajero_nombre', '')
    d['payment_method'] = d.get('metodo_pago', d.get('estado', 'Efectivo'))
    return d

class DatabaseManager:

    def __init__(self):
        self.db_path = DB_PATH
        self._ensure_tables()

    # ── Conexion ──────────────────────────────────────────────
    def _conn(self):
        conn = sqlite3.connect(self.db_path, timeout=10,
                               check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")   # evita bloqueos
        conn.execute("PRAGMA busy_timeout=5000")  # 5 seg de espera
        return conn

    def _ensure_tables(self):
        conn = self._conn()
        c = conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS productos (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo    TEXT DEFAULT '',
                nombre    TEXT NOT NULL,
                precio    REAL DEFAULT 0,
                costo     REAL DEFAULT 0,
                stock     INTEGER DEFAULT 0,
                stock_min INTEGER DEFAULT 0,
                categoria TEXT DEFAULT '',
                activo    INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS clientes (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre    TEXT NOT NULL,
                ruc       TEXT DEFAULT '',
                telefono  TEXT DEFAULT '',
                correo    TEXT DEFAULT '',
                direccion TEXT DEFAULT '',
                activo    INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS ventas (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha         TEXT,
                cliente_id    INTEGER DEFAULT 0,
                cliente_nombre TEXT DEFAULT 'Consumidor Final',
                total         REAL DEFAULT 0,
                descuento     REAL DEFAULT 0,
                metodo_pago   TEXT DEFAULT 'Efectivo',
                estado        TEXT DEFAULT 'completada',
                cajero_id     INTEGER DEFAULT 0,
                cajero_nombre TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS detalle_ventas (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id    INTEGER,
                producto_id INTEGER DEFAULT 0,
                nombre      TEXT DEFAULT '',
                cantidad    INTEGER DEFAULT 1,
                precio      REAL DEFAULT 0,
                subtotal    REAL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS creditos (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id         INTEGER,
                cliente_nombre     TEXT DEFAULT '',
                fecha              TEXT,
                monto_total        REAL DEFAULT 0,
                monto              REAL DEFAULT 0,
                cuota_inicial      REAL DEFAULT 0,
                saldo              REAL DEFAULT 0,
                cuota_monto        REAL DEFAULT 0,
                cuotas             INTEGER DEFAULT 1,
                cuotas_pagadas     INTEGER DEFAULT 0,
                frecuencia         TEXT DEFAULT 'monthly',
                proximo_pago       TEXT DEFAULT '',
                estado             TEXT DEFAULT 'active',
                descripcion        TEXT DEFAULT '',
                venta_id           INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS pagos_creditos (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                credito_id INTEGER,
                fecha      TEXT,
                monto      REAL DEFAULT 0,
                nota       TEXT DEFAULT '',
                cajero     TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS empresa (
                id           INTEGER PRIMARY KEY,
                razon_social TEXT DEFAULT '',
                ruc          TEXT DEFAULT '',
                telefono     TEXT DEFAULT '',
                direccion    TEXT DEFAULT '',
                correo       TEXT DEFAULT '',
                logo_path    TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS usuarios (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre    TEXT NOT NULL,
                usuario   TEXT UNIQUE NOT NULL,
                password  TEXT NOT NULL,
                rol       TEXT DEFAULT 'Cajero',
                activo    INTEGER DEFAULT 1,
                creado_en TEXT
            );
            CREATE TABLE IF NOT EXISTS arqueos (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_apertura  TEXT NOT NULL,
                fecha_cierre    TEXT DEFAULT NULL,
                monto_inicial   REAL DEFAULT 0,
                monto_final     REAL DEFAULT NULL,
                total_efectivo  REAL DEFAULT 0,
                total_tarjeta   REAL DEFAULT 0,
                total_transfer  REAL DEFAULT 0,
                total_creditos  REAL DEFAULT 0,
                total_ventas    INTEGER DEFAULT 0,
                diferencia      REAL DEFAULT 0,
                notas           TEXT DEFAULT '',
                usuario_nombre  TEXT DEFAULT '',
                estado          TEXT DEFAULT 'abierto'
            );
            CREATE TABLE IF NOT EXISTS config_precios (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre     TEXT NOT NULL,
                tipo       TEXT NOT NULL,
                cuotas     INTEGER DEFAULT 1,
                porcentaje REAL DEFAULT 0,
                activo     INTEGER DEFAULT 1
            );
        """)
        # Datos por defecto de config_precios
        c.execute("SELECT COUNT(*) FROM config_precios")
        if c.fetchone()[0] == 0:
            defaults = [
                ("Contado",     "contado",  1, 30.0),
                ("Credito 3c",  "credito",  3, 45.0),
                ("Credito 6c",  "credito",  6, 60.0),
                ("Credito 12c", "credito", 12, 80.0),
                ("Credito 18c", "credito", 18,100.0),
                ("Credito 24c", "credito", 24,120.0),
            ]
            for n, t, cu, pct in defaults:
                c.execute("INSERT INTO config_precios (nombre,tipo,cuotas,porcentaje,activo) VALUES (?,?,?,?,1)",
                          (n, t, cu, pct))

        # ── Migración: agregar columnas faltantes a tablas existentes ──
        migrations = [
            ("productos", "costo",     "REAL DEFAULT 0"),
            ("creditos",  "monto_total",   "REAL DEFAULT 0"),
            ("creditos",  "monto",         "REAL DEFAULT 0"),
            ("creditos",  "cuota_inicial",  "REAL DEFAULT 0"),
            ("creditos",  "cuota_monto",    "REAL DEFAULT 0"),
            ("creditos",  "cuotas_pagadas", "INTEGER DEFAULT 0"),
            ("creditos",  "frecuencia",     "TEXT DEFAULT 'monthly'"),
            ("creditos",  "proximo_pago",   "TEXT DEFAULT ''"),
            ("ventas",    "metodo_pago","TEXT DEFAULT 'Efectivo'"),
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
            ("ventas",    "nota",      "TEXT DEFAULT ''"),
        ]
        for tabla, columna, tipo in migrations:
            try:
                c.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}")
            except Exception:
                pass  # Columna ya existe, ignorar

        conn.commit()
        conn.close()

    # ════════════════════════════════════════════════════════
    #  PRODUCTOS
    # ════════════════════════════════════════════════════════
    def get_all_products(self):
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM productos WHERE activo=1 ORDER BY nombre").fetchall()
        conn.close()
        return [_product_aliases(dict(r)) for r in rows]

    def search_products(self, query):
        conn = self._conn()
        q = f"%{query}%"
        rows = conn.execute(
            "SELECT * FROM productos WHERE activo=1 AND (nombre LIKE ? OR codigo LIKE ?)",
            (q, q)).fetchall()
        conn.close()
        return [_product_aliases(dict(r)) for r in rows]

    def get_product_by_id(self, pid):
        conn = self._conn()
        row = conn.execute("SELECT * FROM productos WHERE id=?", (pid,)).fetchone()
        conn.close()
        return _product_aliases(dict(row)) if row else None

    def get_product_by_code(self, code):
        conn = self._conn()
        row = conn.execute(
            "SELECT * FROM productos WHERE codigo=? AND activo=1", (code,)).fetchone()
        conn.close()
        return _product_aliases(dict(row)) if row else None

    def save_product(self, data, pid=None):
        with self._conn() as conn:
            if pid:
                conn.execute("""UPDATE productos SET codigo=?,nombre=?,precio=?,costo=?,
                    stock=?,stock_min=?,categoria=?,activo=? WHERE id=?""",
                    (data.get('codigo',''), data.get('nombre',''),
                     data.get('precio',0), data.get('costo',0),
                     data.get('stock',0), data.get('stock_min',0),
                     data.get('categoria',''), data.get('activo',1), pid))
            else:
                conn.execute("""INSERT INTO productos
                    (codigo,nombre,precio,costo,stock,stock_min,categoria,activo)
                    VALUES (?,?,?,?,?,?,?,?)""",
                    (data.get('codigo',''), data.get('nombre',''),
                     data.get('precio',0), data.get('costo',0),
                     data.get('stock',0), data.get('stock_min',0),
                     data.get('categoria',''), data.get('activo',1)))
            conn.commit()

    def delete_product(self, pid):
        conn = self._conn()
        conn.execute("UPDATE productos SET activo=0 WHERE id=?", (pid,))
        conn.commit()
        conn.close()

    def update_stock(self, pid, cantidad):
        conn = self._conn()
        conn.execute("UPDATE productos SET stock=stock+? WHERE id=?", (cantidad, pid))
        conn.commit()
        conn.close()

    # ════════════════════════════════════════════════════════
    #  CLIENTES
    # ════════════════════════════════════════════════════════
    def get_all_clients(self):
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM clientes WHERE activo=1 ORDER BY nombre").fetchall()
        conn.close()
        return [_client_aliases(dict(r)) for r in rows]

    def search_clients(self, query):
        conn = self._conn()
        # Normalizar: quitar espacios/guiones para buscar CI/RUC con o sin formato
        q_raw   = f"%{query.strip()}%"
        q_clean = f"%{query.strip().replace('-','').replace(' ','')}%"
        # Buscar por nombre, ruc, telefono — con y sin guiones
        rows = conn.execute("""
            SELECT * FROM clientes
            WHERE activo=1 AND (
                nombre   LIKE ? COLLATE NOCASE OR
                ruc      LIKE ? COLLATE NOCASE OR
                ruc      LIKE ? COLLATE NOCASE OR
                telefono LIKE ? COLLATE NOCASE
            )
            ORDER BY nombre""",
            (q_raw, q_raw, q_clean, q_raw)).fetchall()
        conn.close()
        return [_client_aliases(dict(r)) for r in rows]

    def get_client_by_id(self, cid):
        conn = self._conn()
        row = conn.execute("SELECT * FROM clientes WHERE id=?", (cid,)).fetchone()
        conn.close()
        return _client_aliases(dict(row)) if row else None

    def save_client(self, data, cid=None):
        with self._conn() as conn:
            if cid:
                conn.execute("""UPDATE clientes SET nombre=?,ruc=?,telefono=?,correo=?,
                    direccion=? WHERE id=?""",
                    (data.get('nombre',''), data.get('ruc',''), data.get('telefono',''),
                     data.get('correo',''), data.get('direccion',''), cid))
            else:
                conn.execute("""INSERT INTO clientes (nombre,ruc,telefono,correo,direccion)
                    VALUES (?,?,?,?,?)""",
                    (data.get('nombre',''), data.get('ruc',''), data.get('telefono',''),
                     data.get('correo',''), data.get('direccion','')))
            conn.commit()

    def delete_client(self, cid):
        conn = self._conn()
        conn.execute("UPDATE clientes SET activo=0 WHERE id=?", (cid,))
        conn.commit()
        conn.close()

    # ════════════════════════════════════════════════════════
    #  VENTAS
    # ════════════════════════════════════════════════════════
    def create_sale(self, customer_id_or_data, total_or_none=None, payment_method="Efectivo",
                    amount_paid=0, change=0, items=None, is_credit=False, **kwargs):
        """
        Acepta dos firmas:
          create_sale(data_dict, items_list)               -- original
          create_sale(customer_id, total, payment, paid,   -- sale_ui.py
                      change, cart_items, is_credit)
        """
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Detectar firma
        if isinstance(customer_id_or_data, dict):
            # Firma original: create_sale(data_dict, items_list)
            data  = customer_id_or_data
            items = total_or_none or []
            cid   = data.get('cliente_id', 0)
            total = data.get('total', 0)
            pmeth = data.get('metodo_pago', 'Efectivo')
            paid  = data.get('monto_pagado', total)
            chng  = data.get('cambio', 0)
            cname = data.get('cliente_nombre', 'Consumidor Final')
            cajero_id   = data.get('cajero_id', 0)
            cajero_name = data.get('cajero_nombre', '')
        else:
            # Firma positional: create_sale(cust_id, total, payment, paid, change, items, is_credit)
            cid   = customer_id_or_data or 0
            total = total_or_none or 0
            pmeth = payment_method
            paid  = amount_paid
            chng  = change
            items = items or []
            cajero_id   = kwargs.get('cajero_id', 0)
            cajero_name = kwargs.get('cajero_nombre', '')
            # Obtener nombre del cliente
            cname = 'Consumidor Final'
            if cid:
                try:
                    cli = self.get_client_by_id(cid)
                    if cli: cname = cli.get('nombre', cli.get('name', 'Consumidor Final'))
                except: pass

        with self._conn() as conn:
            c = conn.cursor()
            nota_val = kwargs.get('nota','') if not isinstance(customer_id_or_data, dict)                 else customer_id_or_data.get('nota','')
            c.execute("""INSERT INTO ventas
                (fecha,cliente_id,cliente_nombre,total,descuento,metodo_pago,estado,cajero_id,cajero_nombre,nota)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (fecha, cid, cname, total, chng, pmeth, 'completada', cajero_id, cajero_name, nota_val))
            venta_id = c.lastrowid

            for item in items:
                # Aceptar tanto claves en español como en inglés
                prod_id  = item.get('product_id',  item.get('producto_id', 0))
                nombre   = item.get('name',        item.get('nombre', ''))
                cantidad = item.get('quantity',    item.get('cantidad', 1))
                precio   = item.get('unit_price',  item.get('precio', 0))
                subtotal = item.get('subtotal', precio * cantidad)

                # Si no hay nombre, buscar en BD
                if not nombre and prod_id:
                    try:
                        p = self.get_product_by_id(prod_id)
                        if p: nombre = p.get('nombre', p.get('name', ''))
                    except: pass

                c.execute("""INSERT INTO detalle_ventas
                    (venta_id,producto_id,nombre,cantidad,precio,subtotal)
                    VALUES (?,?,?,?,?,?)""",
                    (venta_id, prod_id, nombre, cantidad, precio, subtotal))

                # Descontar stock
                if prod_id:
                    c.execute("UPDATE productos SET stock=stock-? WHERE id=?",
                             (cantidad, prod_id))
            conn.commit()
        return venta_id

    def create_credit_sale(self, sale_id, customer_id, total, down_payment,
                           frequency, installment_amount, installments, first_date):
        """Crea un crédito asociado a una venta."""
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        saldo = total - down_payment

        # Obtener nombre del cliente
        cname = ''
        try:
            cli = self.get_client_by_id(customer_id)
            if cli: cname = cli.get('nombre', cli.get('name', ''))
        except: pass

        with self._conn() as conn:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(creditos)").fetchall()]
            col_monto = "monto_total" if "monto_total" in cols else "monto"
            conn.execute(f"""INSERT INTO creditos
                (cliente_id, cliente_nombre, fecha, {col_monto}, cuota_inicial,
                 saldo, cuota_monto, cuotas, cuotas_pagadas, frecuencia,
                 proximo_pago, estado, descripcion, venta_id)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (customer_id, cname, fecha, total, down_payment,
                 saldo, installment_amount, installments, 0, frequency,
                 first_date, 'active',
                 f"Frecuencia:{frequency} | Cuota:{installment_amount:.0f} | Proximo:{first_date}",
                 sale_id))
            conn.commit()

    def get_sales(self, fecha_desde=None, fecha_hasta=None, limit=100):
        conn = self._conn()
        query = "SELECT * FROM ventas WHERE 1=1"
        params = []
        if fecha_desde:
            query += " AND fecha >= ?"; params.append(fecha_desde)
        if fecha_hasta:
            query += " AND fecha <= ?"; params.append(fecha_hasta + " 23:59:59")
        query += " ORDER BY fecha DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [_sale_aliases(dict(r)) for r in rows]

    def get_sale_detail(self, venta_id):
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM detalle_ventas WHERE venta_id=?", (venta_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_sale_by_id(self, venta_id):
        conn = self._conn()
        row = conn.execute("SELECT * FROM ventas WHERE id=?", (venta_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    # ════════════════════════════════════════════════════════
    #  CREDITOS
    # ════════════════════════════════════════════════════════
    def get_all_credits(self):
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM creditos ORDER BY fecha DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_credits_by_client(self, cid):
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM creditos WHERE cliente_id=? ORDER BY fecha DESC", (cid,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def create_credit(self, data):
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        monto = data.get('monto_total', data.get('monto', 0))
        with self._conn() as conn:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(creditos)").fetchall()]
            col_monto = "monto_total" if "monto_total" in cols else "monto"
            c = conn.cursor()
            c.execute(f"""INSERT INTO creditos
                (cliente_id,cliente_nombre,fecha,{col_monto},saldo,cuotas,estado,descripcion,venta_id)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (data.get('cliente_id',0), data.get('cliente_nombre',''),
                 fecha, monto, monto,
                 data.get('cuotas',1), 'pendiente',
                 data.get('descripcion',''), data.get('venta_id',0)))
            conn.commit()
            return c.lastrowid

    def pay_credit(self, credito_id, monto, nota='', cajero=''):
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._conn() as conn:
            conn.execute("""INSERT INTO pagos_creditos (credito_id,fecha,monto,nota,cajero)
                VALUES (?,?,?,?,?)""", (credito_id, fecha, monto, nota, cajero))
            conn.execute("UPDATE creditos SET saldo=saldo-? WHERE id=?", (monto, credito_id))
            conn.execute("""UPDATE creditos SET estado='pagado'
                WHERE id=? AND saldo<=0""", (credito_id,))
            conn.commit()

    def get_credit_payments(self, credito_id):
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM pagos_creditos WHERE credito_id=? ORDER BY fecha",
            (credito_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ════════════════════════════════════════════════════════
    #  REPORTES
    # ════════════════════════════════════════════════════════
    def get_sales_summary(self, fecha_desde=None, fecha_hasta=None):
        conn = self._conn()
        query = """SELECT
            COUNT(*)       as total_ventas,
            COUNT(*)       as total_sales,
            COALESCE(SUM(total),0) as monto_total,
            COALESCE(SUM(total),0) as total_revenue,
            COALESCE(AVG(total),0) as promedio,
            COALESCE(AVG(total),0) as average_sale
            FROM ventas WHERE estado='completada'"""
        params = []
        if fecha_desde:
            query += " AND fecha >= ?"; params.append(fecha_desde)
        if fecha_hasta:
            query += " AND fecha <= ?"; params.append(fecha_hasta + " 23:59:59")
        row = conn.execute(query, params).fetchone()
        conn.close()
        if row:
            d = dict(row)
            d['total_sales']   = d.get('total_ventas', 0)
            d['total_revenue'] = d.get('monto_total', 0)
            d['average_sale']  = d.get('promedio', 0)
            return d
        return {'total_ventas':0,'total_sales':0,'monto_total':0,'total_revenue':0,'average_sale':0}

    def get_top_products(self, limit=10, fecha_desde=None, fecha_hasta=None):
        conn = self._conn()
        query = """SELECT nombre, SUM(cantidad) as total_vendido, SUM(subtotal) as total_monto
            FROM detalle_ventas GROUP BY nombre ORDER BY total_vendido DESC LIMIT ?"""
        rows = conn.execute(query, (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_credits_summary(self):
        conn = self._conn()
        row = conn.execute("""SELECT COUNT(*) as total, SUM(monto_total) as total_monto,
            SUM(saldo) as total_pendiente FROM creditos""").fetchone()
        conn.close()
        return dict(row) if row else {}

    def get_low_stock_products(self):
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM productos WHERE activo=1 AND stock<=stock_min ORDER BY stock").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ════════════════════════════════════════════════════════
    #  CATEGORIAS
    # ════════════════════════════════════════════════════════
    def get_categories(self):
        conn = self._conn()
        rows = conn.execute(
            "SELECT DISTINCT categoria FROM productos WHERE activo=1 AND categoria!='' ORDER BY categoria").fetchall()
        conn.close()
        return [r[0] for r in rows]

    # ── Alias y métodos adicionales que usan los módulos ─────

    def add_product(self, nombre_o_dict, precio=0, stock=0, categoria="", codigo="",
                    costo=0, stock_min=0, **kwargs):
        """Acepta dict, args posicionales o kwargs mixtos."""
        if isinstance(nombre_o_dict, dict):
            d = nombre_o_dict
            if 'costo' not in d: d['costo'] = kwargs.get('costo', 0)
            return self.save_product(d, pid=None)
        data = {
            "nombre":    nombre_o_dict,
            "precio":    precio,
            "costo":     kwargs.get('costo', costo),
            "stock":     stock,
            "stock_min": stock_min,
            "categoria": categoria,
            "codigo":    codigo,
        }
        return self.save_product(data, pid=None)

    def update_product(self, pid, nombre_o_dict=None, precio=0, stock=0,
                       categoria="", codigo="", costo=0, **kwargs):
        """Acepta dict, args posicionales, o kwargs mixtos."""
        if isinstance(nombre_o_dict, dict):
            d = nombre_o_dict
            if 'costo' not in d: d['costo'] = kwargs.get('costo', 0)
            return self.save_product(d, pid=pid)
        if nombre_o_dict is None:
            return
        data = {
            "nombre":    nombre_o_dict,
            "precio":    precio,
            "costo":     kwargs.get('costo', costo),
            "stock":     stock,
            "stock_min": kwargs.get('stock_min', 0),
            "categoria": categoria,
            "codigo":    codigo,
        }
        return self.save_product(data, pid=pid)

    def get_products(self, search="", categoria=""):
        """Buscar productos con filtros opcionales."""
        conn = self._conn()
        query = "SELECT * FROM productos WHERE activo=1"
        params = []
        if search:
            query += " AND (nombre LIKE ? OR codigo LIKE ?)"
            q = f"%{search}%"
            params += [q, q]
        if categoria:
            query += " AND categoria=?"
            params.append(categoria)
        query += " ORDER BY nombre"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [_product_aliases(dict(r)) for r in rows]

    def add_client(self, nombre_o_dict, ruc="", telefono="", correo="", direccion=""):
        """Acepta dict o args posicionales."""
        if isinstance(nombre_o_dict, dict):
            return self.save_client(nombre_o_dict, cid=None)
        data = {"nombre": nombre_o_dict, "ruc": ruc, "telefono": telefono,
                "correo": correo, "direccion": direccion}
        return self.save_client(data, cid=None)

    def update_client(self, cid, nombre_o_dict=None, ruc="", telefono="", correo="", direccion=""):
        """Acepta dict o args posicionales."""
        if isinstance(nombre_o_dict, dict):
            return self.save_client(nombre_o_dict, cid=cid)
        if nombre_o_dict is None:
            return
        data = {"nombre": nombre_o_dict, "ruc": ruc, "telefono": telefono,
                "correo": correo, "direccion": direccion}
        return self.save_client(data, cid=cid)

    # Alias customer (algunos módulos usan customer en vez de client)
    def add_customer(self, nombre_o_dict, telefono_o_ruc="", email_o_tel="",
                     direccion_o_email="", direccion2=""):
        """
        Acepta dos firmas:
          add_customer(nombre, ruc, telefono, correo, direccion)  -- original
          add_customer(nombre, phone, email, address)             -- modulo ingles
        """
        if isinstance(nombre_o_dict, dict):
            d = nombre_o_dict
            return self.save_client({
                "nombre":   d.get('name', d.get('nombre','')),
                "ruc":      d.get('ruc',''),
                "telefono": d.get('phone', d.get('telefono','')),
                "correo":   d.get('email', d.get('correo','')),
                "direccion":d.get('address', d.get('direccion','')),
            }, cid=None)
        # Detectar si es firma inglesa (phone, email, address) o española (ruc, telefono, correo, dir)
        # Si el 2do arg parece telefono (solo numeros/+) -> firma inglesa
        tel_o_ruc = str(telefono_o_ruc)
        if tel_o_ruc.replace('+','').replace('-','').replace(' ','').isdigit() or not tel_o_ruc:
            # firma inglesa: (nombre, phone, email, address)
            return self.save_client({
                "nombre":    nombre_o_dict,
                "ruc":       "",
                "telefono":  tel_o_ruc,
                "correo":    str(email_o_tel),
                "direccion": str(direccion_o_email),
            }, cid=None)
        else:
            # firma española: (nombre, ruc, telefono, correo, direccion)
            return self.save_client({
                "nombre":    nombre_o_dict,
                "ruc":       tel_o_ruc,
                "telefono":  str(email_o_tel),
                "correo":    str(direccion_o_email),
                "direccion": str(direccion2),
            }, cid=None)

    def update_customer(self, cid, nombre_o_dict=None, telefono_o_ruc="",
                        email_o_tel="", direccion_o_email="", direccion2=""):
        """Acepta firma inglesa (name, phone, email, address) o española."""
        if isinstance(nombre_o_dict, dict):
            d = nombre_o_dict
            return self.save_client({
                "nombre":    d.get('name', d.get('nombre','')),
                "ruc":       d.get('ruc',''),
                "telefono":  d.get('phone', d.get('telefono','')),
                "correo":    d.get('email', d.get('correo','')),
                "direccion": d.get('address', d.get('direccion','')),
            }, cid=cid)
        if nombre_o_dict is None:
            return
        tel_o_ruc = str(telefono_o_ruc)
        if tel_o_ruc.replace('+','').replace('-','').replace(' ','').isdigit() or not tel_o_ruc:
            return self.save_client({
                "nombre":    nombre_o_dict,
                "ruc":       "",
                "telefono":  tel_o_ruc,
                "correo":    str(email_o_tel),
                "direccion": str(direccion_o_email),
            }, cid=cid)
        else:
            return self.save_client({
                "nombre":    nombre_o_dict,
                "ruc":       tel_o_ruc,
                "telefono":  str(email_o_tel),
                "correo":    str(direccion_o_email),
                "direccion": str(direccion2),
            }, cid=cid)

    def delete_customer(self, cid):
        return self.delete_client(cid)

    def get_all_customers(self):
        return self.get_all_clients()

    def search_customers(self, query):
        return self.search_clients(query)

    def get_customers(self, search=""):
        return self.get_clients(search)

    def get_customer_by_id(self, cid):
        return self.get_client_by_id(cid)

    def get_clients(self, search=""):
        """Buscar clientes con filtro opcional."""
        if search:
            return self.search_clients(search)
        return self.get_all_clients()

    def get_sales_by_date(self, fecha_desde=None, fecha_hasta=None):
        """Ventas filtradas por rango de fecha."""
        return self.get_sales(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)

    def get_sale_items(self, venta_id):
        """Alias de get_sale_detail."""
        return self.get_sale_detail(venta_id)

    def get_sales_report(self, fecha_desde=None, fecha_hasta=None):
        """Reporte completo de ventas con resumen."""
        ventas  = self.get_sales(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
        resumen = self.get_sales_summary(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
        return {"ventas": ventas, "resumen": resumen}

    def get_daily_sales(self, fecha=None):
        """Ventas de un día específico."""
        if not fecha:
            from datetime import date
            fecha = date.today().strftime("%Y-%m-%d")
        return self.get_sales(fecha_desde=fecha, fecha_hasta=fecha)

    def get_pending_credits(self):
        """Créditos pendientes de pago."""
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM creditos WHERE estado='pendiente' ORDER BY fecha DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_credit_by_id(self, credito_id):
        conn = self._conn()
        row = conn.execute("SELECT * FROM creditos WHERE id=?", (credito_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def update_credit(self, credito_id, data):
        conn = self._conn()
        conn.execute("""UPDATE creditos SET descripcion=?, cuotas=?, estado=?
            WHERE id=?""",
            (data.get('descripcion',''), data.get('cuotas',1),
             data.get('estado','pendiente'), credito_id))
        conn.commit()
        conn.close()

    def get_stats(self, fecha_desde=None, fecha_hasta=None):
        """Estadísticas generales para reportes."""
        conn = self._conn()
        params_v = []
        where_v  = "WHERE estado='completada'"
        if fecha_desde:
            where_v += " AND fecha >= ?"; params_v.append(fecha_desde)
        if fecha_hasta:
            where_v += " AND fecha <= ?"; params_v.append(fecha_hasta + " 23:59:59")

        ventas = conn.execute(
            f"SELECT COUNT(*) as n, COALESCE(SUM(total),0) as total FROM ventas {where_v}",
            params_v).fetchone()
        creditos = conn.execute(
            "SELECT COUNT(*) as n, COALESCE(SUM(saldo),0) as pendiente FROM creditos WHERE estado='pendiente'"
        ).fetchone()
        productos_bajo = conn.execute(
            "SELECT COUNT(*) as n FROM productos WHERE activo=1 AND stock<=stock_min"
        ).fetchone()
        conn.close()
        return {
            "total_ventas":    ventas["n"]           if ventas    else 0,
            "monto_ventas":    ventas["total"]        if ventas    else 0,
            "creditos_pend":   creditos["n"]          if creditos  else 0,
            "monto_creditos":  creditos["pendiente"]  if creditos  else 0,
            "productos_bajos": productos_bajo["n"]    if productos_bajo else 0,
        }

    def execute_query(self, query, params=()):
        """Ejecutar consulta arbitraria (solo lectura)."""
        conn = self._conn()
        try:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    # ════════════════════════════════════════════════════════
    #  CONFIG PRECIOS
    # ════════════════════════════════════════════════════════
    def get_pricing_configs(self, solo_activos=True):
        conn = self._conn()
        q = "SELECT * FROM config_precios"
        if solo_activos: q += " WHERE activo=1"
        q += " ORDER BY tipo, cuotas"
        rows = conn.execute(q).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def save_pricing_config(self, data, pid=None):
        with self._conn() as conn:
            if pid:
                conn.execute("""UPDATE config_precios
                    SET nombre=?,tipo=?,cuotas=?,porcentaje=?,activo=? WHERE id=?""",
                    (data['nombre'], data['tipo'], data['cuotas'],
                     data['porcentaje'], data.get('activo',1), pid))
            else:
                conn.execute("""INSERT INTO config_precios (nombre,tipo,cuotas,porcentaje,activo)
                    VALUES (?,?,?,?,?)""",
                    (data['nombre'], data['tipo'], data['cuotas'],
                     data['porcentaje'], data.get('activo',1)))
            conn.commit()

    def delete_pricing_config(self, pid):
        with self._conn() as conn:
            conn.execute("UPDATE config_precios SET activo=0 WHERE id=?", (pid,))
            conn.commit()

    def calcular_precios_producto(self, costo: float) -> list:
        """Calcula precios de venta para todas las modalidades activas."""
        configs = self.get_pricing_configs(solo_activos=True)
        result  = []
        for c in configs:
            precio      = round(costo * (1 + c['porcentaje'] / 100), 0)
            cuota_monto = round(precio / c['cuotas'], 0) if c['cuotas'] > 1 else 0
            result.append({
                "id":          c['id'],
                "nombre":      c['nombre'],
                "tipo":        c['tipo'],
                "cuotas":      c['cuotas'],
                "porcentaje":  c['porcentaje'],
                "precio":      precio,
                "cuota_monto": cuota_monto,
            })
        return result
    # ════════════════════════════════════════════════════════
    #  METODOS GENERICOS (execute_*)
    # ════════════════════════════════════════════════════════
    def execute_update(self, table_or_query, data_or_params=None, where="", where_params=()):
        """
        Acepta dos formas:
          execute_update(table, data_dict, where, where_params)  -- estructurado
          execute_update(raw_sql, params_tuple)                  -- SQL directo
        """
        with self._conn() as conn:
            # Detectar si es SQL raw (contiene espacios y palabras clave SQL)
            tq = str(table_or_query).strip().upper()
            if ' ' in tq and any(k in tq for k in ('UPDATE','INSERT','DELETE','SET')):
                # SQL raw: execute_update("UPDATE clientes SET...", (params,))
                # Corregir nombre de tabla si usa ingles
                sql = table_or_query
                sql = sql.replace('customers','clientes').replace('products','productos')
                sql = sql.replace('sales','ventas').replace('credits','creditos')
                params = data_or_params if data_or_params else ()
                conn.execute(sql, params)
            else:
                # Estructurado: execute_update(table, {col: val}, "id=?", (id,))
                if not isinstance(data_or_params, dict):
                    return
                cols = ", ".join(f"{k}=?" for k in data_or_params)
                vals = list(data_or_params.values()) + list(where_params)
                conn.execute(f"UPDATE {table_or_query} SET {cols} WHERE {where}", vals)
            conn.commit()

    def execute_insert(self, table, data: dict):
        """INSERT INTO tabla (cols) VALUES (?)"""
        cols = ", ".join(data.keys())
        phs  = ", ".join("?" for _ in data)
        with self._conn() as conn:
            c = conn.cursor()
            c.execute(f"INSERT INTO {table} ({cols}) VALUES ({phs})",
                      list(data.values()))
            conn.commit()
            return c.lastrowid

    def execute_delete(self, table, where: str, where_params=()):
        """DELETE FROM tabla WHERE ..."""
        with self._conn() as conn:
            conn.execute(f"DELETE FROM {table} WHERE {where}", where_params)
            conn.commit()

    def execute_select(self, query, params=()):
        """SELECT generico, retorna lista de dicts."""
        conn = self._conn()
        try:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def execute_select_one(self, query, params=()):
        """SELECT generico, retorna un dict o None."""
        conn = self._conn()
        try:
            row = conn.execute(query, params).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def execute_scalar(self, query, params=()):
        """SELECT que retorna un solo valor."""
        conn = self._conn()
        try:
            row = conn.execute(query, params).fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def soft_delete(self, table, record_id):
        """Marca como inactivo (activo=0) en lugar de borrar."""
        with self._conn() as conn:
            conn.execute(f"UPDATE {table} SET activo=0 WHERE id=?", (record_id,))
            conn.commit()

    def hard_delete(self, table, record_id):
        """Borra fisicamente el registro."""
        with self._conn() as conn:
            conn.execute(f"DELETE FROM {table} WHERE id=?", (record_id,))
            conn.commit()

    # Alias comunes
    def delete_record(self, table, record_id):
        return self.soft_delete(table, record_id)

    def get_by_id(self, table, record_id):
        conn = self._conn()
        try:
            row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (record_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def count(self, table, where="1=1", params=()):
        conn = self._conn()
        try:
            return conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}", params).fetchone()[0]
        finally:
            conn.close()
    def get_sale_details(self, venta_id):
        """Retorna detalle de venta con claves en ingles para report_ui."""
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM detalle_ventas WHERE venta_id=?", (venta_id,)).fetchall()
        conn.close()
        result = []
        for r in rows:
            d = dict(r)
            d['product_name'] = d.get('nombre', '')
            d['quantity']     = d.get('cantidad', 0)
            d['unit_price']   = d.get('precio', 0)
            d['subtotal']     = d.get('subtotal', 0)
            result.append(d)
        return result
    # ════════════════════════════════════════════════════════
    #  CREDITOS - métodos para credit_ui.py
    # ════════════════════════════════════════════════════════

    def _enrich_credit(self, d: dict) -> dict:
        """Agrega datos del cliente (telefono) al crédito."""
        d = _credit_aliases(d)
        if d.get('cliente_id'):
            try:
                cli = self.get_client_by_id(d['cliente_id'])
                if cli:
                    d['phone'] = cli.get('telefono', cli.get('phone', ''))
            except Exception:
                pass
        return d

    def get_all_credit_sales(self, status=None):
        """Retorna todos los créditos con alias en inglés."""
        conn = self._conn()
        q = "SELECT * FROM creditos WHERE 1=1"
        params = []
        if status == 'active':
            q += " AND estado IN ('active','pendiente')"
        elif status == 'paid':
            q += " AND estado IN ('paid','pagado')"
        q += " ORDER BY fecha DESC"
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [self._enrich_credit(dict(r)) for r in rows]

    def get_overdue_credits(self):
        """Créditos vencidos (próximo pago < hoy y activos)."""
        from datetime import date
        today = date.today().strftime('%Y-%m-%d')
        conn = self._conn()
        rows = conn.execute("""SELECT * FROM creditos
            WHERE estado IN ('active','pendiente')
            AND proximo_pago != '' AND proximo_pago < ?
            ORDER BY proximo_pago""", (today,)).fetchall()
        conn.close()
        return [self._enrich_credit(dict(r)) for r in rows]

    def get_credit_sale_by_id(self, credito_id):
        """Retorna un crédito por ID con alias en inglés."""
        conn = self._conn()
        row = conn.execute("SELECT * FROM creditos WHERE id=?", (credito_id,)).fetchone()
        conn.close()
        return self._enrich_credit(dict(row)) if row else None

    def get_credit_payments(self, credito_id):
        """Historial de pagos de un crédito con alias."""
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM pagos_creditos WHERE credito_id=? ORDER BY fecha",
            (credito_id,)).fetchall()
        conn.close()
        return [_payment_aliases(dict(r)) for r in rows]

    def add_credit_payment(self, credito_id, amount, notes=''):
        """Registra un pago y actualiza saldo y cuotas_pagadas."""
        from datetime import datetime, timedelta
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._conn() as conn:
            conn.execute("""INSERT INTO pagos_creditos (credito_id,fecha,monto,nota)
                VALUES (?,?,?,?)""", (credito_id, fecha, amount, notes))
            conn.execute("UPDATE creditos SET saldo=saldo-?, cuotas_pagadas=cuotas_pagadas+1 WHERE id=?",
                        (amount, credito_id))
            # Marcar como pagado si saldo <= 0
            conn.execute("""UPDATE creditos SET estado='paid'
                WHERE id=? AND saldo<=0""", (credito_id,))
            # Avanzar próximo pago según frecuencia
            row = conn.execute(
                "SELECT frecuencia, proximo_pago FROM creditos WHERE id=?",
                (credito_id,)).fetchone()
            if row and row[1]:
                freq = row[0] or 'monthly'
                days_map = {'weekly':7,'biweekly':15,'monthly':30,'semanal':7,'quincenal':15,'mensual':30}
                days = days_map.get(freq, 30)
                try:
                    nxt = datetime.strptime(row[1], '%Y-%m-%d') + timedelta(days=days)
                    conn.execute("UPDATE creditos SET proximo_pago=? WHERE id=?",
                                (nxt.strftime('%Y-%m-%d'), credito_id))
                except Exception:
                    pass
            conn.commit()

    def update_next_payment_date(self, credito_id, new_date):
        """Actualiza la fecha del próximo pago."""
        with self._conn() as conn:
            conn.execute("UPDATE creditos SET proximo_pago=? WHERE id=?",
                        (new_date, credito_id))
            conn.commit()

    # ── GESTIÓN DE USUARIOS ──────────────────────────────────────────────────

    def get_all_users(self):
        """Retorna todos los usuarios (activos e inactivos)."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT id, nombre, usuario, rol, activo FROM usuarios ORDER BY nombre"
            ).fetchall()
        return [{"id": r[0], "nombre": r[1], "usuario": r[2],
                 "rol": r[3], "activo": r[4]} for r in rows]


    # ════════════════════════════════════════════════════════
    #  ARQUEOS DE CAJA
    # ════════════════════════════════════════════════════════
    def get_arqueo_abierto(self):
        """Retorna el arqueo actualmente abierto, o None."""
        conn = self._conn()
        row = conn.execute(
            "SELECT * FROM arqueos WHERE estado='abierto' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def abrir_arqueo(self, monto_inicial, usuario_nombre=''):
        """Abre un nuevo arqueo de caja."""
        from datetime import datetime
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO arqueos (fecha_apertura,monto_inicial,usuario_nombre,estado) VALUES (?,?,?,?)",
                (fecha, monto_inicial, usuario_nombre, 'abierto'))
        return self.get_arqueo_abierto()

    def cerrar_arqueo(self, arqueo_id, monto_final, notas=''):
        """Cierra el arqueo calculando totales de ventas del período."""
        from datetime import datetime
        conn0 = self._conn()
        arq = conn0.execute("SELECT * FROM arqueos WHERE id=?", (arqueo_id,)).fetchone()
        conn0.close()
        if not arq:
            return None
        arq = dict(arq)
        fecha_cierre = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fecha_desde  = arq['fecha_apertura']
        conn = self._conn()
        def _sum(metodo):
            r = conn.execute(
                "SELECT COALESCE(SUM(total),0) FROM ventas WHERE fecha BETWEEN ? AND ? AND metodo_pago=?",
                (fecha_desde, fecha_cierre, metodo)).fetchone()
            return r[0] if r else 0
        total_ef  = _sum('Efectivo')
        total_tc  = _sum('Tarjeta Crédito') + _sum('Tarjeta Débito')
        total_tr  = _sum('Transferencia')
        r_cred = conn.execute(
            "SELECT COALESCE(SUM(cuota_inicial),0) FROM creditos WHERE fecha BETWEEN ? AND ?",
            (fecha_desde, fecha_cierre)).fetchone()
        total_cred = r_cred[0] if r_cred else 0
        r_count = conn.execute(
            "SELECT COUNT(*) FROM ventas WHERE fecha BETWEEN ? AND ?",
            (fecha_desde, fecha_cierre)).fetchone()
        total_ventas = r_count[0] if r_count else 0
        conn.close()
        diferencia = monto_final - (arq['monto_inicial'] + total_ef)
        with self._conn() as conn:
            conn.execute(
                """UPDATE arqueos SET fecha_cierre=?, monto_final=?, total_efectivo=?,
                   total_tarjeta=?, total_transfer=?, total_creditos=?, total_ventas=?,
                   diferencia=?, notas=?, estado='cerrado' WHERE id=?""",
                (fecha_cierre, monto_final, total_ef, total_tc,
                 total_tr, total_cred, total_ventas, diferencia, notas, arqueo_id))
        return self.get_arqueo_by_id(arqueo_id)

    def get_arqueo_by_id(self, arqueo_id):
        """Retorna un arqueo por ID."""
        conn = self._conn()
        row = conn.execute("SELECT * FROM arqueos WHERE id=?", (arqueo_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def get_arqueos(self, limit=30):
        """Historial de arqueos."""
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM arqueos ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_user_by_id(self, uid):
        """Retorna un usuario por su ID."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, nombre, usuario, rol, activo FROM usuarios WHERE id=?", (uid,)
            ).fetchone()
        if row:
            return {"id": row[0], "nombre": row[1], "usuario": row[2],
                    "rol": row[3], "activo": row[4]}
        return None

    def add_user(self, nombre, usuario, password_hash, rol):
        """Crea un nuevo usuario. Retorna el ID generado."""
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO usuarios (nombre, usuario, password, rol, activo) VALUES (?,?,?,?,1)",
                (nombre, usuario, password_hash, rol)
            )
            conn.commit()
            return cur.lastrowid

    def update_user(self, uid, nombre, usuario, password_hash, rol):
        """Actualiza datos de un usuario existente."""
        with self._conn() as conn:
            if password_hash:
                conn.execute(
                    "UPDATE usuarios SET nombre=?, usuario=?, password=?, rol=? WHERE id=?",
                    (nombre, usuario, password_hash, rol, uid)
                )
            else:
                conn.execute(
                    "UPDATE usuarios SET nombre=?, usuario=?, rol=? WHERE id=?",
                    (nombre, usuario, rol, uid)
                )
            conn.commit()

    def toggle_user_active(self, uid):
        """Activa o desactiva un usuario (no permite desactivar al admin principal)."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT usuario, activo FROM usuarios WHERE id=?", (uid,)
            ).fetchone()
            if not row:
                return
            if row[0] == 'admin':
                raise ValueError("No se puede desactivar el usuario admin principal.")
            new_state = 0 if row[1] else 1
            conn.execute("UPDATE usuarios SET activo=? WHERE id=?", (new_state, uid))
            conn.commit()
        return new_state

    def delete_user(self, uid):
        """Elimina un usuario. No permite eliminar al admin principal."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT usuario FROM usuarios WHERE id=?", (uid,)
            ).fetchone()
            if not row:
                raise ValueError("Usuario no encontrado.")
            if row[0].lower() == 'admin':
                raise ValueError("No se puede eliminar el usuario admin principal.")
            conn.execute("DELETE FROM usuarios WHERE id=?", (uid,))
            conn.commit()
