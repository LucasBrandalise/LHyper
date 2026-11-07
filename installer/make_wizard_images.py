"""Generate the installer wizard images from assets/icons/favicon.ico.

The icon is pixel art, so it is scaled by whole multiples with nearest-neighbour
sampling (2x and 4x) to stay crisp; Inno Setup picks the size matching the screen DPI.

    .venv\\Scripts\\python.exe installer\\make_wizard_images.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QIcon

ROOT = Path(__file__).resolve().parents[1]
ICON = ROOT / "assets" / "icons" / "favicon.ico"
OUT_DIR = ROOT / "installer" / "build"
SCALES = (2, 4)


def main() -> int:
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])  # noqa: F841 - Qt needs it
    source = QIcon(str(ICON)).pixmap(32, 32)
    if source.isNull():
        print(f"Não foi possível ler {ICON}", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for scale in SCALES:
        size = 32 * scale
        image = source.scaled(
            size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation
        ).toImage()
        target = OUT_DIR / f"wizard-small-{size}.png"
        if not image.save(str(target), "PNG"):
            print(f"Falha ao salvar {target}", file=sys.stderr)
            return 1
        print(target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
