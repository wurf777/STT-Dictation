# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_all

# Bundle Tcl/Tk from the non-standard location used by Python 3.13 on Windows
_tcl_src = os.path.join(sys.base_prefix, "tcl")
datas = [('icon.png', '.')]
if os.path.isdir(_tcl_src):
    datas += [(_tcl_src, "tcl")]

# Explicitly bundle the tkinter Python package files
import tkinter as _tk_mod
_tkinter_pkg_dir = os.path.dirname(_tk_mod.__file__)
datas += [(_tkinter_pkg_dir, "tkinter")]

# Explicitly bundle _tkinter.pyd and Tcl/Tk DLLs (non-standard location in Python 3.13)
_dll_dir = os.path.join(sys.base_prefix, "DLLs")
binaries = []
for _dll in ("_tkinter.pyd", "tcl86t.dll", "tk86t.dll"):
    _path = os.path.join(_dll_dir, _dll)
    if os.path.exists(_path):
        binaries += [(_path, ".")]
hiddenimports = ['tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog',
                 'faster_whisper', 'pyperclip', 'pyautogui', 'pystray', 'keyboard', 'sounddevice', 'numpy']
tmp_ret = collect_all('faster_whisper')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('nvidia.cublas')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('nvidia.cudnn')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
for _nvidia_pkg in ('nvidia.cuda_runtime', 'nvidia.cufft', 'nvidia.curand', 'nvidia.cusolver', 'nvidia.cusparse', 'nvidia.cublas'):
    try:
        tmp_ret = collect_all(_nvidia_pkg)
        datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
    except Exception:
        pass


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['rthook_tcl.py'],
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
    name='STT Dictation',
    icon='icon.ico',
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
    name='STT Dictation',
)
