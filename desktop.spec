# -*- mode: python ; coding: utf-8 -*-
import sys

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("src") + collect_submodules("config")

analysis = Analysis(
    ["src/desktop.py"],
    pathex=["."],
    binaries=[],
    datas=[("config", "config")],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=["installer/runtime_user_paths.py"],
    excludes=["tests", "secrets", "storage"],
    noarchive=False,
)

pyz = PYZ(analysis.pure)
exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="VideoTranslationPipeline",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        analysis.binaries,
        analysis.datas,
        name="VideoTranslationPipeline.app",
        icon=None,
        bundle_identifier="com.bdpp3942.videotranslationpipeline",
    )
else:
    coll = COLLECT(
        exe,
        analysis.binaries,
        analysis.datas,
        strip=False,
        upx=True,
        name="VideoTranslationPipeline",
    )
