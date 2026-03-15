# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Sobriety Counter.

Usage:
    pip install pyinstaller
    pyinstaller sobriety_counter.spec

This will create a standalone executable in the dist/ directory.
"""

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['src/sobriety_counter_gui.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'sobriety_core',
        'sobriety_db',
        'themes',
        'notifications',
        'tray',
        'plyer.platforms',
        'plyer.platforms.linux',
        'plyer.platforms.macosx',
        'plyer.platforms.win',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SobrietyCounter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# macOS .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='Sobriety Counter.app',
        icon=None,
        bundle_identifier='com.sobrietycounter.app',
        info_plist={
            'CFBundleName': 'Sobriety Counter',
            'CFBundleDisplayName': 'Sobriety Counter',
            'CFBundleVersion': '2.0.0',
            'CFBundleShortVersionString': '2.0.0',
            'LSMinimumSystemVersion': '10.13.0',
        },
    )
