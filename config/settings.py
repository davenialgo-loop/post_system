"""
Configuración global del sistema POS
Define colores, fuentes, tamaños y rutas
"""

# ============= PALETA DE COLORES MODERNA =============
COLORS = {
    'primary': '#2563eb',
    'primary_hover': '#1d4ed8',
    'secondary': '#64748b',
    'bg_main': '#f8fafc',
    'bg_card': '#ffffff',
    'bg_sidebar': '#1e293b',
    'text_primary': '#0f172a',
    'text_secondary': '#64748b',
    'text_white': '#ffffff',
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'info': '#3b82f6',
    'border': '#e2e8f0',
    'border_focus': '#2563eb',
}

# ============= TIPOGRAFÍA =============
FONTS = {
    'family': 'Segoe UI',
    'family_alt': 'Arial',
    'title': 24,
    'subtitle': 18,
    'heading': 16,
    'body': 11,
    'small': 9,
    'bold': 'bold',
    'normal': 'normal',
}

# ============= ESPACIADO =============
SPACING = {
    'xs': 4,
    'sm': 8,
    'md': 16,
    'lg': 24,
    'xl': 32,
}

# ============= DIMENSIONES DE VENTANAS =============
WINDOW = {
    'main_width': 1100,
    'main_height': 650,
    'min_width': 900,
    'min_height': 550,
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
    'currency_name': 'Guaraníes',
    'tax_rate': 0.10,
    'decimal_places': 0,
}

# ============= CONFIGURACIÓN DE CRÉDITOS =============
CREDIT = {
    'payment_frequencies': {
        'weekly': {'name': 'Semanal', 'days': 7},
        'biweekly': {'name': 'Quincenal', 'days': 15},
        'monthly': {'name': 'Mensual', 'days': 30},
    },
    'min_down_payment_percent': 10,
    'max_installments': 24,
}