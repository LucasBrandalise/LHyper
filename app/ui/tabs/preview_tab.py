from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class PreviewTab(QWidget):
    """Tab principal para validar URL, escolher formato e iniciar o download."""

    download_requested = Signal()

    def __init__(self, output_dir: str):
        super().__init__()
        self.output_dir = output_dir

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 35, 40, 35)
        layout.setSpacing(18)

        title = QLabel("Baixe seus conteúdos.")
        title.setObjectName("title")

        subtitle = QLabel("Cole um link do YouTube para começar.")
        subtitle.setObjectName("subtitle")

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.url_input.setMinimumHeight(48)
        self.url_input.returnPressed.connect(self.emit_download_request)

        self.format_select = QComboBox()
        self.format_select.addItems(["MP4 - Vídeo", "MP3 - Áudio"])
        self.format_select.setMinimumHeight(42)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

        self.status_label = QLabel("Pronto para começar.")
        self.status_label.setObjectName("status_label")

        self.download_button = QPushButton("Analisar conteúdo")
        self.download_button.setObjectName("primary_button")
        self.download_button.setMinimumHeight(48)
        self.download_button.clicked.connect(self.emit_download_request)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        layout.addWidget(QLabel("URL DO CONTEÚDO"))
        layout.addWidget(self.url_input)
        layout.addWidget(QLabel("FORMATO"))
        layout.addWidget(self.format_select)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addWidget(self.download_button)
        layout.addStretch()

    def emit_download_request(self):
        self.download_requested.emit()

    def set_status(self, text: str):
        self.status_label.setText(text)

    def set_progress_visible(self, visible: bool):
        self.progress_bar.setVisible(visible)

    def set_progress(self, value: int):
        self.progress_bar.setValue(value)

    def set_button_enabled(self, enabled: bool):
        self.download_button.setEnabled(enabled)

    def get_url(self) -> str:
        return self.url_input.text().strip()

    def get_format(self) -> str:
        return self.format_select.currentText()
