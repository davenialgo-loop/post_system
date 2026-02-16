"""
Script para agregar datos de prueba al sistema POS
Ejecuta este archivo DESPUÉS de crear la estructura de carpetas
"""

from database.db_manager import DatabaseManager

def add_sample_data():
    """Agrega productos y clientes de ejemplo"""
    db = DatabaseManager()
    
    print("Agregando productos de ejemplo...")
    
    # Productos de ejemplo
    products = [
        ("Laptop HP", 850.00, 15, "Electrónica", "LP001"),
        ("Mouse Logitech", 25.00, 50, "Accesorios", "MS001"),
        ("Teclado Mecánico", 75.00, 30, "Accesorios", "KB001"),
        ("Monitor Samsung 24\"", 200.00, 20, "Electrónica", "MN001"),
        ("Audífonos Bluetooth", 45.00, 40, "Audio", "AU001"),
        ("Webcam HD", 60.00, 25, "Accesorios", "WC001"),
        ("SSD 500GB", 80.00, 35, "Almacenamiento", "SS001"),
        ("RAM 8GB DDR4", 50.00, 45, "Componentes", "RM001"),
        ("Cable HDMI 2m", 12.00, 100, "Cables", "CB001"),
        ("Hub USB 4 puertos", 18.00, 60, "Accesorios", "HB001"),
    ]
    
    for name, price, stock, category, barcode in products:
        db.add_product(name, price, stock, category, barcode)
        print(f"✓ Agregado: {name}")
    
    print("\nAgregando clientes de ejemplo...")
    
    # Clientes de ejemplo
    customers = [
        ("Juan Pérez", "555-0101", "juan@email.com", "Calle Principal 123"),
        ("María González", "555-0102", "maria@email.com", "Av. Central 456"),
        ("Carlos Rodríguez", "555-0103", "carlos@email.com", "Barrio Norte 789"),
        ("Ana Martínez", "555-0104", "ana@email.com", "Zona Sur 321"),
    ]
    
    for name, phone, email, address in customers:
        db.add_customer(name, phone, email, address)
        print(f"✓ Agregado: {name}")
    
    print("\n✅ Datos de prueba agregados exitosamente!")
    print("Ahora puedes ejecutar: python main.py")

if __name__ == "__main__":
    add_sample_data()