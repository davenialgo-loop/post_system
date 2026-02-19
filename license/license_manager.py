"""
Sistema de Licencias — Venialgo Sistemas
Gestión de claves, activaciones y hardware fingerprint
"""

import hashlib
import hmac
import json
import os
import platform
import re
import sqlite3
import struct
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# ── Clave maestra del desarrollador (CAMBIAR EN PRODUCCIÓN) ──────────────
# Esta clave NUNCA se distribuye al cliente. Úsala solo en tu keygen_tool.
_MASTER_SECRET = b"VenialgoPOS2024#SecretMaster$Key!XYZ987"

# ── Archivos de licencia en AppData (siempre escribible) ─────────────────
def _get_app_dir():
    import sys
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.path.expanduser("~")
    d = os.path.join(base, "VenialgoPOS")
    os.makedirs(d, exist_ok=True)
    return d

_APP_DIR        = _get_app_dir()
LICENSE_FILE    = os.path.join(_APP_DIR, "license.dat")
ACTIVATION_FILE = os.path.join(_APP_DIR, "activation.dat")
MAX_ACTIVATIONS = 2          # maximo de PCs por licencia
import os as _os, sys as _sys
def _get_db_file():
    if _sys.platform == "win32":
        base = _os.environ.get("APPDATA", _os.path.expanduser("~"))
    else:
        base = _os.path.expanduser("~")
    d = _os.path.join(base, "VenialgoPOS")
    _os.makedirs(d, exist_ok=True)
    return _os.path.join(d, "pos_database.db")
DB_FILE = _get_db_file()

# ════════════════════════════════════════════════════════════════════════════
#  HARDWARE FINGERPRINT
# ════════════════════════════════════════════════════════════════════════════
def get_hardware_id() -> str:
    """
    Genera un ID único del hardware combinando:
    - MAC address principal
    - Nombre del equipo
    - Plataforma / arquitectura
    Retorna un hash SHA256 de 16 chars (suficiente para comparación).
    """
    parts = []

    # MAC address
    try:
        mac = uuid.getnode()
        parts.append(str(mac))
    except Exception:
        parts.append("00:00:00:00:00:00")

    # Hostname
    try:
        parts.append(platform.node())
    except Exception:
        parts.append("unknown")

    # Plataforma
    parts.append(platform.system())
    parts.append(platform.machine())

    # En Windows, intentar disco serial
    if platform.system() == "Windows":
        try:
            import subprocess
            r = subprocess.check_output(
                "wmic diskdrive get SerialNumber",
                shell=True, stderr=subprocess.DEVNULL
            ).decode(errors='ignore')
            serial = r.strip().split('\n')[-1].strip()
            if serial:
                parts.append(serial)
        except Exception:
            pass

    raw = "|".join(parts).encode('utf-8')
    full_hash = hashlib.sha256(raw).hexdigest()
    return full_hash[:16].upper()       # ID corto legible


# ════════════════════════════════════════════════════════════════════════════
#  GENERACIÓN DE CLAVES  (usar solo en keygen_tool.py)
# ════════════════════════════════════════════════════════════════════════════
def generate_license_key(client_id: str,
                         product: str = "POS",
                         days: int = 365,
                         max_act: int = MAX_ACTIVATIONS,
                         secret: bytes = _MASTER_SECRET) -> str:
    """
    Genera una clave de licencia en formato XXXX-XXXX-XXXX-XXXX-XXXX.
    Algoritmo: HMAC-SHA256 + struct binario + base32
    """
    import base64
    expiry   = int((datetime.now() + timedelta(days=days)).timestamp())
    cid_hash = hashlib.sha256(client_id.upper().encode()).digest()[:4]
    payload  = struct.pack(">IB", expiry, max_act) + cid_hash   # 9 bytes
    sig      = hmac.new(secret, payload, hashlib.sha256).digest()[:8]
    raw      = payload + sig   # 17 bytes
    encoded  = base64.b32encode(raw).decode().rstrip("=")
    groups   = [encoded[i:i+4] for i in range(0, len(encoded), 4)]
    return "-".join(groups)


