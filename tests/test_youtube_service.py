import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from yt_dlp.utils import DownloadError

from app.services import youtube_service
from app.services.youtube_service import DownloadCancelledError, YouTubeService


class ValidateUrlTests(unittest.TestCase):
    def test_accepts_youtube_variants(self):
        for url in (
            "https://www.youtube.com/watch?v=abc",
            "http://youtube.com/watch?v=abc",
            "https://m.youtube.com/watch?v=abc",
            "https://music.youtube.com/watch?v=abc",
            "https://youtu.be/abc",
            "https://www.youtube.com:443/watch?v=abc",
            "https://youtube.com?v=abc",
            "  https://youtu.be/abc  ",
            "HTTPS://WWW.YOUTUBE.COM/watch?v=abc",
        ):
            with self.subTest(url=url):
                self.assertEqual(YouTubeService.validate_url(url), url.strip())

    def test_rejects_invalid(self):
        for url in (
            "",
            "   ",
            None,
            "youtube.com/watch?v=abc",
            "ftp://youtube.com/x",
            "file:///C:/Windows/win.ini",
            "https://evil.com/youtube.com",
            "https://youtube.com.evil.com/watch",
            "https://notyoutube.com/watch",
            "https://youtube.com@evil.com/watch",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                YouTubeService.validate_url(url)


class FormatTests(unittest.TestCase):
    def test_normalize_format(self):
        self.assertEqual(YouTubeService.normalize_format("mp3"), "mp3")
        self.assertEqual(YouTubeService.normalize_format("MP3 - Áudio"), "mp3")
        self.assertEqual(YouTubeService.normalize_format("MP4 - Vídeo"), "mp4")
        self.assertEqual(YouTubeService.normalize_format(""), "mp4")
        self.assertEqual(YouTubeService.normalize_format(None), "mp4")

    def test_mp3_requires_ffmpeg(self):
        with self.assertRaises(RuntimeError):
            YouTubeService.build_download_options("mp3", "out", ffmpeg_available=False)

    def test_mp3_options(self):
        options = YouTubeService.build_download_options("mp3", "out", ffmpeg_available=True)
        self.assertEqual(options["format"], "bestaudio/best")
        self.assertEqual(options["postprocessors"][0]["preferredcodec"], "mp3")
        self.assertEqual(options["paths"], {"home": "out"})
        self.assertTrue(options["noplaylist"])

    def test_mp4_options_with_and_without_ffmpeg(self):
        with_ffmpeg = YouTubeService.build_download_options("mp4", "out", ffmpeg_available=True)
        self.assertIn("+bestaudio", with_ffmpeg["format"])
        self.assertEqual(with_ffmpeg["merge_output_format"], "mp4")

        without = YouTubeService.build_download_options("mp4", "out", ffmpeg_available=False)
        self.assertNotIn("+", without["format"])
        self.assertNotIn("merge_output_format", without)


class PercentTests(unittest.TestCase):
    def test_parse_percent(self):
        self.assertEqual(YouTubeService._parse_percent(" 42.7%"), 42)
        self.assertEqual(YouTubeService._parse_percent("\x1b[0;94m 42.0%\x1b[0m"), 42)
        self.assertEqual(YouTubeService._parse_percent("150%"), 100)
        self.assertIsNone(YouTubeService._parse_percent("N/A"))
        self.assertIsNone(YouTubeService._parse_percent(None))

    def test_compute_percent_prefers_bytes(self):
        self.assertEqual(YouTubeService._compute_percent({"downloaded_bytes": 50, "total_bytes": 200}), 25)
        self.assertEqual(
            YouTubeService._compute_percent({"downloaded_bytes": 10, "total_bytes_estimate": 20}), 50
        )
        self.assertEqual(YouTubeService._compute_percent({"_percent_str": "7%"}), 7)


class SingleEntryTests(unittest.TestCase):
    def test_playlist_returns_first_entry(self):
        info = {"_type": "playlist", "entries": [None, {"title": "a"}]}
        self.assertEqual(YouTubeService._single_entry(info), {"title": "a"})

    def test_empty_results(self):
        with self.assertRaises(RuntimeError):
            YouTubeService._single_entry(None)
        with self.assertRaises(RuntimeError):
            YouTubeService._single_entry({"_type": "playlist", "entries": []})


class FakeYDL:
    """Minimal stand-in for yt_dlp.YoutubeDL used by download_video."""

    instances = []

    def __init__(self, options):
        self.options = options
        FakeYDL.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def extract_info(self, url, download=False):
        return {"title": "Vídeo: teste?", "thumbnail": "https://i.ytimg.com/x.jpg"}

    def process_ie_result(self, info, download=True):
        home = Path(self.options["paths"]["home"])
        for hook in self.options["progress_hooks"]:
            hook({"status": "downloading", "downloaded_bytes": 1, "total_bytes": 2})
            hook({"status": "finished"})
        final = home / "Vídeo： teste？.mp3"
        final.write_bytes(b"data")
        return {**info, "requested_downloads": [{"filepath": str(final)}]}


class DownloadVideoTests(unittest.TestCase):
    def setUp(self):
        FakeYDL.instances.clear()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        patcher = mock.patch.object(youtube_service, "YoutubeDL", FakeYDL)
        patcher.start()
        self.addCleanup(patcher.stop)
        ffmpeg = mock.patch.object(YouTubeService, "ffmpeg_available", return_value=True)
        ffmpeg.start()
        self.addCleanup(ffmpeg.stop)

    def test_returns_real_output_path_and_reports_progress(self):
        progress, infos = [], []
        path = YouTubeService.download_video(
            "https://youtu.be/abc",
            "mp3",
            self.tmp.name,
            progress_callback=lambda p, m: progress.append(p),
            info_callback=infos.append,
        )
        self.assertTrue(Path(path).is_file())
        self.assertEqual(Path(path).name, "Vídeo： teste？.mp3")
        self.assertEqual(progress, [50, 100])
        self.assertEqual(infos[0].title, "Vídeo: teste?")
        self.assertEqual(len(FakeYDL.instances), 1, "metadados devem ser extraídos uma única vez")

    def test_cancel_before_download(self):
        event = threading.Event()
        event.set()
        with self.assertRaises(DownloadCancelledError):
            YouTubeService.download_video("https://youtu.be/abc", "mp4", self.tmp.name, cancel_event=event)

    def test_cancel_during_download(self):
        event = threading.Event()

        def fake_process(ydl, info, download=True):
            hook = ydl.options["progress_hooks"][0]
            hook({"status": "downloading", "downloaded_bytes": 1, "total_bytes": 2})
            hook({"status": "downloading", "downloaded_bytes": 2, "total_bytes": 2})
            raise AssertionError("o segundo hook deveria ter cancelado")

        with mock.patch.object(FakeYDL, "process_ie_result", autospec=True, side_effect=fake_process):
            with self.assertRaises(DownloadCancelledError):
                YouTubeService.download_video(
                    "https://youtu.be/abc",
                    "mp4",
                    self.tmp.name,
                    progress_callback=lambda p, m: event.set(),
                    cancel_event=event,
                )

    def test_yt_dlp_errors_become_runtime_error(self):
        with mock.patch.object(FakeYDL, "extract_info", side_effect=DownloadError("ERROR: Video unavailable")):
            with self.assertRaises(RuntimeError) as ctx:
                YouTubeService.download_video("https://youtu.be/abc", "mp4", self.tmp.name)
        self.assertIn("Video unavailable", str(ctx.exception))
        self.assertNotIn("ERROR:", str(ctx.exception))

    def test_missing_output_file_is_an_error(self):
        with mock.patch.object(
            FakeYDL, "process_ie_result", return_value={"requested_downloads": [{"filepath": "nao_existe.mp4"}]}
        ):
            with self.assertRaises(RuntimeError):
                YouTubeService.download_video("https://youtu.be/abc", "mp4", self.tmp.name)

    def test_invalid_url_never_reaches_yt_dlp(self):
        with self.assertRaises(ValueError):
            YouTubeService.download_video("https://example.com", "mp4", self.tmp.name)
        self.assertEqual(FakeYDL.instances, [])


if __name__ == "__main__":
    unittest.main()
