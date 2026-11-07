import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.services import thumbnail_service
from app.services.thumbnail_service import ThumbnailService


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, size=-1):
        return self.data if size < 0 else self.data[:size]


class ThumbnailServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.service = ThumbnailService(self.tmp.name)

    def test_cache_name_is_stable(self):
        url = "https://i.ytimg.com/vi/x/maxresdefault.jpg"
        self.assertEqual(self.service.cache_path(url), ThumbnailService(self.tmp.name).cache_path(url))
        self.assertNotEqual(self.service.cache_path(url), self.service.cache_path(url + "?2"))

    def test_rejects_non_http_urls(self):
        for url in ("file:///C:/Windows/win.ini", "ftp://x/y.jpg", ""):
            with self.subTest(url=url), self.assertRaises(ValueError):
                self.service.fetch(url)

    def test_downloads_once_then_uses_cache(self):
        url = "https://i.ytimg.com/a.jpg"
        with mock.patch.object(thumbnail_service, "urlopen", return_value=FakeResponse(b"img")) as urlopen:
            first = self.service.fetch(url)
            second = self.service.fetch(url)
        self.assertEqual(first, second)
        self.assertEqual(first.read_bytes(), b"img")
        self.assertEqual(urlopen.call_count, 1)
        self.assertEqual(list(Path(self.tmp.name).glob("*.tmp")), [])

    def test_network_error_leaves_no_partial_file(self):
        with mock.patch.object(thumbnail_service, "urlopen", side_effect=OSError("offline")):
            with self.assertRaises(OSError):
                self.service.fetch("https://i.ytimg.com/b.jpg")
        self.assertEqual(list(Path(self.tmp.name).iterdir()), [])

    def test_empty_or_oversized_response(self):
        with mock.patch.object(thumbnail_service, "urlopen", return_value=FakeResponse(b"")):
            with self.assertRaises(OSError):
                self.service.fetch("https://i.ytimg.com/c.jpg")
        big = b"x" * (ThumbnailService.MAX_BYTES + 1)
        with mock.patch.object(thumbnail_service, "urlopen", return_value=FakeResponse(big)):
            with self.assertRaises(OSError):
                self.service.fetch("https://i.ytimg.com/d.jpg")
        self.assertEqual(list(Path(self.tmp.name).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
