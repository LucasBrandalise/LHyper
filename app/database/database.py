from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.core.paths import app_data_dir


class Database:
    """SQLite helper for app state and download history."""

    DEFAULT_FILENAME = "downloads.db"

    def __init__(self, database_path: str | Path | None = None):
        path = Path(database_path) if database_path is not None else app_data_dir()
        if path.suffix != ".db":
            path = path / self.DEFAULT_FILENAME
        path.parent.mkdir(parents=True, exist_ok=True)

        self.database_path = path
        self._initialize()

    def _initialize(self):
        with self.connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    thumbnail TEXT,
                    file_path TEXT NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    file_format TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'completed',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    error_message TEXT
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_downloads_file_path ON downloads (file_path)"
            )

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Yield a connection that commits on success, rolls back on error and is always closed."""
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()
