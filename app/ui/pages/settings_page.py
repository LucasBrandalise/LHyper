from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.core.constants import APP_NAME, APP_VERSION
from app.core.paths import app_data_dir, downloads_dir
from app.services.youtube_service import YouTubeService
from app.ui.components import icons
from app.ui.components.controls import StatusDot
from app.ui.styles import theme


class SettingsPage(QWidget):
    """Informações do ambiente: pastas, FFmpeg e versão."""

    def __init__(self, output_dir: str | Path | None = None):
        super().__init__()
        self.output_dir = Path(output_dir) if output_dir is not None else downloads_dir()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(0)

        title = QLabel("Configurações")
        title.setObjectName("page_title")
        layout.addWidget(title)
        layout.addSpacing(8)
        subtitle = QLabel("Onde os arquivos ficam e o que o LHyper encontrou neste computador")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)
        layout.addSpacing(24)

        card = QFrame()
        card.setObjectName("card")
        rows = QVBoxLayout(card)
        rows.setContentsMargins(20, 4, 20, 4)
        rows.setSpacing(0)

        ffmpeg = YouTubeService.ffmpeg_available()
        entries = [
            ("folder", "Pasta de downloads", str(self.output_dir), True, lambda: self._open(self.output_dir), None),
            ("disk", "Dados do aplicativo", str(app_data_dir()), True, lambda: self._open(app_data_dir()), None),
            (
                "bolt",
                "FFmpeg",
                "Conversão para MP3 e junção de vídeo em alta resolução disponíveis"
                if ffmpeg
                else "Instale o FFmpeg e adicione-o ao PATH para baixar MP3 e MP4 em alta resolução",
                False,
                None,
                ("Encontrado", "success") if ffmpeg else ("Não encontrado", "warning"),
            ),
            ("info", "Versão", f"{APP_NAME} {APP_VERSION}", False, None, None),
        ]
        for i, (icon_name, name, value, mono, action, badge) in enumerate(entries):
            if i:
                line = QFrame()
                line.setFixedHeight(1)
                line.setStyleSheet(f"background:{theme.HAIRLINE}; border:none;")
                rows.addWidget(line)
            rows.addWidget(self._row(icon_name, name, value, mono, action, badge))

        layout.addWidget(card)
        layout.addStretch()

    @staticmethod
    def _open(path: Path):
        Path(path).mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    @staticmethod
    def _row(icon_name, title, value, mono, action, badge) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(12)

        icon = QLabel()
        icon.setFixedSize(16, 20)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setPixmap(icons.pixmap(icon_name, theme.TEXT_3, 16))
        layout.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)

        text = QVBoxLayout()
        text.setSpacing(4)
        name = QLabel(title)
        name.setObjectName("card_title")
        detail = QLabel(value)
        detail.setObjectName("mono_meta" if mono else "subtitle")
        detail.setWordWrap(True)
        detail.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        text.addWidget(name)
        text.addWidget(detail)
        layout.addLayout(text, 1)

        if badge:
            dot = StatusDot(6)
            dot.set_state(badge[1])
            label = QLabel(badge[0])
            label.setObjectName("subtitle")
            layout.addWidget(dot, 0, Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(label, 0, Qt.AlignmentFlag.AlignVCenter)
        if action:
            button = QPushButton(" Abrir")
            button.setObjectName("secondary_button")
            button.setIcon(icons.icon("open", theme.TEXT_2, 16))
            button.setFixedHeight(32)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(action)
            layout.addWidget(button, 0, Qt.AlignmentFlag.AlignVCenter)
        return row
