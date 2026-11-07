from __future__ import annotations

import sys
from pathlib import Path


def resource_path(relative_path: str) -> str:
    """Path to a bundled read-only resource (works from source and PyInstaller)."""
    base_path = getattr(sys, "_MEIPASS", None)
    if base_path:
        return str(Path(base_path) / relative_path)
    return str(Path(__file__).resolve().parents[2] / relative_path)


def app_root() -> Path:
    """Writable base directory: next to the executable when frozen, project root otherwise."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def app_data_dir() -> Path:
    return app_root() / "app_data"


def downloads_dir() -> Path:
    return app_root() / "downloads"


def thumbnails_dir() -> Path:
    return app_data_dir() / "thumbnails"
