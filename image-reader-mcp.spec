# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build definition for the image-reader-mcp server.

Build a single self-contained executable with::

    uv run pyinstaller image-reader-mcp.spec --clean --noconfirm

The resulting binary is written to ``dist/`` and runs without a Python
installation. Because the server speaks MCP over stdio, the executable is a
console application.
"""

import os

from PyInstaller.utils.hooks import collect_all

# ``SPECPATH`` is injected by PyInstaller and points at the directory holding
# this spec, so the build works regardless of the current working directory.
PROJECT_ROOT = SPECPATH  # noqa: F821 - injected by PyInstaller

ENTRY_POINT = os.path.join(PROJECT_ROOT, "src", "image_reader_mcp", "__main__.py")
SOURCE_PATH = os.path.join(PROJECT_ROOT, "src")

datas = []
binaries = []
hiddenimports = []

# The MCP SDK discovers transports, encoders and extras at runtime, so
# PyInstaller's static analysis cannot follow every import. Collect these
# distributions wholesale (submodules, data files and metadata) to keep the
# frozen server functionally identical to the source tree.
for package in (
    "mcp",
    "pydantic",
    "pydantic_core",
    "anyio",
    "httpx",
    "httpcore",
    "h11",
    "sniffio",
    "starlette",
    "uvicorn",
    "sse_starlette",
    "certifi",
    "requests",
    "charset_normalizer",
    "idna",
    "urllib3",
):
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

a = Analysis(  # noqa: F821 - injected by PyInstaller
    [ENTRY_POINT],
    pathex=[SOURCE_PATH],
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
pyz = PYZ(a.pure)  # noqa: F821 - injected by PyInstaller

exe = EXE(  # noqa: F821 - injected by PyInstaller
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="image-reader-mcp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