def _decode_key(key: str, secret: bytes = _MASTER_SECRET):
    """
    Decodifica y verifica una clave.
    Retorna dict o None si invalida.
    """
    import base64
    try:
        clean   = key.replace("-", "").upper()
        padding = (8 - len(clean) % 8) % 8
        raw     = base64.b32decode(clean + "=" * padding)
        if len(raw) < 17:
            return None
        payload, sig_recv = raw[:9], raw[9:17]
        sig_calc = hmac.new(secret, payload, hashlib.sha256).digest()[:8]
        if not hmac.compare_digest(sig_recv, sig_calc):
            return None
        expiry, max_act  = struct.unpack(">IB", payload[:5])
        cid_hash_stored  = payload[5:9].hex().upper()
        return {
            "client_id":   cid_hash_stored,
            "expiry":      expiry,
            "max_act":     max_act,
            "expiry_date": datetime.fromtimestamp(expiry).strftime("%d/%m/%Y"),
            "days_left":   max(0, (expiry - int(time.time())) // 86400),
        }
    except Exception:
        return None


# ════════════════════════════════════════════════════════════════════════════
#  VALIDACIÓN Y ACTIVACIÓN
# ════════════════════════════════════════════════════════════════════════════
class LicenseStatus:
    VALID        = "VALID"
    EXPIRED      = "EXPIRED"
    INVALID_KEY  = "INVALID_KEY"
    NOT_FOUND    = "NOT_FOUND"
    MAX_EXCEEDED = "MAX_EXCEEDED"
    HARDWARE_MISMATCH = "HARDWARE_MISMATCH"


def _load_activation() -> dict:
    if not os.path.exists(ACTIVATION_FILE):
        return {}
    try:
        with open(ACTIVATION_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_activation(data: dict):
    with open(ACTIVATION_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def validate_license(key: str = None) -> tuple[str, dict]:
    """
    Valida la licencia actual.
    Retorna (LicenseStatus, info_dict).
    Si se pasa key, usa esa; si no, carga desde license.dat.
    """
    if key is None:
        if not os.path.exists(LICENSE_FILE):
            return LicenseStatus.NOT_FOUND, {}
        try:
            with open(LICENSE_FILE, 'r') as f:
                key = f.read().strip()
        except Exception:
            return LicenseStatus.NOT_FOUND, {}

    info = _decode_key(key)
    if not info:
        return LicenseStatus.INVALID_KEY, {}

    # Verificar expiración
    if time.time() > info['expiry']:
        return LicenseStatus.EXPIRED, info

    # Verificar hardware
    hwid = get_hardware_id()
    activation = _load_activation()

    if activation.get("hwid") and activation["hwid"] != hwid:
        return LicenseStatus.HARDWARE_MISMATCH, info

    # Verificar máx activaciones (registro en servidor omitido — local)
    info['hwid']         = hwid
    info['expiry_date']  = datetime.fromtimestamp(info['expiry']).strftime("%d/%m/%Y")
    info['days_left']    = max(0, (info['expiry'] - int(time.time())) // 86400)
    return LicenseStatus.VALID, info


def activate_license(key: str) -> tuple[bool, str]:
    """
    Activa una licencia en este equipo.
    Retorna (éxito, mensaje).
    """
    status, info = validate_license(key)

    if status == LicenseStatus.INVALID_KEY:
        return False, "❌ Clave de licencia inválida."
    if status == LicenseStatus.EXPIRED:
        return False, "❌ La licencia ha expirado."
    if status == LicenseStatus.HARDWARE_MISMATCH:
        return False, "❌ Esta licencia ya está activada en otro equipo."
    if status == LicenseStatus.MAX_EXCEEDED:
        return False, "❌ Se superó el límite de activaciones permitidas."

    # Guardar licencia y activación
    with open(LICENSE_FILE, 'w') as f:
        f.write(key.strip())

    hwid = get_hardware_id()
    _save_activation({
        "hwid":       hwid,
        "key":        key.strip(),
        "client_id":  info.get("client_id"),
        "activated":  datetime.now().isoformat(),
        "expiry":     info.get("expiry_date"),
    })

    return True, f"✅ Licencia activada correctamente.\n" \
                 f"Cliente: {info['client_id']}\n" \
                 f"Válida hasta: {info['expiry_date']}\n" \
                 f"Equipo ID: {hwid}"


def get_license_info() -> dict:
    """Retorna información de la licencia activa o dict vacío."""
    status, info = validate_license()
    info['status'] = status
    return info


def is_licensed() -> bool:
    """Retorna True si hay una licencia válida activa."""
    status, _ = validate_license()
    return status == LicenseStatus.VALID
