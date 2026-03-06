# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

project_root = Path(os.path.dirname(os.path.abspath('__file__')))

a = Analysis(
    ['src/gui/main_window.py'],
    pathex=[str(project_root / 'src')],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('scripts', 'scripts'),
        # ('sounds', 'sounds'),
    ],
    hiddenimports=[
        'mido',
        'mido.backends.rtmidi',
        'sounddevice',
        'soundfile',
        'numpy',
        'httpx',
        'pynput',
        'pynput.keyboard',
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'yaml',
        'bank_manager',
        'midi_handler',
        'soundboard',
        'action_runner',
        'midi_types',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter',
        'PIL',
        'scipy',
        'pandas',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MidiFighter3D',
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
    # icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MidiFighter3D'
)
