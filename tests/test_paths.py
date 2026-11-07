import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.core import paths

PROJECT_ROOT = Path(paths.__file__).resolve().parents[2]


class PathLayoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.exe_dir = self.root / "LHyper"
        self.exe_dir.mkdir()
        self.local_appdata = self.root / "LocalAppData"
        self.user_downloads = self.root / "UserDownloads"

    def _frozen(self):
        """Simulate running as LHyper.exe inside ``self.exe_dir``."""
        stack = [
            mock.patch.object(sys, "frozen", True, create=True),
            mock.patch.object(sys, "executable", str(self.exe_dir / "LHyper.exe")),
            mock.patch.dict("os.environ", {"LOCALAPPDATA": str(self.local_appdata)}),
            mock.patch.object(paths, "_user_downloads", return_value=self.user_downloads),
        ]
        for patcher in stack:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_source_run_uses_project_folder(self):
        self.assertFalse(paths.is_frozen())
        self.assertEqual(paths.app_data_dir(), PROJECT_ROOT / "app_data")
        self.assertEqual(paths.downloads_dir(), PROJECT_ROOT / "downloads")

    def test_installed_uses_user_folders(self):
        self._frozen()
        self.assertTrue(paths.is_installed())
        self.assertEqual(paths.app_data_dir(), self.local_appdata / "LHyper")
        self.assertEqual(paths.downloads_dir(), self.user_downloads / "LHyper")
        self.assertEqual(paths.thumbnails_dir(), self.local_appdata / "LHyper" / "thumbnails")

    def test_portable_marker_keeps_data_next_to_exe(self):
        (self.exe_dir / paths.PORTABLE_MARKER).write_text("portable", encoding="utf-8")
        self._frozen()
        self.assertTrue(paths.is_portable())
        self.assertEqual(paths.app_data_dir(), self.exe_dir / "app_data")
        self.assertEqual(paths.downloads_dir(), self.exe_dir / "downloads")

    def test_legacy_zip_without_marker_stays_portable(self):
        # Quem extraiu o .zip da v0.2.6 já tem app_data ao lado do exe e nenhum marcador.
        (self.exe_dir / "app_data").mkdir()
        self._frozen()
        self.assertTrue(paths.is_portable())
        self.assertEqual(paths.downloads_dir(), self.exe_dir / "downloads")

    def test_user_downloads_resolves_a_real_folder(self):
        location = paths._user_downloads()
        self.assertTrue(location.is_absolute())


if __name__ == "__main__":
    unittest.main()
