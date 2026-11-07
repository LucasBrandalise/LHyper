from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from app.database.download_repository import DownloadRepository


class DownloadsTab(QWidget):
    """Aba de downloads com visualização dos arquivos salvos e uso real de armazenamento."""

    def __init__(self, output_dir: str, repository: DownloadRepository | None = None):
        super().__init__()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.repository = repository or DownloadRepository()

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 25, 30, 25)
        self.layout.setSpacing(16)

        title = QLabel("Downloads")
        title.setObjectName("section_title")
        self.layout.addWidget(title)

        self.storage_label = QLabel("0 arquivos · 0 B")
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
        self.repository.sync_from_disk(self.output_dir)
        records = self.repository.list()

        total_bytes = sum(record.file_size for record in records)
        self.storage_label.setText(f"{len(records)} arquivo(s) · {self._format_size(total_bytes)}")

        while self.items_layout.count():
            item = self.items_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not records:
            empty = QLabel("Nenhum download encontrado.")
            empty.setObjectName("subtitle")
            self.items_layout.addWidget(empty)
            self.storage_bar.setValue(0)
            return

        max_file_size = max((record.file_size for record in records), default=1)
        ratio = min(100, max(0, int((total_bytes / max(1, max_file_size * 2)) * 100)))
        self.storage_bar.setValue(ratio)

        for record in records:
            row = QWidget()
            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(12, 10, 12, 10)
            row_layout.setSpacing(4)

            title_label = QLabel(record.title)
            size_label = QLabel(f"{record.file_format.upper()} · {self._format_size(record.file_size)}")
            status_label = QLabel(record.status.capitalize())

            row_layout.addWidget(title_label)
            row_layout.addWidget(size_label)
            row_layout.addWidget(status_label)
            row.setStyleSheet("background-color: #1F2937; border: 1px solid #374151; border-radius: 8px;")
            self.items_layout.addWidget(row)

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        units = ["B", "KB", "MB", "GB"]
        size = float(size_bytes)
        unit_index = 0
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        return f"{size:.1f} {units[unit_index]}"
