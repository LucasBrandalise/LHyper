from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QRectF, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.core.constants import FORMAT_MP3, STATUS_COMPLETED, STATUS_ERROR, STATUS_MISSING
from app.core.models import DownloadRecord
from app.database.download_repository import DownloadRepository
from app.ui.components import icons
from app.ui.components.controls import AnimatedProgressBar, StatusDot
from app.ui.styles import theme

STATUS_LABELS = {
    STATUS_COMPLETED: "Concluído",
    STATUS_ERROR: "Erro",
    STATUS_MISSING: "Arquivo não encontrado",
}
AUDIO_FORMATS = {FORMAT_MP3, "m4a", "aac", "opus", "ogg", "wav", "flac"}


def format_size(size_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(max(0, size_bytes))
    unit_index = 0
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    return f"{size:.1f} {units[unit_index]}"


def format_date(value: str | None) -> str:
    if not value:
        return ""
    try:
        return datetime.fromisoformat(value).astimezone().strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return ""


def cached_thumbnail(url: str | None) -> str | None:
    """Caminho da thumbnail já em cache (sem acessar a rede)."""
    if not url:
        return None
    try:
        from app.services.thumbnail_service import ThumbnailService

        path = ThumbnailService().cache_path(url)
    except (OSError, ValueError):
        return None
    return str(path) if path.is_file() else None


class _MediaTile(QWidget):
    """Miniatura 16:9 do item (thumbnail em cache ou ícone do formato)."""

    def __init__(self, record: DownloadRecord):
        super().__init__()
        self.setFixedSize(80, 45)
        self._audio = record.file_format.lower() in AUDIO_FORMATS
        thumb = cached_thumbnail(record.thumbnail)
        self._pixmap = QPixmap(thumb) if thumb else None
        if self._pixmap is not None and self._pixmap.isNull():
            self._pixmap = None

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(rect, 6, 6)
        p.setClipPath(path)
        if self._pixmap is not None:
            src = self._pixmap
            scale = max(rect.width() / src.width(), rect.height() / src.height())
            w, h = src.width() * scale, src.height() * scale
            p.drawPixmap(QRectF(rect.center().x() - w / 2, rect.center().y() - h / 2, w, h), src, QRectF(src.rect()))
        else:
            p.fillRect(rect, QColor(theme.SURFACE_2))
            pm = icons.pixmap("music" if self._audio else "film", theme.TEXT_3, 16)
            p.drawPixmap(int(rect.center().x() - 8), int(rect.center().y() - 8), pm)
        p.setClipping(False)
        p.setPen(QPen(QColor(237, 237, 237, 20), 1))
        p.drawPath(path)
        p.end()


class DownloadsPage(QWidget):
    """Histórico de downloads e uso de armazenamento do disco onde ficam os arquivos."""

    count_changed = Signal(int)

    def __init__(self, output_dir: str, repository: DownloadRepository | None = None):
        super().__init__()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.repository = repository or DownloadRepository()

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 32, 32, 24)
        main_layout.setSpacing(0)

        header = QHBoxLayout()
        header.setSpacing(8)
        titles = QVBoxLayout()
        titles.setSpacing(8)
        title = QLabel("Downloads")
        title.setObjectName("page_title")
        titles.addWidget(title)
        self.storage_label = QLabel("0 arquivos")
        self.storage_label.setObjectName("subtitle")
        self.storage_label.setWordWrap(True)
        titles.addWidget(self.storage_label)
        header.addLayout(titles, 1)

        refresh_button = QPushButton(" Atualizar")
        refresh_button.setObjectName("secondary_button")
        refresh_button.setIcon(icons.icon("refresh", theme.TEXT_2, 16))
        refresh_button.setFixedHeight(36)
        refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_button.clicked.connect(self.refresh)
        open_button = QPushButton(" Abrir pasta")
        open_button.setObjectName("secondary_button")
        open_button.setIcon(icons.icon("folder", theme.TEXT_2, 16))
        open_button.setFixedHeight(36)
        open_button.setCursor(Qt.CursorShape.PointingHandCursor)
        open_button.clicked.connect(self.open_folder)
        header.addWidget(refresh_button, 0, Qt.AlignmentFlag.AlignTop)
        header.addWidget(open_button, 0, Qt.AlignmentFlag.AlignTop)
        main_layout.addLayout(header)
        main_layout.addSpacing(24)

        # Disco: uma linha de meta e uma barra fina
        disk = QHBoxLayout()
        disk.setSpacing(8)
        disk_label = QLabel("Disco")
        disk_label.setObjectName("field_label")
        disk.addWidget(disk_label)
        disk.addStretch()
        self.disk_percent = QLabel("")
        self.disk_percent.setObjectName("mono_meta")
        disk.addWidget(self.disk_percent)
        main_layout.addLayout(disk)
        main_layout.addSpacing(8)
        self.storage_bar = AnimatedProgressBar()
        self.storage_bar.setRange(0, 100)
        self.storage_bar.setValue(0)
        main_layout.addWidget(self.storage_bar)
        main_layout.addSpacing(24)

        list_card = QFrame()
        list_card.setObjectName("card")
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(4, 4, 4, 4)
        list_layout.setSpacing(0)

        self.items_container = QWidget()
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(0)
        self.items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(self.items_container)
        list_layout.addWidget(scroll)
        main_layout.addWidget(list_card, 1)

    def open_folder(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.output_dir)))

    def refresh(self):
        self.repository.sync_from_disk(self.output_dir)
        records = self.repository.list()

        completed = [record for record in records if record.status == STATUS_COMPLETED]
        total_bytes = sum(record.file_size for record in completed)
        count = len(completed)
        summary = f"{count} {'arquivo' if count == 1 else 'arquivos'}, {format_size(total_bytes)} no total"

        try:
            usage = shutil.disk_usage(self.output_dir)
        except OSError:
            usage = None
        if usage is not None and usage.total > 0:
            percent = round(usage.used * 100 / usage.total)
            self.storage_bar.setValue(percent)
            self.disk_percent.setText(f"{format_size(usage.free)} livres  ·  {percent}% usado")
            self.storage_bar.setToolTip(
                f"Disco: {format_size(usage.used)} usados de {format_size(usage.total)}"
            )
        else:
            self.storage_bar.setValue(0)
            self.disk_percent.setText("")
        self.storage_label.setText(summary)
        self.count_changed.emit(len(completed))

        self._clear_items()
        if not records:
            self.items_layout.addWidget(self._build_empty())
            return

        for record in records:
            self.items_layout.addWidget(self._build_row(record))

    def _clear_items(self):
        while self.items_layout.count():
            item = self.items_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    @staticmethod
    def _build_empty() -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(24, 48, 24, 48)
        layout.setSpacing(8)
        icon = QLabel()
        icon.setPixmap(icons.pixmap("download", theme.TEXT_3, 18))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("Nenhum download ainda")
        title.setObjectName("card_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint = QLabel("Os arquivos baixados aparecem aqui")
        hint.setObjectName("subtitle")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(hint)
        return box

    @staticmethod
    def _build_row(record: DownloadRecord) -> QFrame:
        row = QFrame()
        row.setObjectName("download_row")
        row.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(12, 12, 12, 12)
        row_layout.setSpacing(16)

        row_layout.addWidget(_MediaTile(record), 0, Qt.AlignmentFlag.AlignTop)

        text = QVBoxLayout()
        text.setSpacing(4)
        title_label = QLabel(record.title)
        title_label.setObjectName("row_title")
        title_label.setWordWrap(True)
        title_label.setMinimumWidth(120)
        if record.file_path:
            title_label.setToolTip(record.file_path)
        text.addWidget(title_label)

        parts = [record.file_format.upper()]
        if record.status == STATUS_COMPLETED:
            parts.append(format_size(record.file_size))
        date = format_date(record.created_at)
        if date:
            parts.append(date)
        meta = QLabel("  ·  ".join(parts))
        meta.setObjectName("row_meta")
        text.addWidget(meta)

        if record.status == STATUS_ERROR and record.error_message:
            error_label = QLabel(record.error_message)
            error_label.setObjectName("download_error")
            error_label.setWordWrap(True)
            error_label.setMinimumWidth(120)
            text.addWidget(error_label)
        row_layout.addLayout(text, 1)

        # Status: ponto semântico + texto discreto
        status = QHBoxLayout()
        status.setSpacing(8)
        dot = StatusDot(6)
        dot.set_state({STATUS_COMPLETED: "success", STATUS_ERROR: "error", STATUS_MISSING: "warning"}.get(record.status, "idle"))
        status_label = QLabel(STATUS_LABELS.get(record.status, record.status.capitalize()))
        status_label.setObjectName(f"download_status_{record.status}")
        status.addWidget(dot)
        status.addWidget(status_label)
        row_layout.addLayout(status)

        actions = QHBoxLayout()
        actions.setSpacing(4)
        if record.status == STATUS_COMPLETED and record.file_path:
            path = record.file_path
            open_button = QPushButton()
            open_button.setObjectName("ghost_button")
            open_button.setIcon(icons.icon("play", theme.TEXT_2, 16))
            open_button.setToolTip("Abrir arquivo")
            open_button.setFixedSize(32, 32)
            open_button.setCursor(Qt.CursorShape.PointingHandCursor)
            open_button.clicked.connect(lambda _=False, p=path: QDesktopServices.openUrl(QUrl.fromLocalFile(p)))
            folder_button = QPushButton()
            folder_button.setObjectName("ghost_button")
            folder_button.setIcon(icons.icon("folder", theme.TEXT_2, 16))
            folder_button.setToolTip("Abrir pasta do arquivo")
            folder_button.setFixedSize(32, 32)
            folder_button.setCursor(Qt.CursorShape.PointingHandCursor)
            folder_button.clicked.connect(
                lambda _=False, p=path: QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(p).parent)))
            )
            actions.addWidget(open_button)
            actions.addWidget(folder_button)
        holder = QWidget()
        holder.setFixedWidth(68)  # mesma largura em todas as linhas: colunas alinhadas
        holder.setLayout(actions)
        actions.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(holder)

        return row
