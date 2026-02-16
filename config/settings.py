"""
Configuración global del sistema POS
Define colores, fuentes, tamaños y rutas
"""

# ============= PALETA DE COLORES MODERNA =============
# Inspirada en diseños minimalistas tipo Stripe, Notion

COLORS = {
    # Colores principales
    'primary': '#2563eb',        # Azul profesional
    'primary_hover': '#1d4ed8',  # Azul hover
    'secondary': '#64748b',      # Gris azulado
    
    # Fondos
    'bg_main': '#f8fafc',        # Fondo principal (casi blanco)
    'bg_card': '#ffffff',        # Fondo de tarjetas
    'bg_sidebar': '#1e293b',     # Sidebar oscuro
    
    # Textos
    'text_primary': '#0f172a',   # Texto principal (casi negro)
    'text_secondary': '#64748b', # Texto secundario
    'text_white': '#ffffff',     # Texto blanco
    
    # Estados
    'success': '#10b981',        # Verde éxito
    'warning': '#f59e0b',        # Naranja advertencia
    'danger': '#ef4444',         # Rojo error
    'info': '#3b82f6',           # Azul información
    
    # Bordes
    'border': '#e2e8f0',         # Borde sutil
    'border_focus': '#2563eb',   # Borde al enfocar
}

# ============= TIPOGRAFÍA =============
FONTS = {
    'family': 'Segoe UI',        # Fuente por defecto de Windows
    'family_alt': 'Arial',       # Alternativa
    
    # Tamaños
    'title': 24,                 # Títulos principales
    'subtitle': 18,              # Subtítulos
    'heading': 16,               # Encabezados
    'body': 11,                  # Texto normal
    'small': 9,                  # Texto pequeño
    
    # Pesos (simulados con configuraciones)
    'bold': 'bold',
    'normal': 'normal',
}

# ============= ESPACIADO =============
SPACING = {
    'xs': 4,    # Extra pequeño
    'sm': 8,    # Pequeño
    'md': 16,   # Mediano
    'lg': 24,   # Grande
    'xl': 32,   # Extra grande
}

# ============= DIMENSIONES DE VENTANAS =============
WINDOW = {
    'main_width': 1200,
    'main_height': 700,
    'min_width': 1000,
    'min_height': 600,
}

# ============= ESTILOS DE BOTONES =============
BUTTON_STYLES = {
    'primary': {
        'bg': COLORS['primary'],
        'fg': COLORS['text_white'],
        'activebackground': COLORS['primary_hover'],
        'activeforeground': COLORS['text_white'],
        'disabledforeground': COLORS['text_white'],
        'font': (FONTS['family'], FONTS['body'], FONTS['bold']),
        'relief': 'flat',
        'cursor': 'hand2',
        'padx': SPACING['md'],
        'pady': SPACING['sm'],
    },
    'secondary': {
        'bg': COLORS['secondary'],
        'fg': COLORS['text_white'],
        'activebackground': '#475569',
        'activeforeground': COLORS['text_white'],
        'disabledforeground': COLORS['text_white'],
        'font': (FONTS['family'], FONTS['body']),
        'relief': 'flat',
        'cursor': 'hand2',
        'padx': SPACING['md'],
        'pady': SPACING['sm'],
    },
    'success': {
        'bg': COLORS['success'],
        'fg': COLORS['text_white'],
        'activebackground': '#059669',
        'activeforeground': COLORS['text_white'],
        'disabledforeground': COLORS['text_white'],
        'font': (FONTS['family'], FONTS['body'], FONTS['bold']),
        'relief': 'flat',
        'cursor': 'hand2',
        'padx': SPACING['md'],
        'pady': SPACING['sm'],
    },
    'danger': {
        'bg': COLORS['danger'],
        'fg': COLORS['text_white'],
        'activebackground': '#dc2626',
        'activeforeground': COLORS['text_white'],
        'disabledforeground': COLORS['text_white'],
        'font': (FONTS['family'], FONTS['body']),
        'relief': 'flat',
        'cursor': 'hand2',
        'padx': SPACING['md'],
        'pady': SPACING['sm'],
    },
}

# ============= ESTILOS DE ENTRADAS =============
ENTRY_STYLE = {
    'font': (FONTS['family'], FONTS['body']),
    'relief': 'solid',
    'borderwidth': 1,
    'highlightthickness': 2,
    'highlightcolor': COLORS['border_focus'],
    'highlightbackground': COLORS['border'],
}

# ============= RUTAS =============
PATHS = {
    'database': 'data/pos.db',
    'reports': 'reports/',
    'backups': 'backups/',
}

# ============= CONFIGURACIÓN DE NEGOCIO =============
BUSINESS = {
    'name': 'Venialgo Sistemas',
    'currency': '₲',
    'tax_rate': 0.10,  # 10% impuesto
    'decimal_places': 2,
}