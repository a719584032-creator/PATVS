# -*- mode: python ; coding: utf-8 -*-
# 设置资源文件和目录
added_files = [
    ('D:\\PATVS\\ui_manager\\icon\\*', 'icon'),
    ('D:\\PATVS\\common', 'common'),
    ('D:\\PATVS\\config.json', 'config.json')
]

hidden_imports = [
    'loguru',
    'win32api',
    'win32gui',
    'win32con',
    'mysql.connector'
]

a = Analysis(
    ['patvs_gui.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='patvs_gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
