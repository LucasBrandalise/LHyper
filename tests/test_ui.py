import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication  # noqa: E402
from PySide6.QtWidgets import QApplication, QLabel  # noqa: E402

from app.core.constants import STATUS_COMPLETED, STATUS_ERROR  # noqa: E402
from app.core.models import DownloadRecord, VideoInfo  # noqa: E402
from app.database.download_repository import DownloadRepository  # noqa: E402
from app.services.youtube_service import DownloadCancelledError, YouTubeService  # noqa: E402
from app.ui.main_window import MainWindow  # noqa: E402
from app.ui.pages.downloads_page import DownloadsPage, format_size  # noqa: E402
from app.ui.widgets.preview_widget import PLACEHOLDER_TITLE, PreviewWidget  # noqa: E402

app = QApplication.instance() or QApplication([])


def process_until(condition, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        QCoreApplication.processEvents()
        if condition():
            return True
        time.sleep(0.01)
    return condition()


class TempDirTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.output_dir = self.root / "downloads"
        self.repository = DownloadRepository(self.root / "data")


class PreviewWidgetTests(TempDirTestCase):
    def test_leaving_url_field_does_not_start_download(self):
        widget = PreviewWidget(str(self.output_dir))
        downloads, previews = [], []
        widget.download_requested.connect(lambda: downloads.append(1))
        widget.preview_requested.connect(lambda: previews.append(1))

        widget.url_input.editingFinished.emit()
        widget.url_input.returnPressed.emit()
        self.assertEqual(downloads, [])
        self.assertEqual(previews, [1])

        widget.download_button.click()
        self.assertEqual(downloads, [1])

    def test_format_codes(self):
        widget = PreviewWidget(str(self.output_dir))
        self.assertEqual(widget.get_format(), "mp4")
        widget.format_select.setCurrentIndex(1)
        self.assertEqual(widget.get_format(), "mp3")

    def test_invalid_thumbnail_shows_fallback(self):
        widget = PreviewWidget(str(self.output_dir))
        broken = self.root / "broken.img"
        broken.write_bytes(b"not an image")
        widget.set_video_info("Título", str(broken))
        self.assertEqual(widget.thumbnail_label.text(), "Imagem indisponível")
        widget.clear_video_info()
        self.assertEqual(widget.video_title.text(), PLACEHOLDER_TITLE)


class DownloadsPageTests(TempDirTestCase):
    def test_lists_records_and_errors(self):
        self.output_dir.mkdir()
        (self.output_dir / "a.mp4").write_bytes(b"x" * 2048)
        self.repository.add(
            DownloadRecord(id=None, title="Falhou", url="u", status=STATUS_ERROR, error_message="sem rede")
        )
        page = DownloadsPage(str(self.output_dir), self.repository)

        self.assertEqual(page.items_layout.count(), 2)
        self.assertTrue(page.storage_label.text().startswith("1 arquivo, 2.0 KB"))
        texts = [label.text() for label in page.items_container.findChildren(QLabel)]
        self.assertIn("sem rede", texts)
        self.assertIn("Concluído", texts)

    def test_empty_state(self):
        page = DownloadsPage(str(self.output_dir), self.repository)
        self.assertEqual(page.items_layout.count(), 1)

    def test_format_size(self):
        self.assertEqual(format_size(0), "0 B")
        self.assertEqual(format_size(1536), "1.5 KB")
        self.assertEqual(format_size(5 * 1024**3), "5.0 GB")
        self.assertEqual(format_size(-1), "0 B")


class MainWindowTests(TempDirTestCase):
    def make_window(self):
        window = MainWindow(repository=self.repository, output_dir=self.output_dir)
        self.addCleanup(window.close)
        return window

    def test_navigation(self):
        window = self.make_window()
        window.nav_group.button(1).click()
        self.assertIs(window.stacked_widget.currentWidget(), window.downloads_page)
        window.nav_group.button(2).click()
        self.assertIs(window.stacked_widget.currentWidget(), window.settings_page)

    def test_invalid_url_does_not_start_download(self):
        window = self.make_window()
        window.preview.url_input.setText("https://example.com/video")
        window.handle_download()
        self.assertIsNone(window.download_thread)
        self.assertEqual(window.preview.status_label.text(), "A URL deve apontar para um vídeo do YouTube")

    def test_successful_download_is_recorded(self):
        gui_thread = threading.get_ident()
        called_from = []

        def fake_download(url, output_format, output_dir, progress_callback=None, info_callback=None,
                          cancel_event=None, **kwargs):
            called_from.append(threading.get_ident())
            info_callback(VideoInfo(title="Meu vídeo", url=url, thumbnail="https://i.ytimg.com/t.jpg"))
            progress_callback(50, "Baixando... 50%")
            path = Path(output_dir) / "Meu vídeo.mp3"
            path.write_bytes(b"abc")
            return str(path)

        window = self.make_window()
        window.preview.url_input.setText("https://youtu.be/abc")
        window.preview.format_select.setCurrentIndex(1)
        with mock.patch.object(YouTubeService, "download_video", side_effect=fake_download):
            window.handle_download()
            self.assertFalse(window.preview.download_button.isEnabled())
            window.handle_download()  # segundo clique é ignorado enquanto baixa
            self.assertTrue(process_until(lambda: window.download_thread is None))

        self.assertEqual(len(called_from), 1)
        self.assertNotEqual(called_from[0], gui_thread, "download deve rodar fora da thread da GUI")
        self.assertTrue(window.preview.download_button.isEnabled())
        records = self.repository.list()
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(
            (record.title, record.url, record.file_format, record.status, record.file_size),
            ("Meu vídeo", "https://youtu.be/abc", "mp3", STATUS_COMPLETED, 3),
        )
        self.assertEqual(record.thumbnail, "https://i.ytimg.com/t.jpg")
        self.assertIn("Download concluído", window.preview.status_label.text())

    def test_window_slots_run_on_gui_thread(self):
        calls = {}

        class SpyWindow(MainWindow):
            def on_download_completed(self, file_path):
                calls["completed"] = threading.get_ident()
                super().on_download_completed(file_path)

            def on_download_thread_finished(self):
                calls["finished"] = threading.get_ident()
                super().on_download_thread_finished()

            def _reap_preview_jobs(self):
                calls["reap"] = threading.get_ident()
                super()._reap_preview_jobs()

        def fake_download(url, output_format, output_dir, **kwargs):
            path = Path(output_dir) / "a.mp4"
            path.write_bytes(b"x")
            return str(path)

        window = SpyWindow(repository=self.repository, output_dir=self.output_dir)
        self.addCleanup(window.close)
        window.preview.url_input.setText("https://youtu.be/abc")
        with mock.patch.object(YouTubeService, "download_video", side_effect=fake_download), \
                mock.patch.object(YouTubeService, "extract_info", return_value=VideoInfo(title="t", url="u")):
            window.refresh_preview_from_url()
            window.handle_download()
            self.assertTrue(process_until(lambda: window.download_thread is None and not window._preview_jobs))

        gui = threading.get_ident()
        self.assertEqual(calls, {"completed": gui, "finished": gui, "reap": gui})

    def test_failed_download_is_recorded(self):
        window = self.make_window()
        window.preview.url_input.setText("https://youtu.be/abc")
        with mock.patch.object(YouTubeService, "download_video", side_effect=RuntimeError("Falha X")):
            window.handle_download()
            self.assertTrue(process_until(lambda: window.download_thread is None))
            window.handle_download()
            self.assertTrue(process_until(lambda: window.download_thread is None))

        records = self.repository.list()
        self.assertEqual([r.status for r in records], [STATUS_ERROR, STATUS_ERROR])
        self.assertEqual(window.preview.status_label.text(), "Falha X")

    def test_close_cancels_running_download(self):
        started = threading.Event()

        def slow_download(url, output_format, output_dir, progress_callback=None, info_callback=None,
                          cancel_event=None, **kwargs):
            started.set()
            if not cancel_event.wait(5):
                raise AssertionError("cancelamento não chegou")
            raise DownloadCancelledError("Download cancelado.")

        window = self.make_window()
        window.preview.url_input.setText("https://youtu.be/abc")
        with mock.patch.object(YouTubeService, "download_video", side_effect=slow_download):
            window.handle_download()
            self.assertTrue(started.wait(5))
            thread = window.download_thread
            begin = time.monotonic()
            window.close()
            self.assertLess(time.monotonic() - begin, 5)
            self.assertTrue(thread.isFinished())
            process_until(lambda: window.download_thread is None, timeout=1)
        self.assertEqual(self.repository.list(), [])

    def test_preview_runs_async_and_ignores_stale_results(self):
        def fake_extract(url):
            time.sleep(0.05)
            return VideoInfo(title=f"title:{url}", url=url)

        window = self.make_window()
        with mock.patch.object(YouTubeService, "extract_info", side_effect=fake_extract):
            window.preview.url_input.setText("https://youtu.be/old")
            window.refresh_preview_from_url()
            window.preview.url_input.setText("https://youtu.be/new")
            window.refresh_preview_from_url()
            window.refresh_preview_from_url()  # mesma URL: não dispara outra busca
            self.assertEqual(len(window._preview_jobs), 2)
            self.assertTrue(process_until(lambda: not window._preview_jobs))

        self.assertEqual(window.preview.video_title.text(), "title:https://youtu.be/new")
        self.assertEqual(window.preview.status_label.text(), "Preview atualizado")

    def test_preview_error_is_shown(self):
        window = self.make_window()
        with mock.patch.object(YouTubeService, "extract_info", side_effect=RuntimeError("Vídeo privado")):
            window.preview.url_input.setText("https://youtu.be/x")
            window.refresh_preview_from_url()
            self.assertTrue(process_until(lambda: not window._preview_jobs))
        self.assertEqual(window.preview.status_label.text(), "Vídeo privado")
        self.assertEqual(window.preview.video_title.text(), PLACEHOLDER_TITLE)


if __name__ == "__main__":
    unittest.main()
