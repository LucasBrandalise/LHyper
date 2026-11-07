
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QFrame,
)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

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

        # Sidebar
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

        # Main content
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 35, 40, 35)
        content_layout.setSpacing(18)

        title = QLabel("Baixe seus conteúdos.")
        title.setObjectName("title")

        subtitle = QLabel(
            "Cole um link do YouTube para começar."
        )
        subtitle.setObjectName("subtitle")

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(
            "https://www.youtube.com/watch?v=..."
        )
        self.url_input.setMinimumHeight(48)

        self.format_select = QComboBox()
        self.format_select.addItems(["MP4 - Vídeo", "MP3 - Áudio"])
        self.format_select.setMinimumHeight(42)

        self.download_button = QPushButton("Analisar conteúdo")
        self.download_button.setObjectName("primary_button")
        self.download_button.setMinimumHeight(48)

        content_layout.addWidget(title)
        content_layout.addWidget(subtitle)
        content_layout.addSpacing(20)
        content_layout.addWidget(QLabel("URL DO CONTEÚDO"))
        content_layout.addWidget(self.url_input)
        content_layout.addWidget(QLabel("FORMATO"))
        content_layout.addWidget(self.format_select)
        content_layout.addWidget(self.download_button)

        content_layout.addSpacing(35)

        history_title = QLabel("Downloads recentes")
        history_title.setObjectName("section_title")

        content_layout.addWidget(history_title)
        content_layout.addStretch()

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content)

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

            QLineEdit, QComboBox {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 10px;
                color: white;
            }

            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #3B82F6;
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
        """)
