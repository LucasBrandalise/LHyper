
from pathlib import Path

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.models import DownloadRecord
from app.database.download_repository import DownloadRepository
from app.services.youtube_service import YouTubeService
from app.ui.tabs.downloads_tab import DownloadsTab
from app.ui.tabs.preview_tab import PreviewTab
from app.workers.download_worker import DownloadWorker


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.output_dir = str(Path(__file__).resolve().parents[2] / "downloads")
        self.service = YouTubeService()
        self.repository = DownloadRepository()
        self.repository.sync_from_disk(self.output_dir)
        self.worker = None
        self.worker_thread = None
        self.current_download_title = ""
        self.current_download_url = ""
        self.current_download_format = "mp4"

        self.preview_tab = PreviewTab(self.output_dir)
        self.downloads_tab = DownloadsTab(self.output_dir, self.repository)

        self.setWindowTitle("YT Downloader")
        self.resize(1100, 720)
        self.setMinimumSize(850, 600)

        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)

        sidebar_layout = QVBoxLayout(sidebar)
        logo = QLabel("YT Downloader")
        logo.setObjectName("logo")
        sidebar_layout.addWidget(logo)
        sidebar_layout.addSpacing(30)

        nav_items = ["Início", "Downloads", "Histórico", "Configurações"]
        for name in nav_items:
            button = QPushButton(name)
            button.setObjectName("nav_button")
            if name == "Início":
                button.clicked.connect(lambda checked, idx=0: self.tab_widget.setCurrentIndex(idx))
            elif name == "Downloads":
                button.clicked.connect(lambda checked, idx=1: self.tab_widget.setCurrentIndex(idx))
            sidebar_layout.addWidget(button)

        sidebar_layout.addStretch()

        version = QLabel("Version 0.2.0")
        version.setObjectName("version")
        sidebar_layout.addWidget(version)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabBarAutoHide(False)
        self.tab_widget.addTab(self.preview_tab, "Preview")
        self.tab_widget.addTab(self.downloads_tab, "Downloads")

        self.preview_tab.download_requested.connect(self.handle_download)
        self.preview_tab.url_input.editingFinished.connect(self.refresh_preview_from_url)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.tab_widget)

    def refresh_preview_from_url(self):
        url = self.preview_tab.get_url()
        try:
            info = self.service.extract_info(url)
            self.preview_tab.set_video_info(info.title, info.thumbnail)
            self.current_download_title = info.title
            self.current_download_url = url
            self.current_download_format = self.preview_tab.get_format().split(" - ", 1)[0].lower()
            self.preview_tab.set_status("Preview atualizado.")
        except ValueError as exc:
            self.preview_tab.set_status(str(exc))
        except Exception as exc:
            self.preview_tab.set_status(str(exc))

    def handle_download(self):
        if self.worker_thread is not None and self.worker_thread.isRunning():
            return

        url = self.preview_tab.get_url()
        try:
            self.service.validate_url(url)
            info = self.service.extract_info(url)
            self.preview_tab.set_video_info(info.title, info.thumbnail)
            self.current_download_title = info.title
            self.current_download_url = url
            self.current_download_format = self.preview_tab.get_format().split(" - ", 1)[0].lower()
        except ValueError as exc:
            self.preview_tab.set_status(str(exc))
            return
        except Exception as exc:
            self.preview_tab.set_status(str(exc))
            return

        self.preview_tab.set_status("Preparando download...")
        self.preview_tab.set_button_enabled(False)
        self.preview_tab.set_progress(0)
        self.preview_tab.set_progress_visible(True)

        self.worker = DownloadWorker(url, self.preview_tab.get_format(), self.output_dir)
        self.worker_thread = QThread(self)

        self.worker.started.connect(self.on_worker_started)
        self.worker.progress.connect(self.on_worker_progress)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.error.connect(self.on_worker_error)

        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.error.connect(self.worker_thread.quit)

        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.worker_thread.start()

    def on_worker_started(self, message: str):
        self.preview_tab.set_status(message)

    def on_worker_progress(self, value: int, message: str):
        self.preview_tab.set_progress(value)
        self.preview_tab.set_status(message)

    def on_worker_finished(self, message: str):
        self.preview_tab.set_status(message)
        self.preview_tab.set_progress_visible(False)
        self.preview_tab.set_button_enabled(True)

        if self.worker and getattr(self.worker, "output_path", ""):
            file_path = self.worker.output_path
            file_size = Path(file_path).stat().st_size if Path(file_path).exists() else 0
            record = DownloadRecord(
                id=None,
                title=self.current_download_title or Path(file_path).stem,
                url=self.current_download_url,
                thumbnail=None,
                file_path=file_path,
                file_size=file_size,
                file_format=self.current_download_format,
                status="completed",
                created_at=None,
                updated_at=None,
                error_message=None,
            )
            self.repository.add_or_update(record)

        self.downloads_tab.refresh()
        self.worker = None
        self.worker_thread = None

    def on_worker_error(self, message: str):
        self.preview_tab.set_status(message)
        self.preview_tab.set_progress_visible(False)
        self.preview_tab.set_button_enabled(True)

        if self.current_download_url:
            record = DownloadRecord(
                id=None,
                title=self.current_download_title or "Erro no download",
                url=self.current_download_url,
                thumbnail=None,
                file_path="",
                file_size=0,
                file_format=self.current_download_format,
                status="error",
                created_at=None,
                updated_at=None,
                error_message=message,
            )
            self.repository.add_or_update(record)

        self.downloads_tab.refresh()
        self.worker = None
        self.worker_thread = None

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #111827;
                color: #F9FAFB;
                font-family: Segoe UI;
                font-size: 14px;
            }

            #sidebar {
                background-color: #0B1220;
                border-right: 1px solid #263244;
            }

            #logo {
                font-size: 21px;
                font-weight: bold;
                color: white;
            }

            #nav_button {
                text-align: left;
                padding: 13px;
                border: none;
                border-radius: 7px;
                color: #AAB5C5;
            }

            #nav_button:hover {
                background-color: #1E293B;
                color: white;
            }

            #version {
                color: #64748B;
                font-size: 11px;
            }

            #title {
                font-size: 30px;
                font-weight: bold;
            }

            #subtitle {
                color: #94A3B8;
            }

            #section_title {
                font-size: 19px;
                font-weight: bold;
            }

            QTabWidget::pane {
                border: none;
                background: transparent;
            }

            QTabBar::tab {
                background: #0B1220;
                color: #AAB5C5;
                padding: 10px 18px;
                border: 1px solid #263244;
                border-bottom: none;
                margin-right: 4px;
            }

            QTabBar::tab:selected {
                background: #111827;
                color: white;
                border-bottom: 2px solid #2563EB;
            }

            QLineEdit, QComboBox, QProgressBar {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 10px;
                color: white;
            }

            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #3B82F6;
            }

            #status_label {
                color: #A5F3FC;
                padding-top: 4px;
            }

            #primary_button {
                background-color: #2563EB;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                color: white;
            }

            #primary_button:hover {
                background-color: #1D4ED8;
            }

            #primary_button:disabled {
                background-color: #374151;
                color: #94A3B8;
            }
        """)
