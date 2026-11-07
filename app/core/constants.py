APP_NAME = "LHyper"
APP_VERSION = "0.2.5"
APP_TITLE = APP_NAME
VERSION_LABEL = f"Version {APP_VERSION}"

FORMAT_MP4 = "mp4"
FORMAT_MP3 = "mp3"
# (código interno, rótulo exibido na interface)
FORMAT_OPTIONS = (
    (FORMAT_MP4, "MP4 - Vídeo"),
    (FORMAT_MP3, "MP3 - Áudio"),
)

STATUS_COMPLETED = "completed"
STATUS_ERROR = "error"
STATUS_MISSING = "missing"

# Qualidade (opcional). "best" mantém o comportamento original do download.
QUALITY_BEST = "best"
VIDEO_QUALITY_OPTIONS = (
    (QUALITY_BEST, "Melhor disponível"),
    ("2160", "2160p · 4K"),
    ("1440", "1440p · 2K"),
    ("1080", "1080p · Full HD"),
    ("720", "720p · HD"),
    ("480", "480p"),
    ("360", "360p"),
)
AUDIO_QUALITY_OPTIONS = (
    (QUALITY_BEST, "Máxima · VBR"),
    ("320", "320 kbps"),
    ("192", "192 kbps"),
    ("128", "128 kbps"),
)
