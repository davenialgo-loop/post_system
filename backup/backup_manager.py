"""
Sistema de Backup Automático — Venialgo Sistemas
Backups comprimidos con rotación y restauración
"""

import os
import shutil
import sqlite3
import threading
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

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
BACKUP_DIR   = Path("backups")
MAX_BACKUPS  = 30          # cantidad máxima de backups a mantener
INTERVAL_MIN = 60          # backup automático cada N minutos


# ════════════════════════════════════════════════════════
#  CORE — crear / restaurar backup
# ════════════════════════════════════════════════════════

def _ensure_backup_dir():
    BACKUP_DIR.mkdir(exist_ok=True)


def create_backup(label: str = "auto") -> tuple[bool, str]:
    """
    Crea un backup comprimido de la base de datos.
    Nombre: pos_backup_YYYYMMDD_HHMMSS_<label>.zip
    Retorna (éxito, ruta_o_error).
    """
    _ensure_backup_dir()

    if not os.path.exists(DB_FILE):
        return False, "No se encontró la base de datos."

    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = BACKUP_DIR / f"pos_backup_{ts}_{label}.zip"

    try:
        with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(DB_FILE, DB_FILE)

            # Metadatos del backup
            meta = (
                f"Backup: {filename.name}\n"
                f"Fecha:  {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                f"Tipo:   {label}\n"
                f"BD:     {os.path.getsize(DB_FILE):,} bytes\n"
            )
            zf.writestr("backup_info.txt", meta)

        _rotate_backups()
        return True, str(filename)

    except Exception as e:
        return False, str(e)


def restore_backup(zip_path: str) -> tuple[bool, str]:
    """
    Restaura la base de datos desde un backup .zip.
    Hace un backup de seguridad antes de restaurar.
    """
    if not os.path.exists(zip_path):
        return False, "Archivo de backup no encontrado."

    try:
        # Backup de seguridad antes de restaurar
        if os.path.exists(DB_FILE):
            safety = BACKUP_DIR / f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            with zipfile.ZipFile(safety, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(DB_FILE, DB_FILE)

        # Restaurar
        with zipfile.ZipFile(zip_path, 'r') as zf:
            if DB_FILE in zf.namelist():
                zf.extract(DB_FILE, ".")
            else:
                return False, "El archivo zip no contiene la base de datos."

        return True, f"Base de datos restaurada desde:\n{zip_path}"

    except Exception as e:
        return False, str(e)


def list_backups() -> list[dict]:
    """
    Lista todos los backups disponibles ordenados por fecha (más reciente primero).
    """
    _ensure_backup_dir()
    backups = []
    for f in sorted(BACKUP_DIR.glob("pos_backup_*.zip"), reverse=True):
        size = f.stat().st_size
        backups.append({
            "name":     f.name,
            "path":     str(f),
            "size_kb":  round(size / 1024, 1),
            "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%d/%m/%Y %H:%M"),
        })
    return backups


def _rotate_backups():
    """Elimina backups más antiguos si se supera MAX_BACKUPS."""
    _ensure_backup_dir()
    backups = sorted(BACKUP_DIR.glob("pos_backup_*.zip"))
    while len(backups) > MAX_BACKUPS:
        oldest = backups.pop(0)
        try:
            oldest.unlink()
        except Exception:
            pass


# ════════════════════════════════════════════════════════
#  BACKUP AUTOMÁTICO  (hilo en segundo plano)
# ════════════════════════════════════════════════════════

class AutoBackupService:
    """
    Servicio de backup automático que corre en un hilo daemon.

    Uso:
        service = AutoBackupService(interval_min=60)
        service.start()
        # Para detener:
        service.stop()
    """

    def __init__(self, interval_min: int = INTERVAL_MIN,
                 on_backup: callable = None):
        self.interval_sec = interval_min * 60
        self.on_backup    = on_backup   # callback(ok, msg) opcional
        self._stop_event  = threading.Event()
        self._thread      = None
        self._last_backup = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def force_backup(self) -> tuple[bool, str]:
        """Dispara un backup inmediato (llamable desde la UI)."""
        ok, msg = create_backup(label="manual")
        self._last_backup = datetime.now() if ok else self._last_backup
        if self.on_backup:
            self.on_backup(ok, msg)
        return ok, msg

    @property
    def last_backup_str(self) -> str:
        if not self._last_backup:
            return "Sin backup reciente"
        return self._last_backup.strftime("Último: %d/%m/%Y %H:%M")

    def _run(self):
        # Backup inicial al iniciar el servicio
        ok, msg = create_backup(label="inicio")
        self._last_backup = datetime.now() if ok else None
        if self.on_backup:
            self.on_backup(ok, msg)

        while not self._stop_event.wait(self.interval_sec):
            if os.path.exists(DB_FILE):
                ok, msg = create_backup(label="auto")
                self._last_backup = datetime.now() if ok else self._last_backup
                if self.on_backup:
                    self.on_backup(ok, msg)


# ════════════════════════════════════════════════════════
#  INSTANCIA GLOBAL  (importar desde otros módulos)
# ════════════════════════════════════════════════════════
backup_service = AutoBackupService(interval_min=INTERVAL_MIN)