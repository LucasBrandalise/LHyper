# -*- mode: python ; coding: utf-8 -*-
# Build do executável Windows (pasta dist/LHyper/ com LHyper.exe).
#
#   .venv\Scripts\python.exe -m PyInstaller LHyper.spec --noconfirm
#
# O mesmo arquivo é usado pelo GitHub Actions (.github/workflows/release.yml).

a = Analysis(
    ["run.py"],
    pathex=[],
    binaries=[],
    # Fontes e ícones lidos em tempo de execução via app.core.paths.resource_path().
    datas=[("assets", "assets")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "pydoc_data"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LHyper",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon="assets/icons/favicon.ico",
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="LHyper",
)
