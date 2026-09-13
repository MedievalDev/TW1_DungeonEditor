# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for TW1DungeonEditor.exe
# Build: build_exe.bat  (one file, no console)
# The exe contains no SDK files. It looks for Dungeons.exe from the user's
# own Two Worlds SDK and asks for it on the first start if it is not found.

block_cipher = None

a = Analysis(
    ['dungeon_editor.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=['theme'],
    hookspath=[],
    runtime_hooks=[],
    excludes=['numpy', 'PIL', 'matplotlib', 'pandas', 'scipy', 'IPython',
              'pydoc', 'unittest', 'test', 'lib2to3', 'sqlite3',
              'xmlrpc', 'multiprocessing', 'test_i18n',
              # not used by the tool, keeps the exe small
              'ssl', '_ssl', '_hashlib', 'lzma', '_lzma', 'bz2', '_bz2',
              'decimal', '_decimal', 'http', 'email', 'xml', 'pyexpat',
              'urllib.request', 'asyncio', 'concurrent', 'sqlite3'],
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
    name='TW1DungeonEditor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
)
