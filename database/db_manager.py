"""
Gestor de Base de Datos SQLite
Maneja conexiones, creación de tablas y operaciones CRUD
"""

import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path='data/pos.db'):
        """Inicializa el gestor de base de datos"""
        self.db_path = db_path
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Inicializar tablas
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """
        Context manager para manejar conexiones de forma segura
        Uso: with db.get_connection() as conn:
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permite acceder a columnas por nombre
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        """Crea todas las tablas necesarias"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabla de productos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    stock INTEGER DEFAULT 0,
                    category TEXT,
                    barcode TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de clientes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    email TEXT,
                    address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de ventas (encabezado)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER,
                    total REAL NOT NULL,
                    payment_method TEXT NOT NULL,
                    amount_paid REAL,
                    change_amount REAL,
                    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_credit BOOLEAN DEFAULT 0,
                    FOREIGN KEY (customer_id) REFERENCES customers (id)
                )
            ''')
            
            # Tabla de detalles de venta
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sale_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    subtotal REAL NOT NULL,
                    FOREIGN KEY (sale_id) REFERENCES sales (id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')
            
            # Tabla de ventas a crédito
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS credit_sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL UNIQUE,
                    customer_id INTEGER NOT NULL,
                    total_amount REAL NOT NULL,
                    down_payment REAL DEFAULT 0,
                    remaining_balance REAL NOT NULL,
                    payment_frequency TEXT NOT NULL,
                    installment_amount REAL NOT NULL,
                    total_installments INTEGER NOT NULL,
                    paid_installments INTEGER DEFAULT 0,
                    next_payment_date DATE,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sale_id) REFERENCES sales (id) ON DELETE CASCADE,
                    FOREIGN KEY (customer_id) REFERENCES customers (id)
                )
            ''')
            
            # Tabla de pagos realizados
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS credit_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    credit_sale_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (credit_sale_id) REFERENCES credit_sales (id) ON DELETE CASCADE
                )
            ''')
            
            # Índices para mejorar rendimiento
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sale_date ON sales(sale_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_name ON products(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_credit_status ON credit_sales(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_next_payment ON credit_sales(next_payment_date)')
            
            conn.commit()
    
    def execute_query(self, query, params=None):
        """
        Ejecuta una consulta y retorna los resultados
        Útil para SELECT
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def execute_update(self, query, params=None):
        """
        Ejecuta una consulta de modificación (INSERT, UPDATE, DELETE)
        Retorna el ID del último registro insertado
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.lastrowid
    
    # ============= MÉTODOS CRUD PARA PRODUCTOS =============
    
    def add_product(self, name, price, stock=0, category='', barcode=''):
        """Agrega un nuevo producto"""
        query = '''
            INSERT INTO products (name, price, stock, category, barcode)
            VALUES (?, ?, ?, ?, ?)
        '''
        return self.execute_update(query, (name, price, stock, category, barcode))
    
    def get_all_products(self):
        """Obtiene todos los productos"""
        query = 'SELECT * FROM products ORDER BY name'
        return self.execute_query(query)
    
    def get_product_by_id(self, product_id):
        """Obtiene un producto por ID"""
        query = 'SELECT * FROM products WHERE id = ?'
        result = self.execute_query(query, (product_id,))
        return result[0] if result else None
    
    def search_products(self, search_term):
        """Busca productos por nombre o código de barras"""
        query = '''
            SELECT * FROM products 
            WHERE name LIKE ? OR barcode LIKE ?
            ORDER BY name
        '''
        term = f'%{search_term}%'
        return self.execute_query(query, (term, term))
    
    def update_product(self, product_id, name, price, stock, category, barcode):
        """Actualiza un producto existente"""
        query = '''
            UPDATE products 
            SET name=?, price=?, stock=?, category=?, barcode=?
            WHERE id=?
        '''
        self.execute_update(query, (name, price, stock, category, barcode, product_id))
    
    def delete_product(self, product_id):
        """Elimina un producto"""
        query = 'DELETE FROM products WHERE id = ?'
        self.execute_update(query, (product_id,))
    
    def update_stock(self, product_id, quantity_change):
        """Actualiza el stock de un producto (suma o resta)"""
        query = '''
            UPDATE products 
            SET stock = stock + ?
            WHERE id = ?
        '''
        self.execute_update(query, (quantity_change, product_id))
    
    # ============= MÉTODOS CRUD PARA CLIENTES =============
    
    def add_customer(self, name, phone='', email='', address=''):
        """Agrega un nuevo cliente"""
        query = '''
            INSERT INTO customers (name, phone, email, address)
            VALUES (?, ?, ?, ?)
        '''
        return self.execute_update(query, (name, phone, email, address))
    
    def get_all_customers(self):
        """Obtiene todos los clientes"""
        query = 'SELECT * FROM customers ORDER BY name'
        return self.execute_query(query)
    
    def search_customers(self, search_term):
        """Busca clientes por nombre o teléfono"""
        query = '''
            SELECT * FROM customers 
            WHERE name LIKE ? OR phone LIKE ?
            ORDER BY name
        '''
        term = f'%{search_term}%'
        return self.execute_query(query, (term, term))
    
    # ============= MÉTODOS PARA VENTAS =============
    
    def create_sale(self, customer_id, total, payment_method, amount_paid, change_amount, cart_items, is_credit=False):
        """
        Crea una venta completa con sus detalles
        cart_items: lista de diccionarios con {product_id, quantity, unit_price, subtotal}
        is_credit: indica si es venta a crédito
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Insertar venta
            cursor.execute('''
                INSERT INTO sales (customer_id, total, payment_method, amount_paid, change_amount, is_credit)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (customer_id, total, payment_method, amount_paid, change_amount, is_credit))
            
            sale_id = cursor.lastrowid
            
            # Insertar detalles de venta y actualizar stock
            for item in cart_items:
                cursor.execute('''
                    INSERT INTO sale_details (sale_id, product_id, quantity, unit_price, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                ''', (sale_id, item['product_id'], item['quantity'], 
                      item['unit_price'], item['subtotal']))
                
                # Reducir stock solo si no es crédito o si ya pagó
                if not is_credit or amount_paid > 0:
                    cursor.execute('''
                        UPDATE products SET stock = stock - ? WHERE id = ?
                    ''', (item['quantity'], item['product_id']))
            
            conn.commit()
            return sale_id
    
    # ============= MÉTODOS PARA CRÉDITOS =============
    
    def create_credit_sale(self, sale_id, customer_id, total_amount, down_payment, 
                          payment_frequency, installment_amount, total_installments, next_payment_date):
        """Crea una venta a crédito"""
        remaining_balance = total_amount - down_payment
        query = '''
            INSERT INTO credit_sales 
            (sale_id, customer_id, total_amount, down_payment, remaining_balance,
             payment_frequency, installment_amount, total_installments, next_payment_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        return self.execute_update(query, (
            sale_id, customer_id, total_amount, down_payment, remaining_balance,
            payment_frequency, installment_amount, total_installments, next_payment_date
        ))
    
    def get_all_credit_sales(self, status=None):
        """Obtiene todas las ventas a crédito, opcionalmente filtradas por estado"""
        if status:
            query = '''
                SELECT cs.*, c.name as customer_name, c.phone
                FROM credit_sales cs
                JOIN customers c ON cs.customer_id = c.id
                WHERE cs.status = ?
                ORDER BY cs.next_payment_date ASC
            '''
            return self.execute_query(query, (status,))
        else:
            query = '''
                SELECT cs.*, c.name as customer_name, c.phone
                FROM credit_sales cs
                JOIN customers c ON cs.customer_id = c.id
                ORDER BY cs.next_payment_date ASC
            '''
            return self.execute_query(query)
    
    def get_credit_sale_by_id(self, credit_sale_id):
        """Obtiene una venta a crédito específica"""
        query = '''
            SELECT cs.*, c.name as customer_name, c.phone, c.address
            FROM credit_sales cs
            JOIN customers c ON cs.customer_id = c.id
            WHERE cs.id = ?
        '''
        result = self.execute_query(query, (credit_sale_id,))
        return result[0] if result else None
    
    def add_credit_payment(self, credit_sale_id, amount, notes=''):
        """Registra un pago a una venta a crédito"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Insertar pago
            cursor.execute('''
                INSERT INTO credit_payments (credit_sale_id, amount, notes)
                VALUES (?, ?, ?)
            ''', (credit_sale_id, amount, notes))
            
            # Obtener datos del crédito
            cursor.execute('SELECT * FROM credit_sales WHERE id = ?', (credit_sale_id,))
            credit = cursor.fetchone()
            
            if credit:
                new_balance = credit['remaining_balance'] - amount
                paid_installments = credit['paid_installments'] + 1
                
                # Calcular siguiente fecha de pago
                from datetime import datetime, timedelta
                current_next = datetime.strptime(credit['next_payment_date'], '%Y-%m-%d')
                
                # Días según frecuencia
                freq_days = {
                    'weekly': 7,
                    'biweekly': 15,
                    'monthly': 30
                }
                days_to_add = freq_days.get(credit['payment_frequency'], 30)
                next_date = current_next + timedelta(days=days_to_add)
                
                # Determinar estado
                status = 'paid' if new_balance <= 0 else 'active'
                
                # Actualizar crédito
                cursor.execute('''
                    UPDATE credit_sales 
                    SET remaining_balance = ?,
                        paid_installments = ?,
                        next_payment_date = ?,
                        status = ?
                    WHERE id = ?
                ''', (new_balance, paid_installments, next_date.strftime('%Y-%m-%d'), 
                      status, credit_sale_id))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_credit_payments(self, credit_sale_id):
        """Obtiene todos los pagos de un crédito"""
        query = '''
            SELECT * FROM credit_payments 
            WHERE credit_sale_id = ?
            ORDER BY payment_date DESC
        '''
        return self.execute_query(query, (credit_sale_id,))
    
    def update_next_payment_date(self, credit_sale_id, new_date):
        """Actualiza la fecha del próximo pago"""
        query = 'UPDATE credit_sales SET next_payment_date = ? WHERE id = ?'
        self.execute_update(query, (new_date, credit_sale_id))
    
    def get_overdue_credits(self):
        """Obtiene créditos vencidos"""
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        query = '''
            SELECT cs.*, c.name as customer_name, c.phone
            FROM credit_sales cs
            JOIN customers c ON cs.customer_id = c.id
            WHERE cs.status = 'active' 
            AND cs.next_payment_date < ?
            ORDER BY cs.next_payment_date ASC
        '''
        return self.execute_query(query, (today,))
    
    def get_sales_by_date(self, start_date, end_date):
        """Obtiene ventas en un rango de fechas"""
        query = '''
            SELECT s.*, c.name as customer_name
            FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.id
            WHERE DATE(s.sale_date) BETWEEN DATE(?) AND DATE(?)
            ORDER BY s.sale_date DESC
        '''
        return self.execute_query(query, (start_date, end_date))
    
    def get_sale_details(self, sale_id):
        """Obtiene los detalles de una venta específica"""
        query = '''
            SELECT sd.*, p.name as product_name
            FROM sale_details sd
            JOIN products p ON sd.product_id = p.id
            WHERE sd.sale_id = ?
        '''
        return self.execute_query(query, (sale_id,))
    
    def get_sales_summary(self, start_date, end_date):
        """Obtiene resumen de ventas en un período"""
        query = '''
            SELECT 
                COUNT(*) as total_sales,
                SUM(total) as total_revenue,
                AVG(total) as average_sale
            FROM sales
            WHERE DATE(sale_date) BETWEEN DATE(?) AND DATE(?)
        '''
        result = self.execute_query(query, (start_date, end_date))
        return result[0] if result else None