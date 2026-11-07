
from pathlib import Path

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.services.youtube_service import YouTubeService
from app.workers.download_worker import DownloadWorker


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.output_dir = str(Path(__file__).resolve().parents[2] / "downloads")
        self.service = YouTubeService()
        self.worker = None
        self.worker_thread = None

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

        for name in ["Início", "Downloads", "Histórico", "Configurações"]:
            button = QPushButton(name)
            button.setObjectName("nav_button")
            sidebar_layout.addWidget(button)

        sidebar_layout.addStretch()

        version = QLabel("Version 0.1.0")
        version.setObjectName("version")
        sidebar_layout.addWidget(version)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 35, 40, 35)
        content_layout.setSpacing(18)

        title = QLabel("Baixe seus conteúdos.")
        title.setObjectName("title")

        subtitle = QLabel("Cole um link do YouTube para começar.")
        subtitle.setObjectName("subtitle")

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.url_input.setMinimumHeight(48)
        self.url_input.returnPressed.connect(self.handle_download)

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
        self.download_button.clicked.connect(self.handle_download)

        content_layout.addWidget(title)
        content_layout.addWidget(subtitle)
        content_layout.addSpacing(20)
        content_layout.addWidget(QLabel("URL DO CONTEÚDO"))
        content_layout.addWidget(self.url_input)
        content_layout.addWidget(QLabel("FORMATO"))
        content_layout.addWidget(self.format_select)
        content_layout.addWidget(self.progress_bar)
        content_layout.addWidget(self.status_label)
        content_layout.addWidget(self.download_button)

        content_layout.addSpacing(35)

        history_title = QLabel("Downloads recentes")
        history_title.setObjectName("section_title")

        content_layout.addWidget(history_title)
        content_layout.addStretch()

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content)

    def handle_download(self):
        if self.worker_thread is not None and self.worker_thread.isRunning():
            return

        url = self.url_input.text().strip()
        try:
            self.service.validate_url(url)
        except ValueError as exc:
            self.status_label.setText(str(exc))
            return

        self.status_label.setText("Preparando download...")
        self.download_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        self.worker = DownloadWorker(url, self.format_select.currentText(), self.output_dir)
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
        self.status_label.setText(message)

    def on_worker_progress(self, value: int, message: str):
        self.progress_bar.setValue(value)
        self.status_label.setText(message)

    def on_worker_finished(self, message: str):
        self.status_label.setText(message)
        self.progress_bar.setVisible(False)
        self.download_button.setEnabled(True)
        self.worker = None
        self.worker_thread = None

    def on_worker_error(self, message: str):
        self.status_label.setText(message)
        self.progress_bar.setVisible(False)
        self.download_button.setEnabled(True)
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
