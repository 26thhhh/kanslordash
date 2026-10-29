# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# Get the project root
project_root = Path(SPECPATH)

import subprocess
try:
    build_commit = subprocess.check_output(['git', '-C', str(project_root), 'rev-parse', '--short', 'HEAD']).decode().strip()
    (project_root / 'BUILD_INFO').write_text(build_commit)
except Exception:
    build_commit = ''
    if (project_root / 'BUILD_INFO').exists():
        build_commit = (project_root / 'BUILD_INFO').read_text().strip()

datas_list = [
    (str(project_root / 'kanslordash' / 'ui' / 'app.tcss'), 'kanslordash/ui'),
]
if build_commit:
    (project_root / 'BUILD_INFO').write_text(build_commit)
    datas_list.append((str(project_root / 'BUILD_INFO'), '.'))

a = Analysis(
    ['windows_entry.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas_list,
    hiddenimports=[
        'textual',
        'rich',
        'platformdirs',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
        'IPython',
        'jupyter',
        'pytest',
        'pytest_asyncio',
        '_pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='KANSLORDASH',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='KANSLORDASH',
)
