from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.core.models import DownloadRecord
from app.database.database import Database


class DownloadRepository:
    def __init__(self, database_path: str | Path | None = None):
        self.database = Database(database_path)

    def add_or_update(self, record: DownloadRecord):
        now = datetime.now(timezone.utc).isoformat()

        with self.database.connection() as conn:
            existing = conn.execute(
                "SELECT id FROM downloads WHERE file_path = ?",
                (record.file_path,),
            ).fetchone()

            if existing is None:
                conn.execute(
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
                        now,
                        now,
                        record.error_message,
                    ),
                )
            else:
                conn.execute(
                    """
                    UPDATE downloads
                    SET title = ?, url = ?, thumbnail = ?, file_size = ?, file_format = ?,
                        status = ?, updated_at = ?, error_message = ?
                    WHERE file_path = ?
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
                        record.file_path,
                    ),
                )
            conn.commit()

    def list(self):
        with self.database.connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM downloads
                ORDER BY updated_at DESC
                """
            ).fetchall()

        return [
            DownloadRecord(
                id=row["id"],
                title=row["title"],
                url=row["url"],
                thumbnail=row["thumbnail"],
                file_path=row["file_path"],
                file_size=row["file_size"],
                file_format=row["file_format"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                error_message=row["error_message"],
            )
            for row in rows
        ]

    def sync_from_disk(self, output_dir: str | Path):
        path = Path(output_dir)
        if not path.exists():
            return []

        records = []
        for file_path in sorted(path.iterdir()):
            if not file_path.is_file():
                continue
            record = DownloadRecord(
                id=None,
                title=file_path.stem,
                url="",
                thumbnail=None,
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                file_format=file_path.suffix.lower().replace(".", "") or "unknown",
                status="completed",
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat(),
                error_message=None,
            )
            self.add_or_update(record)
            records.append(record)
        return records
