from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import sys
from datetime import datetime

from PySide6.QtCore import QObject, Qt, QThread, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.core.constants import APP_TITLE, APP_VERSION, STATUS_COMPLETED, STATUS_ERROR, VERSION_LABEL
from app.core.models import DownloadRecord, VideoInfo
from app.core.paths import downloads_dir
from app.database.download_repository import DownloadRepository
from app.services.youtube_service import YouTubeService
from app.ui.components import icons
from app.ui.components.controls import FadeStackedWidget, LogoMark, StatusDot
from app.ui.pages.downloads_page import DownloadsPage
from app.ui.pages.home_page import HomePage
from app.ui.pages.settings_page import SettingsPage
from app.ui.styles import theme
from app.workers.download_worker import DownloadWorker
from app.workers.preview_worker import PreviewWorker


def _apply_dark_title_bar(window: QWidget):
    """Barra de título escura no Windows 10/11 (sem efeito em outros sistemas)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        hwnd = int(window.winId())
        dwm = ctypes.windll.dwmapi
        value = ctypes.c_int(1)
        for attribute in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (novo / antigo)
            if dwm.DwmSetWindowAttribute(hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)) == 0:
                break
        caption = ctypes.c_int(0x000B0B0B)  # COLORREF 0x00BBGGRR -> #0B0B0B (Windows 11)
        dwm.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(caption), ctypes.sizeof(caption))
    except Exception:  # noqa: BLE001 - puramente cosmético
        pass


class MainWindow(QMainWindow):

    def __init__(self, repository: DownloadRepository | None = None, output_dir: str | Path | None = None):
        super().__init__()

        self.output_dir = str(Path(output_dir) if output_dir is not None else downloads_dir())
        self.repository = repository or DownloadRepository()

        self.download_worker: DownloadWorker | None = None
        self.download_thread: QThread | None = None
        self._download_url = ""
        self._download_format = ""
        self._download_info: VideoInfo | None = None

        # Previews ativos: job_id -> (thread, worker). O worker não tem pai Qt, então a
        # referência Python precisa ser mantida até o fim, senão o GC destrói o objeto C++.
        self._preview_jobs: dict[int, tuple[QThread, PreviewWorker]] = {}
        self._next_preview_id = 0
        self._previewed_url = ""
        self._preview_info: VideoInfo | None = None

        theme.load_fonts()

        self.home_page = HomePage(self.output_dir)
        self.downloads_page = DownloadsPage(self.output_dir, self.repository)
        self.settings_page = SettingsPage(self.output_dir)
        self.preview = self.home_page.preview_widget
        self.preview.set_ffmpeg_available(YouTubeService.ffmpeg_available())

        self.setWindowTitle(APP_TITLE)
        self.setWindowIcon(QIcon(theme.app_icon_path()))
        self.resize(1200, 800)
        self.setMinimumSize(860, 620)

        self.setup_ui()
        self.apply_styles()
        _apply_dark_title_bar(self)

    # ------------------------------------------------------------------ layout
    def setup_ui(self):
        central = QWidget()
        central.setObjectName("root")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.stacked_widget = FadeStackedWidget()
        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.downloads_page)
        self.stacked_widget.addWidget(self.settings_page)

        main_layout.addWidget(self._build_header())
        main_layout.addWidget(self.stacked_widget, 1)
        main_layout.addWidget(self._build_footer())

        self.nav_group.idClicked.connect(self.stacked_widget.setCurrentIndex)
        self.nav_group.button(0).setChecked(True)
        self.stacked_widget.setCurrentIndex(0)

        self.home_page.download_requested.connect(self.handle_download)
        self.home_page.preview_requested.connect(self.refresh_preview_from_url)
        self.preview.cancel_requested.connect(self.cancel_download)
        self.preview.status_changed.connect(self._on_status_changed)
        self.downloads_page.count_changed.connect(self._on_download_count)
        self.downloads_page.refresh()
        self.preview.url_input.setFocus()

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(56)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(8)

        layout.addWidget(LogoMark(32))
        logo = QLabel(APP_TITLE)
        logo.setObjectName("wordmark")
        layout.addWidget(logo)
        layout.addSpacing(32)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons: list[QPushButton] = []
        self._nav_icons = ("home", "download", "settings")
        for index, name in enumerate(["Início", "Downloads", "Configurações"]):
            button = QPushButton(f" {name}")
            button.setObjectName("nav_button")
            button.setCheckable(True)
            button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setIcon(icons.icon(self._nav_icons[index], theme.TEXT_3, 16))
            button.setIconSize(icons.icon_size(16))
            button.setFixedHeight(32)
            self.nav_group.addButton(button, index)
            self.nav_buttons.append(button)
            layout.addWidget(button)
        self.nav_group.idToggled.connect(self._on_nav_toggled)

        layout.addStretch()

        self.header_dot = StatusDot(8)
        self.header_status = QLabel("Pronto")
        self.header_status.setObjectName("footer_text")
        layout.addWidget(self.header_dot)
        layout.addWidget(self.header_status)
        return header

    def _on_nav_toggled(self, index: int, checked: bool):
        color = theme.TEXT_2 if checked else theme.TEXT_3
        self.nav_buttons[index].setIcon(icons.icon(self._nav_icons[index], color, 16))

    def _build_footer(self) -> QWidget:
        footer = QFrame()
        footer.setObjectName("footer")
        footer.setFixedHeight(32)
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(24, 0, 16, 0)
        layout.setSpacing(8)

        self.footer_dot = StatusDot(6)
        self.footer_dot.setVisible(False)  # o ponto vive no cabeçalho; o rodapé só traz o texto
        self.footer_status = QLabel("Pronto")
        self.footer_status.setObjectName("footer_text")
        self.footer_status.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.footer_status, 1)

        self.footer_activity = QLabel("")
        self.footer_activity.setObjectName("footer_mono")
        self.footer_activity.setToolTip("Última atividade")
        layout.addWidget(self.footer_activity)
        layout.addSpacing(8)

        self.footer_downloads = QPushButton("Downloads")
        self.footer_downloads.setObjectName("footer_link")
        self.footer_downloads.setCursor(Qt.CursorShape.PointingHandCursor)
        self.footer_downloads.clicked.connect(lambda: self.nav_group.button(1).click())
        layout.addWidget(self.footer_downloads)

        folder = QPushButton("Abrir pasta")
        folder.setObjectName("footer_link")
        folder.setCursor(Qt.CursorShape.PointingHandCursor)
        folder.clicked.connect(self.open_downloads_folder)
        layout.addWidget(folder)

        version = QLabel(f"v{APP_VERSION}")
        version.setObjectName("footer_mono")
        version.setToolTip(VERSION_LABEL)
        layout.addSpacing(8)
        layout.addWidget(version)
        return footer

    # ------------------------------------------------------------------ status visual
    def _on_status_changed(self, text: str, kind: str):
        self.footer_status.setText(text)
        self.footer_status.setToolTip(text)
        dot = {"busy": "busy", "error": "error", "success": "success"}.get(kind, "idle")
        self.footer_dot.set_state(dot)
        self.header_dot.set_state(dot)
        self.header_status.setText(
            {"busy": "Baixando", "error": "Erro", "success": "Concluído"}.get(kind, "Pronto")
        )
        self.footer_activity.setText(datetime.now().strftime("%H:%M:%S"))

    def _on_download_count(self, count: int):
        self.footer_downloads.setText(f"Downloads  {count}")

    def open_downloads_folder(self):
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.output_dir))

    # ------------------------------------------------------------------ threads
    def _start_in_thread(self, worker: QObject, on_finished: Callable[[], None]) -> QThread:
        """Move ``worker`` to a new QThread and start it.

        The worker must expose ``run()`` and a ``done`` signal emitted at the end.
        ``on_finished`` (a method of this window, so it runs on the GUI thread) is called
        after the thread stops; it must drop the Python reference to the worker, which is
        what frees it. ``deleteLater`` is deliberately not used on the worker: combined with
        the Python reference it could destroy the object twice from different threads.
        """
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.done.connect(thread.quit)
        thread.finished.connect(on_finished)
        thread.finished.connect(thread.deleteLater)
        thread.start()
        return thread

    # ------------------------------------------------------------------ preview
    def refresh_preview_from_url(self):
        url = self.preview.get_url()
        if url == self._previewed_url:
            return  # editingFinished também dispara ao perder o foco sem alterações
        self._previewed_url = url
        self._preview_info = None

        if not url:
            self.preview.clear_video_info()
            self.preview.set_status("Pronto para começar.")
            return

        try:
            YouTubeService.validate_url(url)
        except ValueError as exc:
            self.preview.clear_video_info()
            self.preview.set_status(str(exc), "error")
            return

        self.preview.set_status("Carregando preview...")
        self.preview.set_preview_loading(True)
        self._next_preview_id += 1
        worker = PreviewWorker(url, job_id=self._next_preview_id)
        worker.loaded.connect(self.on_preview_loaded)
        worker.failed.connect(self.on_preview_failed)
        thread = self._start_in_thread(worker, self._reap_preview_jobs)
        self._preview_jobs[worker.job_id] = (thread, worker)

    def _reap_preview_jobs(self):
        """Forget finished preview jobs (runs on the GUI thread)."""
        for job_id, (thread, _worker) in list(self._preview_jobs.items()):
            if thread.isFinished():
                del self._preview_jobs[job_id]

    def _is_current_preview(self, url: str) -> bool:
        return url == self._previewed_url == self.preview.get_url()

    def on_preview_loaded(self, url: str, info: VideoInfo, thumbnail_path: str):
        if not self._is_current_preview(url):
            return  # resultado de uma URL que o usuário já trocou
        self._preview_info = info
        self.preview.set_video_info(info.title, thumbnail_path or None)
        self.preview.set_video_details(info)
        if not self._download_running():
            self.preview.set_status("Preview atualizado.")

    def on_preview_failed(self, url: str, message: str):
        if not self._is_current_preview(url):
            return
        self.preview.clear_video_info()
        if not self._download_running():
            self.preview.set_status(message, "error")

    # ------------------------------------------------------------------ download
    def _download_running(self) -> bool:
        return self.download_thread is not None

    def handle_download(self):
        if self._download_running():
            return

        url = self.preview.get_url()
        try:
            YouTubeService.validate_url(url)
        except ValueError as exc:
            self.preview.set_status(str(exc), "error")
            return

        self._download_url = url
        self._download_format = self.preview.get_format()
        self._download_info = self._preview_info if self._previewed_url == url else None

        self.preview.set_downloading(True)
        self.preview.set_status("Preparando download...")
        self.preview.set_button_enabled(False)
        self.preview.set_progress(0)
        self.preview.set_progress_visible(True)

        worker = DownloadWorker(url, self._download_format, self.output_dir, quality=self.preview.get_quality())
        worker.info_ready.connect(self.on_download_info)
        worker.progress.connect(self.on_download_progress)
        worker.completed.connect(self.on_download_completed)
        worker.failed.connect(self.on_download_failed)
        worker.cancelled.connect(self.on_download_cancelled)

        self.download_worker = worker
        self.download_thread = self._start_in_thread(worker, self.on_download_thread_finished)

    def on_download_info(self, info: VideoInfo):
        self._download_info = info
        self.preview.set_status(f"Preparando: {info.title}")

    def on_download_progress(self, value: int, message: str):
        self.preview.set_progress(value)
        self.preview.set_status(message)

    def on_download_completed(self, file_path: str):
        path = Path(file_path)
        info = self._download_info
        self.repository.add_or_update(
            DownloadRecord(
                id=None,
                title=info.title if info else path.stem,
                url=self._download_url,
                thumbnail=info.thumbnail if info else None,
                file_path=str(path),
                file_size=path.stat().st_size if path.is_file() else 0,
                file_format=path.suffix.lower().lstrip(".") or self._download_format,
                status=STATUS_COMPLETED,
            )
        )
        self.preview.set_status(f"Download concluído: {path}", "success")

    def on_download_failed(self, message: str):
        info = self._download_info
        self.repository.add(
            DownloadRecord(
                id=None,
                title=info.title if info else self._download_url,
                url=self._download_url,
                thumbnail=info.thumbnail if info else None,
                file_path="",
                file_size=0,
                file_format=self._download_format,
                status=STATUS_ERROR,
                error_message=message,
            )
        )
        self.preview.set_status(message, "error")

    def on_download_cancelled(self):
        self.preview.set_status("Download cancelado.", "info")

    def cancel_download(self):
        if self.download_worker is not None:
            self.download_worker.cancel()

    def on_download_thread_finished(self):
        self.preview.set_downloading(False)
        self.preview.set_progress_visible(False)
        self.preview.set_button_enabled(True)
        self.download_worker = None
        self.download_thread = None
        self._download_info = None
        self.downloads_page.refresh()

    # ------------------------------------------------------------------ encerramento
    def closeEvent(self, event):
        # Destruir uma QThread em execução derruba o processo; cancela e aguarda antes de sair.
        if self.download_worker is not None:
            self.download_worker.cancel()
        threads = [thread for thread, _worker in self._preview_jobs.values()]
        if self.download_thread is not None:
            threads.append(self.download_thread)
        if threads:
            self.hide()
            for thread in threads:
                thread.quit()
                thread.wait()
        super().closeEvent(event)

    # ------------------------------------------------------------------ estilo
    def apply_styles(self):
        self.setStyleSheet(theme.stylesheet())
