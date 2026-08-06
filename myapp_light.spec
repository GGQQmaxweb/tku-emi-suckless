# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all

datas = [('gui', 'gui')]
binaries = []
hiddenimports = ['gi', 'gi.repository.Gtk', 'gi.repository.WebKit2']

# Collect all files for gi and webview
# Note: collect_all returns a tuple of (datas, binaries, hiddenimports)
tmp_datas, tmp_binaries, tmp_hiddenimports = collect_all('gi')
datas.extend(tmp_datas)
binaries.extend(tmp_binaries)
hiddenimports.extend(tmp_hiddenimports)

tmp_datas, tmp_binaries, tmp_hiddenimports = collect_all('webview')
datas.extend(tmp_datas)
binaries.extend(tmp_binaries)
hiddenimports.extend(tmp_hiddenimports)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# Core system libraries that must be loaded from the host OS to prevent ABI and version mismatches.
# Since this bundle is packaged as DEB/RPM and depends on the system GTK/WebKit, 
# these system-level libraries are guaranteed to be present on the target host.
excluded_libs = {
    'libfontconfig.so',
    'libfreetype.so',
    'libglib-2.0.so',
    'libgobject-2.0.so',
    'libgio-2.0.so',
    'libgthread-2.0.so',
    'libgmodule-2.0.so',
    'libpango-1.0.so',
    'libpangocairo-1.0.so',
    'libpangoft2-1.0.so',
    'libcairo.so',
    'libharfbuzz.so',
    'libpng16.so',
    'libz.so',
    'libgdk-3.so',
    'libgtk-3.so',
    'libgdk_pixbuf-2.0.so',
    # Additional low-level system dependencies to prevent symbol mismatches (e.g. MOUNT_2_40)
    'libmount.so',
    'libblkid.so',
    'libuuid.so',
    'libselinux.so',
    'libffi.so',
    'libpcre2-8.so',
    'libpcre.so',
    'libpixman-1.so',
    'libdbus-1.so',
    'libexpat.so'
}

a.binaries = [
    x for x in a.binaries
    if not any(lib in os.path.basename(x[0]) for lib in excluded_libs)
]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='myapp_light',
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='myapp_light',
)
