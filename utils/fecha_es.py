"""
fecha_es.py — Utilidades de formato de fecha en español.
Sin dependencia de locale del sistema operativo.
"""

from datetime import datetime

DIAS = {
    0: "lunes", 1: "martes", 2: "miércoles",
    3: "jueves", 4: "viernes", 5: "sábado", 6: "domingo",
}
DIAS_CORTO = {
    0: "lun", 1: "mar", 2: "mié",
    3: "jue", 4: "vie", 5: "sáb", 6: "dom",
}
MESES = {
    1: "enero",      2: "febrero",   3: "marzo",
    4: "abril",      5: "mayo",      6: "junio",
    7: "julio",      8: "agosto",    9: "septiembre",
    10: "octubre",  11: "noviembre", 12: "diciembre",
}
MESES_CORTO = {
    1: "ene",  2: "feb",  3: "mar",
    4: "abr",  5: "may",  6: "jun",
    7: "jul",  8: "ago",  9: "sep",
    10: "oct", 11: "nov", 12: "dic",
}


def fecha_corta(dt: datetime = None) -> str:
    """Ej: 'lun 23 feb  15:11:44'"""
    if dt is None:
        dt = datetime.now()
    return (f"{DIAS_CORTO[dt.weekday()].capitalize()} "
            f"{dt.day:02d} {MESES_CORTO[dt.month]}  "
            f"{dt.strftime('%H:%M:%S')}")


def fecha_larga(dt: datetime = None) -> str:
    """Ej: 'Lunes, 23 de febrero de 2026'"""
    if dt is None:
        dt = datetime.now()
    return (f"{DIAS[dt.weekday()].capitalize()}, "
            f"{dt.day} de {MESES[dt.month]} de {dt.year}")


def fecha_hora_ticket(dt: datetime = None) -> str:
    """Ej: '23/02/2026 15:11:44'"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime('%d/%m/%Y %H:%M:%S')


def fecha_iso(dt: datetime = None) -> str:
    """Ej: '2026-02-23' — para guardar en BD"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime('%Y-%m-%d')


def fecha_display(fecha_str: str) -> str:
    """Convierte '2026-02-23' → '23/02/2026'"""
    try:
        dt = datetime.strptime(fecha_str, '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y')
    except Exception:
        return fecha_str or ''


# Alias para compatibilidad con credit_ui
format_date = fecha_display
