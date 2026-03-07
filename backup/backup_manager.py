"""
Sistema de Backup Automatico - Venialgo Sistemas
Backups comprimidos con rotacion y restauracion.
"""

import os
import threading
import zipfile
from datetime import datetime
from pathlib import Path
import sys as _sys

# ── Rutas absolutas (AppData/VenialgoPOS) ──
def _get_appdata_dir():
    if _sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.path.expanduser("~")
    d = os.path.join(base, "VenialgoPOS")
    os.makedirs(d, exist_ok=True)
    return d

APPDATA_DIR  = _get_appdata_dir()
DB_FILE      = os.path.join(APPDATA_DIR, "pos_database.db")
BACKUP_DIR   = Path(APPDATA_DIR) / "backups"  # ruta absoluta
DB_ARCNAME   = "pos_database.db"              # nombre simple dentro del zip
MAX_BACKUPS  = 30
INTERVAL_MIN = 60


def _ensure_backup_dir():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def create_backup(label="auto"):
    _ensure_backup_dir()
    if not os.path.exists(DB_FILE):
        return False, "Base de datos no encontrada: " + DB_FILE
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = BACKUP_DIR / f"pos_backup_{ts}_{label}.zip"
    try:
        with zipfile.ZipFile(str(filename), "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(DB_FILE, DB_ARCNAME)  # arcname simple, sin ruta absoluta
            meta = (
                f"Backup: {filename.name}\n"
                f"Fecha:  {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                f"Tipo:   {label}\n"
                f"BD:     {os.path.getsize(DB_FILE):,} bytes\n"
                f"Origen: {DB_FILE}\n"
            )
            zf.writestr("backup_info.txt", meta)
        _rotate_backups()
        return True, str(filename)
    except Exception as e:
        return False, str(e)


def restore_backup(zip_path):
    if not os.path.exists(zip_path):
        return False, "Archivo no encontrado: " + zip_path
    try:
        _ensure_backup_dir()
        if os.path.exists(DB_FILE):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            safety = BACKUP_DIR / f"pre_restore_{ts}.zip"
            with zipfile.ZipFile(str(safety), "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(DB_FILE, DB_ARCNAME)
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            if DB_ARCNAME in names:
                data = zf.read(DB_ARCNAME)
                with open(DB_FILE, "wb") as f:
                    f.write(data)
            else:
                return False, f"El zip no contiene {DB_ARCNAME!r}. Contenido: {names}"
        return True, f"BD restaurada desde:\n{zip_path}"
    except Exception as e:
        return False, str(e)


def list_backups():
    _ensure_backup_dir()
    result = []
    for f in sorted(BACKUP_DIR.glob("pos_backup_*.zip"), reverse=True):
        result.append({
            "name":     f.name,
            "path":     str(f),
            "size_kb":  round(f.stat().st_size / 1024, 1),
            "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%d/%m/%Y %H:%M"),
        })
    return result


def _rotate_backups():
    _ensure_backup_dir()
    backups = sorted(BACKUP_DIR.glob("pos_backup_*.zip"))
    while len(backups) > MAX_BACKUPS:
        try: backups.pop(0).unlink()
        except Exception: pass


class AutoBackupService:
    def __init__(self, interval_min=INTERVAL_MIN, on_backup=None):
        self.interval_sec = interval_min * 60
        self.on_backup    = on_backup
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

    def force_backup(self):
        ok, msg = create_backup(label="manual")
        if ok:
            self._last_backup = datetime.now()
        if self.on_backup:
            try: self.on_backup(ok, msg)
            except Exception: pass
        return ok, msg

    @property
    def last_backup_str(self):
        if not self._last_backup:
            return "Sin backup reciente"
        return self._last_backup.strftime("Ultimo: %d/%m/%Y %H:%M")

    def _notify(self, ok, msg):
        if self.on_backup:
            try: self.on_backup(ok, msg)
            except Exception: pass

    def _run(self):
        # Esperar 15 seg para que la UI termine de iniciar
        if self._stop_event.wait(15):
            return
        ok, msg = create_backup(label="inicio")
        self._last_backup = datetime.now() if ok else None
        self._notify(ok, msg)
        while not self._stop_event.wait(self.interval_sec):
            if os.path.exists(DB_FILE):
                ok, msg = create_backup(label="auto")
                if ok: self._last_backup = datetime.now()
                self._notify(ok, msg)


backup_service = AutoBackupService(interval_min=INTERVAL_MIN)
