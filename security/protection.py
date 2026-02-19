"""
Protección Anti-Copia — Venialgo Sistemas
Verificación de integridad, hardware binding y detección de entornos no autorizados
"""

import hashlib
import hmac
import json
import os
import platform
import sys
import time
from datetime import datetime
from pathlib import Path

from license.license_manager import (
    get_hardware_id, validate_license, LicenseStatus
)

# ── Archivos críticos que se verifican ───────────────────
PROTECTED_FILES = [
    "license/license_manager.py",
    "security/protection.py",
    "license.dat",
    "activation.dat",
]

_INTEGRITY_FILE  = ".integrity"
_MASTER_SECRET   = b"VenialgoPOS2024#SecretMaster$Key!XYZ987"
_MAX_CLOCK_SKEW  = 86400 * 5   # 5 días de tolerancia de reloj

# ════════════════════════════════════════════════════════
#  VERIFICACIÓN DE HARDWARE
# ════════════════════════════════════════════════════════

def verify_hardware_match() -> tuple[bool, str]:
    """
    Verifica que el hardware actual coincide con el registrado
    en la activación.
    """
    if not os.path.exists("activation.dat"):
        return False, "No hay activación registrada en este equipo."

    try:
        with open("activation.dat") as f:
            activation = json.load(f)
    except Exception:
        return False, "Archivo de activación corrupto."

    registered_hwid = activation.get("hwid", "")
    current_hwid    = get_hardware_id()

    if registered_hwid != current_hwid:
        return False, (f"Hardware no coincide.\n"
                       f"Registrado: {registered_hwid}\n"
                       f"Actual:     {current_hwid}")

    return True, "Hardware verificado correctamente."


# ════════════════════════════════════════════════════════
#  VERIFICACIÓN DE RELOJ (anti-retroceso de fecha)
# ════════════════════════════════════════════════════════

def _get_last_run_timestamp() -> int:
    if not os.path.exists(_INTEGRITY_FILE):
        return 0
    try:
        with open(_INTEGRITY_FILE) as f:
            data = json.load(f)
        return data.get("last_run", 0)
    except Exception:
        return 0


def _save_run_timestamp():
    ts = int(time.time())
    try:
        existing = {}
        if os.path.exists(_INTEGRITY_FILE):
            with open(_INTEGRITY_FILE) as f:
                existing = json.load(f)
        existing["last_run"] = ts
        with open(_INTEGRITY_FILE, 'w') as f:
            json.dump(existing, f)
    except Exception:
        pass


def verify_system_clock() -> tuple[bool, str]:
    """
    Detecta si el reloj del sistema fue retrocedido (técnica común
    para extender licencias vencidas).
    """
    last_run = _get_last_run_timestamp()
    now      = int(time.time())

    if last_run > 0 and (now < last_run - _MAX_CLOCK_SKEW):
        diff_days = (last_run - now) // 86400
        return False, (f"⚠️ Se detectó que el reloj del sistema fue retrocedido "
                       f"aproximadamente {diff_days} días.\n"
                       f"Esto puede invalidar su licencia.")

    _save_run_timestamp()
    return True, "Reloj del sistema verificado."


# ════════════════════════════════════════════════════════
#  DETECCIÓN DE ENTORNO VIRTUAL / SANDBOX
# ════════════════════════════════════════════════════════

def detect_sandbox() -> tuple[bool, str]:
    """
    Detecta indicadores básicos de máquinas virtuales o sandboxes.
    Retorna (es_sospechoso, mensaje).
    """
    indicators = []

    # Detectar variables de VM conocidas
    vm_env_vars = ['VBOX_MSI_INSTALL_PATH', 'VMWARE_HORIZON_CLIENT_SID']
    for var in vm_env_vars:
        if os.environ.get(var):
            indicators.append(f"Variable de entorno VM detectada: {var}")

    # Detectar hostname sospechoso
    hostname = platform.node().lower()
    suspicious_hosts = ['sandbox', 'vm-', 'virtual', 'test-pc', 'malware']
    for s in suspicious_hosts:
        if s in hostname:
            indicators.append(f"Hostname sospechoso: {hostname}")
            break

    if indicators:
        return True, " | ".join(indicators)
    return False, "Entorno limpio."


# ════════════════════════════════════════════════════════
#  VERIFICACIÓN COMPLETA DE PROTECCIÓN
# ════════════════════════════════════════════════════════

class ProtectionResult:
    def __init__(self):
        self.passed      = True
        self.checks      = []
        self.fatal_error = None

    def add(self, name: str, ok: bool, msg: str, fatal: bool = False):
        self.checks.append({"name": name, "ok": ok, "msg": msg, "fatal": fatal})
        if not ok and fatal:
            self.passed = False
            self.fatal_error = msg

    def summary(self) -> str:
        lines = []
        for c in self.checks:
            icon = "✅" if c["ok"] else ("❌" if c["fatal"] else "⚠️")
            lines.append(f"{icon} {c['name']}: {c['msg']}")
        return "\n".join(lines)


def run_protection_checks(strict: bool = True) -> ProtectionResult:
    """
    Ejecuta todas las verificaciones de protección.
    strict=True → falla fatal si cualquier verificación crítica falla.
    """
    result = ProtectionResult()

    # 1. Verificar licencia
    status, info = validate_license()
    if status == LicenseStatus.VALID:
        result.add("Licencia", True,
                   f"Válida — {info.get('days_left', '?')} días restantes")
    elif status == LicenseStatus.EXPIRED:
        result.add("Licencia", False,
                   "Licencia VENCIDA", fatal=strict)
    elif status == LicenseStatus.NOT_FOUND:
        result.add("Licencia", False,
                   "No se encontró licencia", fatal=strict)
    elif status == LicenseStatus.INVALID_KEY:
        result.add("Licencia", False,
                   "Clave inválida o modificada", fatal=True)
    elif status == LicenseStatus.HARDWARE_MISMATCH:
        result.add("Licencia", False,
                   "Licencia activada en otro equipo", fatal=True)

    # 2. Verificar hardware
    hw_ok, hw_msg = verify_hardware_match()
    result.add("Hardware", hw_ok, hw_msg,
               fatal=(not hw_ok and strict and status == LicenseStatus.VALID))

    # 3. Verificar reloj
    clk_ok, clk_msg = verify_system_clock()
    result.add("Reloj sistema", clk_ok, clk_msg, fatal=False)

    # 4. Sandbox (advertencia, no fatal)
    sandbox, sb_msg = detect_sandbox()
    result.add("Entorno", not sandbox, sb_msg, fatal=False)

    return result