from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QFont, QFontMetrics, QGuiApplication, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QBoxLayout,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.core.constants import (
    AUDIO_QUALITY_OPTIONS,
    FORMAT_MP3,
    FORMAT_MP4,
    FORMAT_OPTIONS,
    QUALITY_BEST,
    VIDEO_QUALITY_OPTIONS,
)
from app.core.models import VideoInfo
from app.ui.components import icons
from app.ui.components.controls import AnimatedProgressBar, PrimaryButton, SegmentedControl
from app.ui.styles import theme

PLACEHOLDER_TITLE = "O título do vídeo aparece aqui"
PLACEHOLDER_THUMBNAIL = "Cole um link para ver o preview"

# Rótulos do seletor (o código interno continua vindo de FORMAT_OPTIONS).
_FORMAT_SHORT = {FORMAT_MP4: ("Vídeo MP4", "video"), FORMAT_MP3: ("Áudio MP3", "music")}


def format_duration(seconds: int | float | None) -> str:
    if not seconds:
        return ""
    total = int(seconds)
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def _display_text(text: str) -> str:
    """Frases curtas da interface aparecem sem ponto final."""
    stripped = text.strip()
    if stripped.endswith(".") and not stripped.endswith("...") and ". " not in stripped[:-1]:
        return stripped[:-1]
    return stripped


