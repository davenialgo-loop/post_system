"""
Funciones de formateo para el sistema POS
"""

from datetime import datetime

def format_currency(amount, currency_symbol='₲'):
    """
    Formatea un número como moneda
    Para guaraníes: ₲1.234.567 (sin decimales)
    """
    try:
        # Guaraníes no usan decimales
        return f"{currency_symbol}{int(amount):,}".replace(',', '.')
    except:
        return f"{currency_symbol}0"

def format_date(date_str):
    """
    Formatea una fecha de SQLite a formato legible
    Ejemplo: 2024-12-19 14:30:00 -> 19/12/2024 14:30
    """
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%d/%m/%Y %H:%M')
    except:
        return date_str

def format_date_short(date_str):
    """
    Formatea fecha sin hora
    Ejemplo: 2024-12-19 -> 19/12/2024
    """
    try:
        if ' ' in date_str:
            date_str = date_str.split(' ')[0]
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y')
    except:
        return date_str

def truncate_text(text, max_length=30):
    """
    Trunca texto largo con puntos suspensivos
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + '...'

def generate_ticket(sale_data, business_name="Mi Negocio"):
    """
    Genera un ticket de venta en formato texto
    sale_data debe contener: id, date, items[], total, payment_method, amount_paid, change
    """
    ticket = []
    ticket.append("=" * 40)
    ticket.append(business_name.center(40))
    ticket.append("=" * 40)
    ticket.append(f"Ticket #: {sale_data['id']}")
    ticket.append(f"Fecha: {format_date(sale_data['date'])}")
    ticket.append("-" * 40)
    ticket.append(f"{'Producto':<20} {'Cant':>5} {'P.Unit':>6} {'Total':>7}")
    ticket.append("-" * 40)
    
    for item in sale_data['items']:
        name = truncate_text(item['name'], 20)
        ticket.append(f"{name:<20} {item['quantity']:>5} "
                     f"{format_currency(item['unit_price']):>6} "
                     f"{format_currency(item['subtotal']):>7}")
    
    ticket.append("-" * 40)
    ticket.append(f"{'TOTAL:':<30} {format_currency(sale_data['total']):>9}")
    ticket.append("")
    ticket.append(f"Método de pago: {sale_data['payment_method']}")
    ticket.append(f"Pagó: {format_currency(sale_data['amount_paid'])}")
    ticket.append(f"Cambio: {format_currency(sale_data['change'])}")
    ticket.append("=" * 40)
    ticket.append("¡Gracias por su compra!".center(40))
    ticket.append("=" * 40)
    
    return '\n'.join(ticket)