from __future__ import annotations

import sqlite3
from pathlib import Path


class Database:
    """SQLite helper for app state and download history."""

    def __init__(self, database_path: str | Path | None = None):
        base_path = Path(database_path) if database_path is not None else Path(__file__).resolve().parents[2] / "app_data"
        base_path.mkdir(parents=True, exist_ok=True)

        self.database_path = base_path / "downloads.db" if base_path.suffix != ".db" else base_path
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
            conn.commit()

    def connection(self):
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn
