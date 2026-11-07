from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class VideoInfo:
    title: str
    url: str
    thumbnail: Optional[str] = None
    duration: Optional[int] = None
    uploader: Optional[str] = None
    default_filename: Optional[str] = None
    output_dir: Path | None = None


@dataclass
class DownloadRecord:
    id: Optional[int]
    title: str
    url: str
    thumbnail: Optional[str] = None
    file_path: str = ""
    file_size: int = 0
    file_format: str = "unknown"
    status: str = "completed"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    error_message: Optional[str] = None
