import os
import tempfile
import time
import unittest
from pathlib import Path

from app.core.constants import STATUS_COMPLETED, STATUS_ERROR, STATUS_MISSING
from app.core.models import DownloadRecord
from app.database.download_repository import DownloadRepository, is_media_file


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        # Se alguma conexão SQLite ficar aberta, o cleanup falha no Windows (arquivo bloqueado).
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.downloads = self.root / "downloads"
        self.downloads.mkdir()
        self.repo = DownloadRepository(self.root / "data")

    def _record(self, **overrides):
        values = dict(id=None, title="Título", url="https://youtu.be/a", file_path="", file_format="mp4")
        values.update(overrides)
        return DownloadRecord(**values)

    def test_database_path_accepts_dir_or_file(self):
        self.assertEqual(self.repo.database.database_path, self.root / "data" / "downloads.db")
        explicit = DownloadRepository(self.root / "x" / "custom.db")
        self.assertEqual(explicit.database.database_path, self.root / "x" / "custom.db")
        self.assertTrue(explicit.database.database_path.is_file())

    def test_add_or_update_upserts_by_path(self):
        path = str(self.downloads / "a.mp4")
        self.repo.add_or_update(self._record(file_path=path, file_size=1))
        self.repo.add_or_update(self._record(file_path=path, file_size=2, title="Novo"))
        records = self.repo.list()
        self.assertEqual(len(records), 1)
        self.assertEqual((records[0].title, records[0].file_size), ("Novo", 2))

    def test_errors_do_not_overwrite_each_other(self):
        self.repo.add_or_update(self._record(status=STATUS_ERROR, error_message="e1"))
        self.repo.add(self._record(status=STATUS_ERROR, error_message="e2"))
        messages = sorted(r.error_message for r in self.repo.list())
        self.assertEqual(messages, ["e1", "e2"])

    def test_sync_preserves_download_metadata(self):
        file_path = self.downloads / "arquivo.mp4"
        file_path.write_bytes(b"12345")
        self.repo.add_or_update(
            self._record(
                title="Título real",
                url="https://youtu.be/x",
                file_path=str(file_path),
                file_size=5,
                thumbnail="https://i.ytimg.com/t.jpg",
            )
        )
        self.repo.sync_from_disk(self.downloads)
        record = self.repo.list()[0]
        self.assertEqual(record.title, "Título real")
        self.assertEqual(record.url, "https://youtu.be/x")
        self.assertEqual(record.thumbnail, "https://i.ytimg.com/t.jpg")

    def test_sync_adds_only_media_files(self):
        for name in (
            "video.mp4",
            "musica.mp3",
            "video.mp4.part",
            "x.f137.mp4",
            "x.f140-1.m4a",
            "notas.txt",
            "video.ytdl",
            ".oculto.mp4",
        ):
            (self.downloads / name).write_bytes(b"x")
        (self.downloads / "pasta.mp4").mkdir()
        added = self.repo.sync_from_disk(self.downloads)
        self.assertEqual(sorted(Path(r.file_path).name for r in added), ["musica.mp3", "video.mp4"])
        # Segunda sincronização não duplica nada.
        self.assertEqual(self.repo.sync_from_disk(self.downloads), [])
        self.assertEqual(len(self.repo.list()), 2)

    def test_sync_marks_missing_and_restores(self):
        file_path = self.downloads / "a.mp3"
        file_path.write_bytes(b"abc")
        self.repo.sync_from_disk(self.downloads)
        file_path.unlink()
        self.repo.sync_from_disk(self.downloads)
        self.assertEqual(self.repo.list()[0].status, STATUS_MISSING)

        file_path.write_bytes(b"abcdef")
        self.repo.sync_from_disk(self.downloads)
        record = self.repo.list()[0]
        self.assertEqual((record.status, record.file_size), (STATUS_COMPLETED, 6))

    def test_sync_ignores_other_directories_and_missing_dir(self):
        other = self.root / "outro" / "b.mp4"
        self.repo.add_or_update(self._record(file_path=str(other)))
        self.assertEqual(self.repo.sync_from_disk(self.root / "nao_existe"), [])
        self.assertEqual(self.repo.list()[0].status, STATUS_COMPLETED)

    def test_sync_uses_file_mtime_and_list_order_is_stable(self):
        old = self.downloads / "velho.mp4"
        new = self.downloads / "novo.mp4"
        old.write_bytes(b"x")
        new.write_bytes(b"x")
        now = time.time()
        os.utime(old, (now - 86400, now - 86400))
        self.repo.sync_from_disk(self.downloads)
        first = [r.title for r in self.repo.list()]
        self.assertEqual(first, ["novo", "velho"])
        self.repo.sync_from_disk(self.downloads)
        self.assertEqual([r.title for r in self.repo.list()], first)

    def test_is_media_file(self):
        media = self.downloads / "Clip.MP4"
        media.write_bytes(b"x")
        self.assertTrue(is_media_file(media))
        self.assertFalse(is_media_file(self.downloads / "nao_existe.mp4"))


if __name__ == "__main__":
    unittest.main()
