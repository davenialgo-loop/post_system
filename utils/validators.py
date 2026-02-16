"""
Funciones de validación para el sistema POS
"""

def validate_positive_number(value, field_name="Valor"):
    """
    Valida que un valor sea un número positivo
    Retorna (is_valid, message, parsed_value)
    """
    try:
        num = float(value)
        if num <= 0:
            return False, f"{field_name} debe ser mayor a 0", None
        return True, "", num
    except ValueError:
        return False, f"{field_name} debe ser un número válido", None

def validate_positive_integer(value, field_name="Valor"):
    """
    Valida que un valor sea un entero positivo
    """
    try:
        num = int(value)
        if num < 0:
            return False, f"{field_name} no puede ser negativo", None
        return True, "", num
    except ValueError:
        return False, f"{field_name} debe ser un número entero", None

def validate_required_field(value, field_name="Campo"):
    """Valida que un campo no esté vacío"""
    if not value or str(value).strip() == "":
        return False, f"{field_name} es requerido", None
    return True, "", str(value).strip()

def validate_stock_availability(requested, available, product_name):
    """Valida que haya suficiente stock"""
    if requested > available:
        return False, f"Stock insuficiente de {product_name}. Disponible: {available}", None
    return True, "", requested

def validate_phone(phone):
    """Valida formato básico de teléfono (opcional)"""
    if not phone:
        return True, "", phone
    
    # Remover caracteres comunes
    clean_phone = ''.join(filter(str.isdigit, phone))
    
    if len(clean_phone) < 6:
        return False, "Teléfono debe tener al menos 6 dígitos", None
    
    return True, "", phone

def validate_email(email):
    """Valida formato básico de email (opcional)"""
    if not email:
        return True, "", email
    
    if '@' not in email or '.' not in email:
        return False, "Email inválido", None
    
    return True, "", email