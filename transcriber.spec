# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['transcriber.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('models/base.pt', 'models'),
        ('bin/ffmpeg.exe', 'bin'),
        ('bin/ffprobe.exe', 'bin'),
        ('assets/logo.webp', 'assets'),
        ('settings.json', '.'),
    ],
    hiddenimports=[],
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
    name='transcriber',
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
    icon='qca-logo.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='transcriber'
)
