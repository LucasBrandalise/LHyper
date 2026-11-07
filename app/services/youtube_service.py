from __future__ import annotations

import re
import shutil
import threading
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import urlsplit

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadCancelled, YoutubeDLError

from app.core.constants import FORMAT_MP3, FORMAT_MP4, QUALITY_BEST
from app.core.models import VideoInfo

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

ProgressCallback =Callable[[int, str], None]
InfoCallback = Callable[[VideoInfo], None]


class DownloadCancelledError(Exception):
    """Raised when a download is cancelled by the user."""


class YouTubeService:
    """Serviço para validar URLs, obter metadados e realizar downloads via yt-dlp."""

    YOUTUBE_DOMAINS = ("youtube.com", "youtu.be")
    SOCKET_TIMEOUT = 20

    # ------------------------------------------------------------------ validação
    @staticmethod
    def validate_url(url: str) -> str:
        value = (url or "").strip()
        if not value:
            raise ValueError("Informe uma URL válida.")

        parts = urlsplit(value)
        if parts.scheme.lower() not in ("http", "https"):
            raise ValueError("A URL deve começar com http:// ou https://")

        host = (parts.hostname or "").lower()
        if not any(host == domain or host.endswith(f".{domain}") for domain in YouTubeService.YOUTUBE_DOMAINS):
            raise ValueError("A URL deve apontar para um vídeo do YouTube.")

        return value

    @staticmethod
    def normalize_format(output_format: str) -> str:
        text = (output_format or "").strip().lower()
        if text.startswith(FORMAT_MP3) or "áudio" in text or "audio" in text:
            return FORMAT_MP3
        return FORMAT_MP4

    @staticmethod
    def ffmpeg_available() -> bool:
        return shutil.which("ffmpeg") is not None

    # ------------------------------------------------------------------ opções
    @classmethod
    def _base_options(cls) -> dict[str, Any]:
        return {
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,  # o progresso vai para a UI via progress_hooks, não para o console
            "noplaylist": True,
            "socket_timeout": cls.SOCKET_TIMEOUT,
            "retries": 3,
        }

    @classmethod
    def build_download_options(
        cls,
        output_format: str,
        output_dir: str | Path,
        ffmpeg_available: bool | None = None,
        quality: str | None = None,
    ) -> dict[str, Any]:
        """``quality``: altura máxima do vídeo (ex.: "1080") ou bitrate do MP3 (ex.: "320").

        ``None`` ou ``"best"`` preserva o comportamento padrão (melhor qualidade disponível).
        """
        quality = (quality or QUALITY_BEST).strip().lower()
        height = int(quality) if quality.isdigit() else None
        if ffmpeg_available is None:
            ffmpeg_available = cls.ffmpeg_available()

        options = cls._base_options()
        options.update(
            {
                # O yt-dlp sanitiza o título; windowsfilenames garante nomes válidos no Windows.
                "outtmpl": "%(title)s.%(ext)s",
                "paths": {"home": str(Path(output_dir))},
                "windowsfilenames": True,
            }
        )

        if cls.normalize_format(output_format) == FORMAT_MP3:
            if not ffmpeg_available:
                raise RuntimeError("FFmpeg não encontrado. Instale o FFmpeg para converter para MP3.")
            options["format"] = "bestaudio/best"
            options["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": quality if quality.isdigit() else "0",
                }
            ]
        elif ffmpeg_available:
            if height:
                options["format"] = (
                    f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]"
                    f"/best[height<={height}][ext=mp4]/best[height<={height}]/best"
                )
            else:
                options["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
            options["merge_output_format"] = "mp4"
        else:
            # Sem FFmpeg não é possível juntar vídeo e áudio separados.
            if height:
                options["format"] = f"best[height<={height}][ext=mp4]/best[height<={height}]/best[ext=mp4]/best"
            else:
                options["format"] = "best[ext=mp4]/best"

        return options

    # ------------------------------------------------------------------ metadados
    @staticmethod
    def _to_video_info(info: dict[str, Any], url: str) -> VideoInfo:
        return VideoInfo(
            title=info.get("title") or "Vídeo do YouTube",
            url=url,
            thumbnail=info.get("thumbnail"),
            duration=info.get("duration"),
            uploader=info.get("uploader"),
        )

    @staticmethod
    def _single_entry(info: dict[str, Any] | None) -> dict[str, Any]:
        if not info:
            raise RuntimeError("Não foi possível obter informações do vídeo.")
        if info.get("_type") == "playlist" or "entries" in info:
            entries = [entry for entry in (info.get("entries") or []) if entry]
            if not entries:
                raise RuntimeError("Nenhum vídeo encontrado nesta URL.")
            return entries[0]
        return info

    @staticmethod
    def _error_message(exc: Exception) -> str:
        message = str(exc).strip()
        if message.startswith("ERROR: "):
            message = message[len("ERROR: "):]
        return message or exc.__class__.__name__

    @classmethod
    def extract_info(cls, url: str) -> VideoInfo:
        cleaned_url = cls.validate_url(url)
        options = cls._base_options()
        options["skip_download"] = True

        try:
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(cleaned_url, download=False)
        except YoutubeDLError as exc:
            raise RuntimeError(f"Não foi possível obter informações do vídeo: {cls._error_message(exc)}") from exc

        return cls._to_video_info(cls._single_entry(info), cleaned_url)

    # ------------------------------------------------------------------ download
    @classmethod
    def download_video(
        cls,
        url: str,
        output_format: str,
        output_dir: str | Path,
        progress_callback: Optional[ProgressCallback] = None,
        info_callback: Optional[InfoCallback] = None,
        cancel_event: Optional[threading.Event] = None,
        quality: Optional[str] = None,
    ) -> str:
        """Download ``url`` and return the absolute path of the final file.

        Metadata is extracted only once and reused for the download.
        """
        cleaned_url = cls.validate_url(url)
        target_dir = Path(output_dir).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)

        options = cls.build_download_options(output_format, target_dir, quality=quality)

        def progress_hook(data: dict[str, Any]):
            if cancel_event is not None and cancel_event.is_set():
                raise DownloadCancelled()
            if progress_callback is None:
                return
            status = data.get("status")
            if status == "downloading":
                percent = cls._compute_percent(data)
                if percent is not None:
                    progress_callback(percent, f"Baixando... {percent}%" + cls._transfer_details(data))
            elif status == "finished":
                progress_callback(100, "Finalizando arquivo...")

        options["progress_hooks"] = [progress_hook]

        try:
            with YoutubeDL(options) as ydl:
                info = cls._single_entry(ydl.extract_info(cleaned_url, download=False))
                if info_callback is not None:
                    info_callback(cls._to_video_info(info, cleaned_url))
                if cancel_event is not None and cancel_event.is_set():
                    raise DownloadCancelled()
                result = ydl.process_ie_result(info, download=True)
                output_path = cls._resolve_output_path(ydl, result or info)
        except DownloadCancelled as exc:
            raise DownloadCancelledError("Download cancelado.") from exc
        except YoutubeDLError as exc:
            raise RuntimeError(f"Falha ao baixar o conteúdo: {cls._error_message(exc)}") from exc

        if not Path(output_path).is_file():
            raise RuntimeError("O download terminou, mas o arquivo final não foi encontrado.")
        return output_path

    @staticmethod
    def _resolve_output_path(ydl: YoutubeDL, info: dict[str, Any]) -> str:
        for download in info.get("requested_downloads") or []:
            path = download.get("filepath")
            if path:
                return str(Path(path).resolve())
        if info.get("filepath"):
            return str(Path(info["filepath"]).resolve())
        return str(Path(ydl.prepare_filename(info)).resolve())

    @staticmethod
    def _transfer_details(data: dict[str, Any]) -> str:
        """Sufixo informativo " · 3.2 MB/s · ETA 00:12" (vazio se o yt-dlp não informar)."""
        parts = []
        speed = data.get("speed")
        if speed:
            size = float(speed)
            for unit in ("B/s", "KB/s", "MB/s", "GB/s"):
                if size < 1024 or unit == "GB/s":
                    break
                size /= 1024
            parts.append(f"{size:.1f} {unit}")
        eta = data.get("eta")
        if eta is not None:
            try:
                minutes, seconds = divmod(int(eta), 60)
                hours, minutes = divmod(minutes, 60)
                parts.append(f"ETA {hours}:{minutes:02d}:{seconds:02d}" if hours else f"ETA {minutes:02d}:{seconds:02d}")
            except (TypeError, ValueError):
                pass
        return "".join(f" · {part}" for part in parts)

    @staticmethod
    def _compute_percent(data: dict[str, Any]) -> Optional[int]:
        total = data.get("total_bytes") or data.get("total_bytes_estimate")
        downloaded = data.get("downloaded_bytes")
        if total and downloaded is not None:
            return min(max(int(downloaded * 100 / total), 0), 100)
        return YouTubeService._parse_percent(data.get("_percent_str"))

    @staticmethod
    def _parse_percent(value: Optional[str]) -> Optional[int]:
        if not value:
            return None

        # _percent_str pode vir com códigos de cor ANSI, ex.: "\x1b[0;94m 42.0%\x1b[0m".
        text = _ANSI_ESCAPE.sub("", str(value)).strip().rstrip("%").strip().replace(",", ".")
        try:
            percent = float(text)
        except ValueError:
            return None
        return min(max(int(percent), 0), 100)
