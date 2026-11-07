from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QScrollArea, QVBoxLayout, QWidget

from app.ui.widgets.preview_widget import PreviewWidget


class HomePage(QWidget):
    download_requested = Signal()
    preview_requested = Signal()

    def __init__(self, output_dir: str):
        super().__init__()
        self.output_dir = output_dir
        self.preview_widget = PreviewWidget(output_dir)
        self.preview_widget.download_requested.connect(self.download_requested)
        self.preview_widget.preview_requested.connect(self.preview_requested)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        scroll.setWidget(self.preview_widget)
        layout.addWidget(scroll)
