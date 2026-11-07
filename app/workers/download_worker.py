from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from app.services.youtube_service import YouTubeService


class DownloadWorker(QObject):
    started = Signal(str)
    progress = Signal(int, str)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, url: str, output_format: str, output_dir: str):
        super().__init__()
        self.url = url
        self.output_format = self._normalize_format(output_format)
        self.output_dir = output_dir
        self.output_path = ""
        self.service = YouTubeService()

    @staticmethod
    def _normalize_format(output_format: str) -> str:
        text = (output_format or "").strip().lower()
        if text.startswith("mp3"):
            return "mp3"
        if text.startswith("mp4"):
            return "mp4"
        return "mp4" if "video" in text else "mp3"

    @Slot()
    def run(self):
        try:
            info = self.service.extract_info(self.url)
            self.started.emit(f"Preparando: {info.title}")
            output_path = self.service.download_video(
                self.url,
                self.output_format,
                self.output_dir,
                progress_callback=self._on_progress,
            )
            self.output_path = output_path
            self.finished.emit(f"Download concluído: {output_path}")
        except Exception as exc:  # pragma: no cover - handled by caller
            self.output_path = ""
            self.error.emit(str(exc))

    def _on_progress(self, percent: int, message: str):
        self.progress.emit(percent, message)
