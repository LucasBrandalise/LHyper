from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from app.core.paths import thumbnails_dir


class ThumbnailService:
    """Downloads thumbnails and keeps them in a disk cache."""

    TIMEOUT = 15
    MAX_BYTES = 10 * 1024 * 1024

    def __init__(self, cache_dir: str | Path | None = None):
        self.cache_dir = Path(cache_dir) if cache_dir is not None else thumbnails_dir()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def cache_path(self, thumbnail_url: str) -> Path:
        # hash() do Python muda a cada execução; sha1 gera um nome estável entre sessões.
        digest = hashlib.sha1(thumbnail_url.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.img"

    def fetch(self, thumbnail_url: str) -> Path:
        """Return the cached file for ``thumbnail_url``, downloading it if needed.

        Raises ``ValueError`` for unsupported URLs and ``OSError`` on network/disk failures.
        """
        if urlsplit(thumbnail_url).scheme.lower() not in ("http", "https"):
            raise ValueError("URL de thumbnail inválida.")

        target = self.cache_path(thumbnail_url)
        if target.is_file() and target.stat().st_size > 0:
            return target

        request = Request(thumbnail_url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=self.TIMEOUT) as response:
            data = response.read(self.MAX_BYTES + 1)
        if not data or len(data) > self.MAX_BYTES:
            raise OSError("Thumbnail vazia ou grande demais.")

        # Grava em arquivo temporário e renomeia: nunca deixa um arquivo pela metade no cache.
        fd, tmp_name = tempfile.mkstemp(dir=self.cache_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
            os.replace(tmp_name, target)
        except BaseException:
            Path(tmp_name).unlink(missing_ok=True)
            raise
        return target
