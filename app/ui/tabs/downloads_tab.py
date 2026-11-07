from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtWidgets import (
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)


class DownloadsTab(QWidget):
    """Aba de downloads com visualização dos arquivos salvos e uso real de armazenamento."""

    def __init__(self, output_dir: str):
        super().__init__()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 25, 30, 25)
        self.layout.setSpacing(16)

        title = QLabel("Downloads")
        title.setObjectName("section_title")
        self.layout.addWidget(title)

        self.storage_label = QLabel("0 arquivos · 0 MB")
        self.storage_label.setObjectName("subtitle")
        self.layout.addWidget(self.storage_label)

        self.storage_bar = QProgressBar()
        self.storage_bar.setRange(0, 100)
        self.storage_bar.setValue(0)
        self.layout.addWidget(self.storage_bar)

        self.items_container = QWidget()
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(10)
        self.layout.addWidget(self.items_container)

    def refresh(self):
        total_bytes = 0
        files = []

        if self.output_dir.exists():
            for path in sorted(self.output_dir.iterdir()):
                if path.is_file():
                    files.append(path)
                    total_bytes += path.stat().st_size

        self.storage_label.setText(f"{len(files)} arquivo(s) · {self._format_size(total_bytes)}")

        for item in list(self.items_layout.children()):
            if hasattr(item, "setParent") and item is not self.items_container:
                item.deleteLater()

        if not files:
            empty = QLabel("Nenhum download encontrado.")
            empty.setObjectName("subtitle")
            self.items_layout.addWidget(empty)
            self.storage_bar.setValue(0)
            return

        for path in files:
            row = QWidget()
            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(12, 10, 12, 10)
            row_layout.setSpacing(4)

            row_layout.addWidget(QLabel(path.name))
            row_layout.addWidget(QLabel(self._format_size(path.stat().st_size)))
            row.setStyleSheet("background-color: #1F2937; border: 1px solid #374151; border-radius: 8px;")
            self.items_layout.addWidget(row)

        self.storage_bar.setValue(100 if total_bytes else 0)

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        units = ["B", "KB", "MB", "GB"]
        size = float(size_bytes)
        unit_index = 0
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        return f"{size:.1f} {units[unit_index]}" if unit_index else f"{int(size)} {units[unit_index]}"
