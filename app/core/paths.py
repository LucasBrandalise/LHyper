"""Where the app reads resources and writes data.

Three ways to run, three layouts:

- **Source** (``python run.py``): everything under the project folder.
- **Portable** (extracted ``.zip``): data next to ``LHyper.exe``, so the folder can be
  moved as a whole. Detected by the ``portable.txt`` marker shipped in the zip, or by an
  existing ``app_data`` folder (v0.2.6 zips had no marker).
- **Installed** (``LHyper-Setup.exe``): the install folder is not meant for user data, so
  downloads go to the user's Downloads folder and app data to ``%LOCALAPPDATA%``.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR_NAME = "LHyper"
PORTABLE_MARKER = "portable.txt"


def resource_path(relative_path: str) -> str:
    """Path to a bundled read-only resource (works from source and PyInstaller)."""
    base_path = getattr(sys, "_MEIPASS", None)
    if base_path:
        return str(Path(base_path) / relative_path)
    return str(Path(__file__).resolve().parents[2] / relative_path)


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _executable_dir() -> Path:
    return Path(sys.executable).resolve().parent


def is_portable() -> bool:
    """Frozen build that keeps its data next to the executable."""
    if not is_frozen():
        return False
    exe_dir = _executable_dir()
    return (exe_dir / PORTABLE_MARKER).is_file() or (exe_dir / "app_data").is_dir()


def is_installed() -> bool:
    return is_frozen() and not is_portable()


def app_root() -> Path:
    """Base folder for source and portable runs: project root or the executable's folder."""
    if is_frozen():
        return _executable_dir()
    return Path(__file__).resolve().parents[2]


def _local_appdata() -> Path:
    value = os.environ.get("LOCALAPPDATA")
    return Path(value) if value else Path.home() / "AppData" / "Local"


def _user_downloads() -> Path:
    # Qt resolve a pasta Downloads real do Windows (inclusive se foi movida ou está no OneDrive).
    from PySide6.QtCore import QStandardPaths

    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
    return Path(location) if location else Path.home() / "Downloads"


def app_data_dir() -> Path:
    if is_installed():
        return _local_appdata() / APP_DIR_NAME
    return app_root() / "app_data"


def downloads_dir() -> Path:
    if is_installed():
        return _user_downloads() / APP_DIR_NAME
    return app_root() / "downloads"


def thumbnails_dir() -> Path:
    return app_data_dir() / "thumbnails"
