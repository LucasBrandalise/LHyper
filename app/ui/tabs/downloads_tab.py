"""Backward-compatible alias: the downloads screen now lives in app.ui.pages."""

from app.ui.pages.downloads_page import DownloadsPage

DownloadsTab = DownloadsPage

__all__ = ["DownloadsTab"]
