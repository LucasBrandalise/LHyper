from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Optional

from yt_dlp import YoutubeDL

from app.core.models import VideoInfo


class YouTubeService:
    """Serviço para validar URLs e realizar downloads via yt-dlp."""

    YOUTUBE_HOSTS = ("youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com")

    @staticmethod
    def validate_url(url: str) -> str:
        value = (url or "").strip()
        if not value:
            raise ValueError("Informe uma URL válida.")

        if not re.match(r"^https?://", value):
            raise ValueError("A URL deve começar com http:// ou https://")

        host = re.sub(r"^https?://", "", value).split("/", 1)[0].lower()
        if host not in YouTubeService.YOUTUBE_HOSTS and not any(
            host.endswith(f".{domain}") for domain in ("youtube.com", "youtu.be")
        ):
            raise ValueError("A URL deve apontar para um vídeo do YouTube.")

        return value

    @staticmethod
    def extract_info(url: str) -> VideoInfo:
        cleaned_url = YouTubeService.validate_url(url)
        options = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "skip_download": True,
            "extract_flat": False,
        }

        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(cleaned_url, download=False)

        if not info:
            raise RuntimeError("Não foi possível obter informações do vídeo.")

        if "entries" in info and info["entries"]:
            info = info["entries"][0]

        return VideoInfo(
            title=info.get("title") or "Vídeo do YouTube",
            url=cleaned_url,
            thumbnail=info.get("thumbnail"),
            duration=info.get("duration"),
            uploader=info.get("uploader"),
        )

    @staticmethod
    def download_video(
        url: str,
        output_format: str,
        output_dir: str,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> str:
        cleaned_url = YouTubeService.validate_url(url)
        target_dir = Path(output_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        info = YouTubeService.extract_info(cleaned_url)
        safe_title = re.sub(r"[\\/:*?\"<>|]", "", info.title) or "youtube_video"

        if output_format.lower() == "mp3":
            file_format = "bestaudio/best"
            postprocessors = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "0",
            }]
            outtmpl = str(target_dir / f"{safe_title}.%(ext)s")
            ydl_opts = {
                "format": file_format,
                "outtmpl": outtmpl,
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "postprocessors": postprocessors,
                "paths": {"home": str(target_dir)},
                "retries": 3,
            }
        else:
            ydl_opts = {
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "outtmpl": str(target_dir / f"{safe_title}.%(ext)s"),
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "merge_output_format": "mp4",
                "paths": {"home": str(target_dir)},
                "retries": 3,
            }

        def progress_hook(data):
            if progress_callback is None:
                return

            if data.get("status") == "downloading":
                percent = YouTubeService._parse_percent(data.get("_percent_str"))
                if percent is not None:
                    progress_callback(percent, f"Baixando... {percent}%")
            elif data.get("status") == "finished":
                progress_callback(100, "Finalizando arquivo...")

        ydl_opts["progress_hooks"] = [progress_hook]

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([cleaned_url])
        except Exception as exc:  # pragma: no cover - handled by caller
            raise RuntimeError(f"Falha ao baixar o conteúdo: {exc}") from exc

        file_name = safe_title + (".mp3" if output_format.lower() == "mp3" else ".mp4")
        return str(target_dir / file_name)

    @staticmethod
    def _parse_percent(value: Optional[str]) -> Optional[int]:
        if not value:
            return None

        text = str(value).strip().rstrip("%")
        try:
            percent = float(text)
            return min(max(int(percent), 0), 100)
        except ValueError:
            return None
