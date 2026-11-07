from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.core.constants import STATUS_COMPLETED


@dataclass
class VideoInfo:
    title: str
    url: str
    thumbnail: Optional[str] = None
    duration: Optional[int] = None
    uploader: Optional[str] = None


@dataclass
class DownloadRecord:
    id: Optional[int]
    title: str
    url: str
    thumbnail: Optional[str] = None
    file_path: str = ""
    file_size: int = 0
    file_format: str = "unknown"
    status: str = STATUS_COMPLETED
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    error_message: Optional[str] = None
