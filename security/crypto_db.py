"""
Encriptación de Base de Datos — Venialgo Sistemas
Cifrado transparente AES-128 (Fernet) sobre SQLite
"""

import os
import shutil
import sqlite3
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken

DB_FILE        = "pos_database.db"
DB_ENCRYPTED   = "pos_data.enc"
DB_KEY_FILE    = "pos.key"
DB_BACKUP_PLAIN = "pos_database.bak"

# ════════════════════════════════════════════════════════
#  GESTIÓN DE CLAVE DE CIFRADO
# ════════════════════════════════════════════════════════

def _derive_key(passphrase: str) -> bytes:
    """Deriva una clave Fernet de 32 bytes desde una passphrase."""
    digest = hashlib.sha256(passphrase.encode()).digest()
    import base64
    return base64.urlsafe_b64encode(digest)


def init_encryption(passphrase: str = None) -> Fernet:
    """
    Inicializa el sistema de cifrado.
    - Si existe pos.key, lo carga.
    - Si no, genera uno nuevo desde la passphrase o aleatoriamente.
    """
    if os.path.exists(DB_KEY_FILE):
        with open(DB_KEY_FILE, 'rb') as f:
            key = f.read().strip()
    else:
        if passphrase:
            key = _derive_key(passphrase)
        else:
            key = Fernet.generate_key()
        with open(DB_KEY_FILE, 'wb') as f:
            f.write(key)

    return Fernet(key)


def encrypt_database(fernet: Fernet = None):
    """
    Cifra pos_database.db → pos_data.enc
    y elimina el DB en claro (mantiene backup .bak).
    """
    if not os.path.exists(DB_FILE):
        return

    if fernet is None:
        fernet = init_encryption()

    # Leer DB en binario
    with open(DB_FILE, 'rb') as f:
        data = f.read()

    # Cifrar
    encrypted = fernet.encrypt(data)

    # Guardar cifrado
    with open(DB_ENCRYPTED, 'wb') as f:
        f.write(encrypted)

    # Backup del plano (por si acaso) antes de borrar
    shutil.copy2(DB_FILE, DB_BACKUP_PLAIN)
    os.remove(DB_FILE)


def decrypt_database(fernet: Fernet = None) -> bool:
    """
    Descifra pos_data.enc → pos_database.db
    Retorna True si tuvo éxito.
    """
    if not os.path.exists(DB_ENCRYPTED):
        return True  # Nada que descifrar, primera ejecución

    if fernet is None:
        if not os.path.exists(DB_KEY_FILE):
            return False
        fernet = init_encryption()

    try:
        with open(DB_ENCRYPTED, 'rb') as f:
            encrypted = f.read()

        data = fernet.decrypt(encrypted)

        with open(DB_FILE, 'wb') as f:
            f.write(data)

        return True
    except InvalidToken:
        return False
    except Exception:
        return False


# ════════════════════════════════════════════════════════
#  CONTEXTO MANAGER — uso transparente
# ════════════════════════════════════════════════════════

class SecureDB:
    """
    Context manager para trabajar con la DB cifrada de forma transparente.

    Uso:
        with SecureDB() as conn:
            conn.execute("SELECT * FROM productos")

    Al entrar: descifra automáticamente.
    Al salir:  vuelve a cifrar.
    """

    def __init__(self, passphrase: str = None):
        self.fernet = init_encryption(passphrase)
        self._conn  = None

    def __enter__(self) -> sqlite3.Connection:
        decrypt_database(self.fernet)
        self._conn = sqlite3.connect(DB_FILE)
        self._conn.row_factory = sqlite3.Row
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn:
            self._conn.commit()
            self._conn.close()
        encrypt_database(self.fernet)
        # Eliminar DB en claro después de uso
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        return False


# ════════════════════════════════════════════════════════
#  MODO DESARROLLO  (cifrado OFF)
# ════════════════════════════════════════════════════════

class DevDB:
    """
    Context manager SIN cifrado — solo para desarrollo.
    Usa la misma interfaz que SecureDB para fácil intercambio.
    """

    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self._conn   = None

    def __enter__(self) -> sqlite3.Connection:
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn:
            self._conn.commit()
            self._conn.close()
        return False


def get_db_context(production: bool = False):
    """
    Factory: retorna SecureDB en producción, DevDB en desarrollo.
    Uso:
        DB = get_db_context(production=IS_LICENSED)
        with DB() as conn:
            ...
    """
    return SecureDB if production else DevDB