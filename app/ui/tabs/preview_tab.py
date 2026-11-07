from __future__ import annotations

from pathlib import Path
from urllib.request import urlretrieve

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class PreviewTab(QWidget):
    """Tab principal para validar URL, mostrar preview e iniciar o download."""

    download_requested = Signal()

    def __init__(self, output_dir: str):
        super().__init__()
        self.output_dir = output_dir
        self.cache_dir = Path(output_dir).parent / "app_data" / "thumbnails"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

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
        self.url_input.editingFinished.connect(self.emit_download_request)

        self.format_select = QComboBox()
        self.format_select.addItems(["MP4 - Vídeo", "MP3 - Áudio"])
        self.format_select.setMinimumHeight(42)

        self.thumbnail_label = QLabel("Preview")
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setFixedSize(360, 200)
        self.thumbnail_label.setStyleSheet(
            "background-color: #1F2937; border: 1px solid #374151; border-radius: 10px; color: #94A3B8;"
        )

        self.video_title = QLabel("Título do vídeo aparecerá aqui.")
        self.video_title.setWordWrap(True)
        self.video_title.setObjectName("title")

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
        layout.addWidget(self.thumbnail_label)
        layout.addWidget(self.video_title)
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

    def set_video_info(self, title: str, thumbnail_url: str | None = None):
        self.video_title.setText(title or "Título do vídeo aparecerá aqui.")
        if thumbnail_url:
            self.set_thumbnail(thumbnail_url)

    def set_thumbnail(self, thumbnail_url: str):
        cache_path = self.cache_dir / f"{abs(hash(thumbnail_url))}.jpg"
        if not cache_path.exists():
            try:
                urlretrieve(thumbnail_url, str(cache_path))
            except Exception:
                self.thumbnail_label.setText("Imagem indisponível")
                return

        pixmap = QPixmap(str(cache_path))
        if pixmap.isNull():
            self.thumbnail_label.setText("Imagem indisponível")
            return

        scaled = pixmap.scaled(
            self.thumbnail_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.thumbnail_label.setPixmap(scaled)
        self.thumbnail_label.setText("")

    def get_url(self) -> str:
        return self.url_input.text().strip()

    def get_format(self) -> str:
        return self.format_select.currentText()
