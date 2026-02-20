# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main_comercial.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('config', 'config')],
    hiddenimports=['cryptography', 'cryptography.fernet', 'cryptography.hazmat', 'cryptography.hazmat.primitives', 'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog', 'sqlite3', 'hashlib', 'hmac', 'uuid', 'zipfile', 'threading', 'PIL', 'PIL.Image', 'PIL.ImageTk'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='POS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='POS',
)
