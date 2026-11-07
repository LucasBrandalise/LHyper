from __future__ import annotations

import threading

from PySide6.QtCore import QObject, Signal, Slot

from app.core.models import VideoInfo
from app.services.youtube_service import DownloadCancelledError, YouTubeService


class DownloadWorker(QObject):
    """Runs a download in a background thread.

    Exactly one of ``completed`` / ``failed`` / ``cancelled`` is emitted, always
    followed by ``done``.
    """

    info_ready = Signal(object)  # VideoInfo
    progress = Signal(int, str)
    completed = Signal(str)  # caminho do arquivo final
    failed = Signal(str)
    cancelled = Signal()
    done = Signal()

    def __init__(
        self,
        url: str,
        output_format: str,
        output_dir: str,
        service: YouTubeService | None = None,
        quality: str | None = None,
    ):
        super().__init__()
        self.quality = quality
        self.url = url
        self.output_format = YouTubeService.normalize_format(output_format)
        self.output_dir = output_dir
        self.service = service or YouTubeService()
        self._cancel_event = threading.Event()

    def cancel(self):
        """Thread-safe: may be called from the GUI thread."""
        self._cancel_event.set()

    @Slot()
    def run(self):
        try:
            output_path = self.service.download_video(
                self.url,
                self.output_format,
                self.output_dir,
                progress_callback=self.progress.emit,
                info_callback=self._on_info,
                cancel_event=self._cancel_event,
                quality=self.quality,
            )
        except DownloadCancelledError:
            self.cancelled.emit()
        except (ValueError, RuntimeError, OSError) as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001 - a thread não pode morrer sem avisar a UI
            self.failed.emit(f"Erro inesperado: {exc}")
        else:
            self.completed.emit(output_path)
        finally:
            self.done.emit()

    def _on_info(self, info: VideoInfo):
        self.info_ready.emit(info)
