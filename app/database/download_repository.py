from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.core.constants import STATUS_COMPLETED, STATUS_MISSING
from app.core.models import DownloadRecord
from app.database.database import Database

MEDIA_EXTENSIONS = frozenset(
    {"mp4", "mkv", "webm", "mov", "mp3", "m4a", "aac", "opus", "ogg", "wav", "flac"}
)
# Arquivos intermediários do yt-dlp, ex.: "Titulo.f137.mp4" (stream antes do merge).
_INTERMEDIATE_PATTERN = re.compile(r"\.f\d+(-\d+)?$")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_media_file(path: Path) -> bool:
    if not path.is_file() or path.name.startswith("."):
        return False
    extension = path.suffix.lower().lstrip(".")
    if extension not in MEDIA_EXTENSIONS:
        return False
    return not _INTERMEDIATE_PATTERN.search(path.stem)


class DownloadRepository:
    def __init__(self, database_path: str | Path | None = None):
        self.database = Database(database_path)

    def add(self, record: DownloadRecord) -> int:
        """Always inserts a new row (used for errors, which have no file)."""
        now = _now()
        with self.database.connection() as conn:
            cursor = self._insert(conn, record, record.created_at or now, now)
            return int(cursor.lastrowid)

    def add_or_update(self, record: DownloadRecord):
        """Insert or update the record identified by its file path."""
        if not record.file_path:
            self.add(record)
            return

        now = _now()
        with self.database.connection() as conn:
            existing = conn.execute(
                "SELECT id FROM downloads WHERE file_path = ?",
                (record.file_path,),
            ).fetchone()

            if existing is None:
                self._insert(conn, record, record.created_at or now, now)
            else:
                conn.execute(
                    """
                    UPDATE downloads
                    SET title = ?, url = ?, thumbnail = ?, file_size = ?, file_format = ?,
                        status = ?, updated_at = ?, error_message = ?
                    WHERE id = ?
                    """,
                    (
                        record.title,
                        record.url,
                        record.thumbnail,
                        record.file_size,
                        record.file_format,
                        record.status,
                        now,
                        record.error_message,
                        existing["id"],
                    ),
                )

    @staticmethod
    def _insert(conn: sqlite3.Connection, record: DownloadRecord, created_at: str, updated_at: str):
        return conn.execute(
            """
            INSERT INTO downloads (
                title, url, thumbnail, file_path, file_size, file_format,
                status, created_at, updated_at, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.title,
                record.url,
                record.thumbnail,
                record.file_path,
                record.file_size,
                record.file_format,
                record.status,
                created_at,
                updated_at,
                record.error_message,
            ),
        )

    def list(self) -> list[DownloadRecord]:
        with self.database.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM downloads ORDER BY created_at DESC, id DESC"
            ).fetchall()

        return [
            DownloadRecord(
                id=row["id"],
                title=row["title"],
                url=row["url"],
                thumbnail=row["thumbnail"],
                file_path=row["file_path"],
                file_size=row["file_size"] or 0,
                file_format=row["file_format"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                error_message=row["error_message"],
            )
            for row in rows
        ]

    def sync_from_disk(self, output_dir: str | Path) -> list[DownloadRecord]:
        """Reconcile the history with the files in ``output_dir``.

        - media files not yet registered are added (title = file name);
        - registered files only get their size/status refreshed, so metadata saved at
          download time (title, URL, thumbnail) is preserved;
        - registered files that no longer exist are marked as missing.

        Returns the newly added records.
        """
        directory = Path(output_dir).resolve()
        files = (
            {str(path): path for path in directory.iterdir() if is_media_file(path)}
            if directory.is_dir()
            else {}
        )

        added: list[DownloadRecord] = []
        now = _now()
        with self.database.connection() as conn:
            rows = conn.execute(
                "SELECT id, file_path, file_size, status FROM downloads WHERE file_path != ''"
            ).fetchall()
            known = {row["file_path"]: row for row in rows}

            for row in rows:
                path = Path(row["file_path"])
                if path.parent != directory:
                    continue
                if row["file_path"] in files:
                    size = files[row["file_path"]].stat().st_size
                    if row["status"] == STATUS_MISSING or row["file_size"] != size:
                        conn.execute(
                            "UPDATE downloads SET file_size = ?, status = ?, updated_at = ? WHERE id = ?",
                            (size, STATUS_COMPLETED, now, row["id"]),
                        )
                elif row["status"] == STATUS_COMPLETED:
                    conn.execute(
                        "UPDATE downloads SET status = ?, updated_at = ? WHERE id = ?",
                        (STATUS_MISSING, now, row["id"]),
                    )

            for file_path, path in sorted(files.items()):
                if file_path in known:
                    continue
                stat = path.stat()
                created_at = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
                record = DownloadRecord(
                    id=None,
                    title=path.stem,
                    url="",
                    file_path=file_path,
                    file_size=stat.st_size,
                    file_format=path.suffix.lower().lstrip("."),
                    status=STATUS_COMPLETED,
                    created_at=created_at,
                    updated_at=now,
                )
                record.id = int(self._insert(conn, record, created_at, now).lastrowid)
                added.append(record)

        return added
