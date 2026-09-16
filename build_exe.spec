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
    hiddenimports=['theme', 'guidebook', 'updater', 'version'],
    hookspath=[],
    runtime_hooks=[],
    excludes=['numpy', 'PIL', 'matplotlib', 'pandas', 'scipy', 'IPython',
              'pydoc', 'unittest', 'test', 'lib2to3', 'sqlite3',
              'xmlrpc', 'multiprocessing', 'test_i18n', 'test_guide',
              # not used by the tool, keeps the exe small. Do NOT add ssl,
              # http, email or urllib here: the update check needs them
              # (PY_TOOL_DESIGN.md 9.3).
              'lzma', '_lzma', 'bz2', '_bz2', 'decimal', '_decimal',
              'asyncio', 'concurrent', 'sqlite3', 'xml', 'pyexpat',
              'xmlrpc', 'pydoc_data'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
# Hält die Exe unter 10 MB (Upload-Grenze im Browser).
# Tcl/Tk-Daten, die das Tool nie braucht: Zeitzonen, Demo-Bilder, Test- und
# HTTP-Module von Tcl, ostasiatische Zeichensätze. msgcat und msgs bleiben
# drin, Tk lädt sie beim Start.
_DROP = ('_tcl_data/tzdata/', '_tk_data/images/', '_tk_data/demos/',
         'tcl8/8.5/tcltest', 'tcl8/8.6/http-')
_DROP_ENC = ('cp932', 'cp936', 'cp949', 'cp950', 'big5', 'cns11643', 'euc-cn',
             'euc-jp', 'euc-kr', 'gb12345', 'gb1988', 'gb2312', 'jis0201',
             'jis0208', 'jis0212', 'ksc5601', 'shiftjis', 'iso2022')
a.datas = [d for d in a.datas
           if not any(x in d[0].replace(chr(92), '/') for x in _DROP)
           and not (d[0].replace(chr(92), '/').startswith('_tcl_data/encoding/')
                    and d[0].replace(chr(92), '/').split('/')[-1].startswith(_DROP_ENC))]
# Windows 10 und 11 bringen die UCRT mit.
a.binaries = [b for b in a.binaries
              if not (b[0].lower() == 'ucrtbase.dll'
                      or b[0].lower().startswith('api-ms-win-crt-'))]
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
