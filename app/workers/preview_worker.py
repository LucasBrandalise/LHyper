from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from app.services.thumbnail_service import ThumbnailService
from app.services.youtube_service import YouTubeService


class PreviewWorker(QObject):
    """Fetches video metadata and thumbnail off the GUI thread.

    Signals carry the requested URL so the UI can discard stale results.
    """

    loaded = Signal(str, object, str)  # url, VideoInfo, caminho da thumbnail ("" se indisponível)
    failed = Signal(str, str)  # url, mensagem
    done = Signal()

    def __init__(
        self,
        url: str,
        job_id: int = 0,
        service: YouTubeService | None = None,
        thumbnails: ThumbnailService | None = None,
    ):
        super().__init__()
        self.url = url
        self.job_id = job_id
        self.service = service or YouTubeService()
        self.thumbnails = thumbnails or ThumbnailService()

    @Slot()
    def run(self):
        try:
            info = self.service.extract_info(self.url)
        except (ValueError, RuntimeError, OSError) as exc:
            self.failed.emit(self.url, str(exc))
        except Exception as exc:  # noqa: BLE001 - a thread não pode morrer sem avisar a UI
            self.failed.emit(self.url, f"Erro inesperado: {exc}")
        else:
            thumbnail_path = ""
            if info.thumbnail:
                try:
                    thumbnail_path = str(self.thumbnails.fetch(info.thumbnail))
                except (ValueError, OSError):
                    thumbnail_path = ""  # sem thumbnail o preview continua válido
            self.loaded.emit(self.url, info, thumbnail_path)
        finally:
            self.done.emit()
