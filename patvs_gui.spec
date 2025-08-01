# -*- mode: python ; coding: utf-8 -*-
import glob
import re

# 动态获取 conf 目录下的所有文件
conf_files = [(file, 'conf') for file in glob.glob('D:\\PATVS\\conf\\*')]


version = "unknown"
with open(r'D:\PATVS\conf\env.default', encoding='utf-8') as f:
    for line in f:
        match = re.match(r'VERSION\s*=\s*["\']?([^"\']+)["\']?', line)
        if match:
            version = match.group(1)
            break

# 设置资源文件和目录
added_files = [
    ('D:\\PATVS\\ui_manager\\icon\\*', 'icon'),
    ('D:\\PATVS\\common', 'common'),
    ('D:\\PATVS\\config_manager', 'config_manager'),
    ('D:\\PATVS\\config.json', 'config.json')
] + conf_files

hidden_imports = [
    'loguru',
    'win32api',
    'win32gui',
    'win32con',
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
    name=f'TestTrackingSystem-{version}',
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