# ====================================================================== thumbnail
class ThumbnailLabel(QLabel):
    """Área 16:9 que mantém o pixmap original e o desenha em modo "cover".

    É o momento visual da tela: o quadro real do vídeo com a duração no canto,
    como num player. Sem imagem, mostra um estado vazio neutro.
    """

    MIN_WIDTH = 280
    MIN_HEIGHT = 158
    MAX_HEIGHT = 360

    def __init__(self, text: str = ""):
        super().__init__(text)
        self._source: QPixmap | None = None
        self._fallback = text
        self._loading = False
        self._phase = 0.0
        self._timecode = ""
        self.setMinimumWidth(self.MIN_WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._timer = QTimer(self, interval=33)
        self._timer.timeout.connect(self._tick)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return min(self.MAX_HEIGHT, max(self.MIN_HEIGHT, int(width * 9 / 16)))

    def sizeHint(self) -> QSize:
        width = max(self.MIN_WIDTH, self.width())
        return QSize(width, self.heightForWidth(width))

    def minimumSizeHint(self) -> QSize:
        # Sem isso o QLabel usaria o tamanho do pixmap e impediria a janela de encolher.
        return QSize(self.MIN_WIDTH, self.MIN_HEIGHT)

    def has_image(self) -> bool:
        return self._source is not None

    def set_timecode(self, text: str):
        self._timecode = text or ""
        self.update()

    def set_source_pixmap(self, pixmap: QPixmap | None, fallback_text: str = PLACEHOLDER_THUMBNAIL):
        self._source = pixmap if pixmap is not None and not pixmap.isNull() else None
        self._fallback = fallback_text
        self.setText("" if self._source else fallback_text)
        self.update()

    def set_loading(self, loading: bool):
        self._loading = loading
        self._timer.start() if loading else self._timer.stop()
        self.update()

    def _tick(self):
        self._phase = (self._phase + 0.015) % 1.0
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = theme.RADIUS_CONTROL
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        p.setClipPath(path)
        p.fillRect(rect, QColor(theme.BG))

        if self._source is not None and not self._loading:
            src = self._source
            scale = max(rect.width() / src.width(), rect.height() / src.height())
            w, h = src.width() * scale, src.height() * scale
            p.drawPixmap(QRectF(rect.center().x() - w / 2, rect.center().y() - h / 2, w, h), src, QRectF(src.rect()))
            if self._timecode:
                self._paint_timecode(p, rect)
        elif self._loading:
            # Skeleton neutro enquanto os metadados chegam
            band = rect.width() * 0.5
            x = rect.left() - band + (rect.width() + band) * self._phase
            for i in range(24):
                alpha = int(10 * (1 - abs(i - 12) / 12))
                p.fillRect(QRectF(x + i * band / 24, rect.top(), band / 24 + 1, rect.height()), QColor(255, 255, 255, alpha))
            self._paint_caption(p, rect, "Buscando informações do vídeo", None)
        else:
            self._paint_caption(p, rect, self._fallback, "play")

        p.setClipping(False)
        p.setPen(QPen(QColor(237, 237, 237, 20), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)
        p.end()

    def _paint_timecode(self, p: QPainter, rect: QRectF):
        font = theme.mono_font(12, QFont.Weight.Medium)
        fm = QFontMetrics(font)
        w = fm.horizontalAdvance(self._timecode) + 12
        box = QRectF(rect.right() - w - 8, rect.bottom() - 20 - 8, w, 20)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(15, 15, 16, 210))
        p.drawRoundedRect(box, 4, 4)
        p.setFont(font)
        p.setPen(QColor(theme.TEXT))
        p.drawText(box, Qt.AlignmentFlag.AlignCenter, self._timecode)

    def _paint_caption(self, p: QPainter, rect: QRectF, text: str, icon_name: str | None):
        c = QPointF(rect.center().x(), rect.center().y() - (12 if icon_name else 0))
        if icon_name:
            p.setPen(QPen(QColor(237, 237, 237, 28), 1))
            p.setBrush(QColor(theme.SURFACE))
            p.drawEllipse(c, 20, 20)
            p.drawPixmap(QPointF(c.x() - 7, c.y() - 8), icons.pixmap(icon_name, theme.TEXT_3, 16))
        font = QFont(self.font())
        font.setPixelSize(13)
        p.setFont(font)
        p.setPen(QColor(theme.TEXT_3))
        top = c.y() + (32 if icon_name else -10)
        p.drawText(QRectF(rect.left() + 16, top, rect.width() - 32, 20), Qt.AlignmentFlag.AlignHCenter, text)


# ====================================================================== helpers
def _label(text: str, name: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName(name)
    return label


def _card() -> QFrame:
    card = QFrame()
    card.setObjectName("card")
    return card


def _hairline() -> QFrame:
    line = QFrame()
    line.setFixedHeight(1)
    line.setStyleSheet(f"background:{theme.HAIRLINE}; border:none;")
    return line


# ====================================================================== widget principal
class PreviewWidget(QWidget):
    """Tela principal: link, preview do vídeo, opções e progresso do download.

    A API pública (sinais e métodos ``set_*``/``get_*``) é a mesma usada pela
    MainWindow; os métodos extras são opcionais.
    """

    download_requested = Signal()
    preview_requested = Signal()
    cancel_requested = Signal()
    status_changed = Signal(str, str)  # texto, tipo (info | busy | success | error)

    WIDE_BREAKPOINT = 860

    def __init__(self, output_dir: str):
        super().__init__()
        self.output_dir = output_dir
        self._downloading = False
        self._build_ui()

    # ------------------------------------------------------------------ construção
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(0)

        title = _label("Novo download", "page_title")
        root.addWidget(title)
        root.addSpacing(8)
        root.addWidget(_label("Cole um link do YouTube e salve como vídeo MP4 ou áudio MP3", "subtitle"))
        root.addSpacing(24)
        root.addLayout(self._build_url_row())
        root.addSpacing(24)

        self.content_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.content_layout.setSpacing(16)
        self.content_layout.addWidget(self._build_preview_panel(), 3)
        self.content_layout.addWidget(self._build_download_panel(), 2)
        root.addLayout(self.content_layout)
        root.addStretch()

    def _build_url_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=")
        self.url_input.setFixedHeight(44)
        self.url_input.setClearButtonEnabled(True)
        self.url_input.addAction(
            QAction(icons.icon("link", theme.TEXT_3, 16), "", self.url_input),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        # Enter ou sair do campo apenas atualiza o preview; o download só começa pelo botão.
        self.url_input.editingFinished.connect(self.preview_requested)

        self.paste_button = QPushButton(" Colar")
        self.paste_button.setObjectName("secondary_button")
        self.paste_button.setIcon(icons.icon("paste", theme.TEXT_2, 16))
        self.paste_button.setIconSize(icons.icon_size(16))
        self.paste_button.setFixedHeight(44)
        self.paste_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.paste_button.setToolTip("Colar link da área de transferência")
        self.paste_button.clicked.connect(self.paste_from_clipboard)

        self.download_button = PrimaryButton("Baixar", "download")
        self.download_button.setObjectName("primary_button")
        self.download_button.setMinimumWidth(132)
        self.download_button.clicked.connect(self.download_requested)

        row.addWidget(self.url_input, 1)
        row.addWidget(self.paste_button)
        row.addWidget(self.download_button)
        return row

    def _build_preview_panel(self) -> QWidget:
        card = _card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        self.thumbnail_label = ThumbnailLabel(PLACEHOLDER_THUMBNAIL)
        self.thumbnail_label.setObjectName("thumbnailLabel")
        layout.addWidget(self.thumbnail_label)
        layout.addSpacing(16)

        self.video_title = QLabel(PLACEHOLDER_TITLE)
        self.video_title.setObjectName("videoTitle")
        self.video_title.setProperty("empty", True)
        self.video_title.setWordWrap(True)
        self.video_title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout.addWidget(self.video_title)
        layout.addSpacing(4)

        self.video_meta = _label("", "mono_meta")
        self.video_meta.setVisible(False)
        layout.addWidget(self.video_meta)
        layout.addStretch()
        return card

    def _build_download_panel(self) -> QWidget:
        card = _card()
        card.setMinimumWidth(300)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        layout.addWidget(_label("Formato", "field_label"))
        layout.addSpacing(8)
        self.format_select = SegmentedControl()
        for code, label in FORMAT_OPTIONS:
            short, icon_name = _FORMAT_SHORT.get(code, (label, None))
            self.format_select.addItem(short, code, icon_name)
        self.format_select.currentIndexChanged.connect(self._refresh_quality_options)
        layout.addWidget(self.format_select)
        layout.addSpacing(16)

        self.quality_label = _label("Resolução máxima", "field_label")
        layout.addWidget(self.quality_label)
        layout.addSpacing(8)
        self.quality_select = QComboBox()
        self.quality_select.setFixedHeight(40)
        self.quality_select.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.quality_select)
        self._refresh_quality_options()
        layout.addSpacing(12)

        # Vídeo detectado + FFmpeg: linhas de meta, discretas
        detected = QHBoxLayout()
        detected.setSpacing(8)
        self.detected_icon = QLabel()
        self.detected_icon.setFixedSize(16, 16)
        self.detected_label = _label("Nenhum vídeo detectado", "meta")
        self.detected_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        detected.addWidget(self.detected_icon)
        detected.addWidget(self.detected_label, 1)
        layout.addLayout(detected)
        layout.addSpacing(4)
        ffmpeg = QHBoxLayout()
        ffmpeg.setSpacing(8)
        self.ffmpeg_icon = QLabel()
        self.ffmpeg_icon.setFixedSize(16, 16)
        self.ffmpeg_label = _label("", "meta")
        ffmpeg.addWidget(self.ffmpeg_icon)
        ffmpeg.addWidget(self.ffmpeg_label, 1)
        layout.addLayout(ffmpeg)
        self._set_detected(None)

        layout.addSpacing(20)
        layout.addWidget(_hairline())
        layout.addSpacing(20)

        # Progresso: o número que importa fica em destaque, em mono
        top = QHBoxLayout()
        top.setSpacing(8)
        self.status_icon = QLabel()
        self.status_icon.setFixedSize(16, 16)
        self.status_label = QLabel("Pronto para começar")
        self.status_label.setObjectName("status_label")
        self.status_label.setWordWrap(True)
        self.status_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.status_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        top.addWidget(self.status_icon, 0, Qt.AlignmentFlag.AlignTop)
        top.addWidget(self.status_label, 1)
        layout.addLayout(top)

        self.percent_label = QLabel("")
        self.percent_label.setObjectName("percent_label")
        self.percent_label.setStyleSheet(
            f'color:{theme.ACCENT}; font-family:"{theme.MONO_FAMILY}"; font-size:28px; font-weight:500;'
        )
        self.percent_label.setVisible(False)
        layout.addSpacing(8)
        layout.addWidget(self.percent_label)
        layout.addSpacing(8)

        self.progress_bar = AnimatedProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        layout.addSpacing(8)

        meta = QHBoxLayout()
        meta.setSpacing(8)
        self.speed_label = _label("", "mono_meta")
        meta.addWidget(self.speed_label, 1)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setObjectName("danger_button")
        self.cancel_button.setFixedHeight(32)
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        meta.addWidget(self.cancel_button)
        layout.addLayout(meta)
        layout.addStretch()

        self._set_status_kind("info")
        return card

    # ------------------------------------------------------------------ responsividade
    def resizeEvent(self, event):
        super().resizeEvent(event)
        wide = self.width() >= self.WIDE_BREAKPOINT
        direction = QBoxLayout.Direction.LeftToRight if wide else QBoxLayout.Direction.TopToBottom
        if self.content_layout.direction() != direction:
            self.content_layout.setDirection(direction)

    # ------------------------------------------------------------------ estado auxiliar
    def _set_detected(self, info: VideoInfo | None, title: str | None = None):
        if info is None and not title:
            self.detected_icon.setPixmap(icons.pixmap("video", theme.TEXT_3, 16))
            self.detected_label.setText("Nenhum vídeo detectado")
            self.detected_label.setToolTip("")
            return
        self.detected_icon.setPixmap(icons.pixmap("check", theme.POSITIVE, 16))
        self.detected_label.setText("Vídeo detectado, pronto para baixar")
        self.detected_label.setToolTip(title or (info.title if info else ""))

    def _refresh_quality_options(self, *_):
        is_audio = self.get_format() == FORMAT_MP3
        previous = self.quality_select.currentData()
        options = AUDIO_QUALITY_OPTIONS if is_audio else VIDEO_QUALITY_OPTIONS
        self.quality_label.setText("Qualidade do áudio" if is_audio else "Resolução máxima")
        self.quality_select.blockSignals(True)
        self.quality_select.clear()
        for code, label in options:
            self.quality_select.addItem(label, code)
        index = self.quality_select.findData(previous)
        self.quality_select.setCurrentIndex(index if index >= 0 else 0)
        self.quality_select.blockSignals(False)

    def set_ffmpeg_available(self, available: bool):
        self.ffmpeg_icon.setPixmap(icons.pixmap("bolt", theme.TEXT_3, 16))
        self.ffmpeg_label.setText("FFmpeg encontrado" if available else "FFmpeg não encontrado, MP3 indisponível")
        self.ffmpeg_label.setStyleSheet("" if available else f"color:{theme.CAUTION};")
        self.ffmpeg_label.setToolTip(
            "Junção de vídeo e áudio e conversão para MP3 disponíveis"
            if available
            else "Instale o FFmpeg e adicione-o ao PATH para converter MP3 e baixar MP4 em alta resolução"
        )

    # ------------------------------------------------------------------ ações
    def paste_from_clipboard(self):
        text = (QGuiApplication.clipboard().text() or "").strip()
        if not text:
            self.set_status("A área de transferência está vazia", "error")
            return
        self.url_input.setText(text)
        self.url_input.setFocus()
        self.preview_requested.emit()

    def _on_cancel_clicked(self):
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText("Cancelando")
        self.cancel_requested.emit()

    # ------------------------------------------------------------------ API pública
    def set_status(self, text: str, kind: str | None = None):
        if kind is None:
            kind = "busy" if self._downloading else "info"
        main, _, details = text.partition(" · ")
        if self._downloading and main.startswith("Baixando"):
            # "Baixando... 42% · 3.2 MB/s · ETA 00:12"
            self.status_label.setText("Baixando")
            self.speed_label.setText(details.replace(" · ", "   "))
        else:
            self.status_label.setText(_display_text(text))
            if not self._downloading:
                self.speed_label.setText("")
        self._set_status_kind(kind)
        self.status_changed.emit(_display_text(text), kind)

    def _set_status_kind(self, kind: str):
        icon_by_kind = {
            "info": ("info", theme.TEXT_3),
            "busy": ("download", theme.TEXT_2),
            "success": ("check", theme.POSITIVE),
            "error": ("x", theme.NEGATIVE),
        }
        icon_name, color = icon_by_kind.get(kind, icon_by_kind["info"])
        text_color = theme.TEXT if kind in ("busy", "success", "error") else theme.TEXT_2
        self.status_label.setStyleSheet(f"color:{text_color}; font-size:14px;")
        self.status_icon.setPixmap(icons.pixmap(icon_name, color, 16))

    def set_progress_visible(self, visible: bool):
        self.progress_bar.setVisible(visible)
        self.progress_bar.set_busy(visible)
        self.percent_label.setVisible(visible)
        if not visible:
            self.percent_label.setText("")

    def set_progress(self, value: int):
        self.progress_bar.setValue(value)
        self.percent_label.setText(f"{value}%")

    def set_button_enabled(self, enabled: bool):
        self.download_button.setEnabled(enabled)

    def set_downloading(self, downloading: bool):
        """Estado visual de download em andamento (botão ocupado + cancelar)."""
        self._downloading = downloading
        self.download_button.set_loading(downloading, "Baixando" if downloading else "Baixar")
        self.cancel_button.setVisible(downloading)
        self.cancel_button.setEnabled(True)
        self.cancel_button.setText("Cancelar")
        self.format_select.setEnabled(not downloading)
        self.quality_select.setEnabled(not downloading)
        if not downloading:
            self.speed_label.setText("")

    def set_preview_loading(self, loading: bool):
        self.thumbnail_label.set_loading(loading)

    def set_video_info(self, title: str | None, thumbnail_path: str | None = None):
        self.thumbnail_label.set_loading(False)
        self.video_title.setText(title or PLACEHOLDER_TITLE)
        self.video_title.setProperty("empty", not title)
        self.video_title.style().unpolish(self.video_title)
        self.video_title.style().polish(self.video_title)
        if thumbnail_path:
            self.set_thumbnail(thumbnail_path)
        else:
            self.thumbnail_label.set_source_pixmap(None)
        if not title:
            self.video_meta.setVisible(False)
            self.thumbnail_label.set_timecode("")
        self._set_detected(None, title)

    def set_video_details(self, info: VideoInfo | None):
        """Exibe canal e duração (opcional, complementa ``set_video_info``)."""
        duration = format_duration(info.duration) if info else ""
        uploader = (info.uploader or "") if info else ""
        parts = [part for part in (uploader, duration) if part]
        self.video_meta.setText("  ·  ".join(parts))
        self.video_meta.setVisible(bool(parts))
        self.thumbnail_label.set_timecode(duration)
        self._set_detected(info, info.title if info else None)

    def clear_video_info(self):
        self.set_video_info(None, None)

    def set_thumbnail(self, image_path: str):
        """Show an image already on disk (downloads are done by PreviewWorker)."""
        self.thumbnail_label.set_source_pixmap(QPixmap(image_path), "Imagem indisponível")

    def get_url(self) -> str:
        return self.url_input.text().strip()

    def get_format(self) -> str:
        """Internal format code ("mp4" or "mp3")."""
        return self.format_select.currentData() or FORMAT_MP4

    def get_quality(self) -> str:
        """Altura máxima (MP4) ou bitrate (MP3); ``"best"`` mantém o padrão original."""
        return self.quality_select.currentData() or QUALITY_BEST
