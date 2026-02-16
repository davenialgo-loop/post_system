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
            
            # Índices para mejorar rendimiento
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sale_date ON sales(sale_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_name ON products(name)')
            
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
    
    def create_sale(self, customer_id, total, payment_method, amount_paid, change_amount, cart_items):
        """
        Crea una venta completa con sus detalles
        cart_items: lista de diccionarios con {product_id, quantity, unit_price, subtotal}
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Insertar venta
            cursor.execute('''
                INSERT INTO sales (customer_id, total, payment_method, amount_paid, change_amount)
                VALUES (?, ?, ?, ?, ?)
            ''', (customer_id, total, payment_method, amount_paid, change_amount))
            
            sale_id = cursor.lastrowid
            
            # Insertar detalles de venta y actualizar stock
            for item in cart_items:
                cursor.execute('''
                    INSERT INTO sale_details (sale_id, product_id, quantity, unit_price, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                ''', (sale_id, item['product_id'], item['quantity'], 
                      item['unit_price'], item['subtotal']))
                
                # Reducir stock
                cursor.execute('''
                    UPDATE products SET stock = stock - ? WHERE id = ?
                ''', (item['quantity'], item['product_id']))
            
            conn.commit()
            return sale_id
    
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