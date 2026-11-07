"""Design tokens, fontes e folha de estilo (QSS) do LHyper.

Direção: uma ferramenta rápida, exata e silenciosa, como uma mesa de edição à
noite. Superfícies em grafite neutro, um único acento laranja (a cor da marca)
usado só na ação principal, na seleção e no número que importa. Números de
mídia (duração, tamanho, velocidade) em fonte mono, como um timecode.

Valores baseados no unslop de Damir Sokolovsky (@heydamir), CC BY 4.0.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase

from app.core.paths import resource_path

# ---------------------------------------------------------------------- rampa grafite
BG_DEEP = "#0F0F10"      # barra superior e rodapé
BG = "#141415"           # fundo da página
SURFACE = "#19191B"      # cartões
SURFACE_2 = "#232325"    # elevado: campos, linha ativa
SURFACE_3 = "#2A2A2D"    # hover sobre elevado
HAIRLINE = "rgba(237, 237, 237, 0.08)"
HAIRLINE_STRONG = "rgba(237, 237, 237, 0.14)"

TEXT = "#EDEDED"
TEXT_2 = "#A1A1A6"
TEXT_3 = "#85858B"

# ---------------------------------------------------------------------- acento e semânticas
ACCENT = "#FF570A"
ACCENT_HOVER = "#FF6A26"
ACCENT_PRESSED = "#E84E08"
ON_ACCENT = "#141415"    # texto escuro sobre o laranja (contraste > 4.5:1)
POSITIVE = "#4CC38A"
NEGATIVE = "#E5484D"
CAUTION = "#D9A54A"

# Aliases mantidos para compatibilidade com componentes existentes
SURFACE_DEEP = BG_DEEP
SUCCESS = POSITIVE
DANGER = NEGATIVE
WARNING = CAUTION
BORDER = HAIRLINE
BORDER_STRONG = HAIRLINE_STRONG

# ---------------------------------------------------------------------- forma
RADIUS_PANEL = 14
RADIUS_CARD = 12
RADIUS_CONTROL = 8
RADIUS_SMALL = 6
RADIUS_LG = RADIUS_PANEL
RADIUS_MD = RADIUS_CARD
RADIUS_SM = RADIUS_CONTROL

# ---------------------------------------------------------------------- movimento
EASE_DURATION_FAST = 150
EASE_DURATION_ENTER = 300

FONT_FAMILY = "Inter"
MONO_FAMILY = "JetBrains Mono"
_FALLBACK_FAMILIES = ["Inter", "Segoe UI Variable Text", "Segoe UI", "sans-serif"]
_FALLBACK_MONO = ["JetBrains Mono", "Cascadia Mono", "Consolas", "monospace"]


def load_fonts() -> str:
    """Registra as fontes empacotadas em assets/fonts e escolhe as famílias disponíveis."""
    global FONT_FAMILY, MONO_FAMILY
    fonts_dir = Path(resource_path("assets/fonts"))
    if fonts_dir.is_dir():
        for font_file in sorted(fonts_dir.glob("*.ttf")):
            QFontDatabase.addApplicationFont(str(font_file))
    available = set(QFontDatabase.families())
    FONT_FAMILY = next((f for f in _FALLBACK_FAMILIES if f in available), "sans-serif")
    MONO_FAMILY = next((f for f in _FALLBACK_MONO if f in available), "monospace")
    return FONT_FAMILY


def mono_font(pixel_size: int = 12, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    font = QFont(MONO_FAMILY)
    font.setPixelSize(pixel_size)
    font.setWeight(weight)
    font.setStyleHint(QFont.StyleHint.Monospace)
    return font


def stylesheet() -> str:
    chevron = resource_path("assets/icons/chevron-down.svg").replace("\\", "/")
    ui = FONT_FAMILY
    mono = MONO_FAMILY
    return f"""
    * {{
        font-family: "{ui}", "Segoe UI";
        outline: 0;
    }}
    QMainWindow, #root {{ background-color: {BG}; }}
    QWidget {{ color: {TEXT}; font-size: 14px; }}
    QLabel {{ background: transparent; }}
    QToolTip {{
        background-color: {SURFACE_2};
        color: {TEXT};
        border: 1px solid {HAIRLINE_STRONG};
        border-radius: {RADIUS_SMALL}px;
        padding: 4px 8px;
        font-size: 12px;
    }}

    /* ------------------------------------------------------------ barra superior */
    #header {{
        background-color: {BG_DEEP};
        border-bottom: 1px solid {HAIRLINE};
    }}
    #wordmark {{
        font-size: 16px;
        font-weight: 600;
        color: {TEXT};
    }}
    #nav_button {{
        background: transparent;
        color: {TEXT_2};
        border: 1px solid transparent;
        border-radius: {RADIUS_CONTROL}px;
        padding: 0 12px;
        font-size: 14px;
        font-weight: 500;
        text-align: left;
    }}
    #nav_button:hover {{ color: {TEXT}; background-color: {SURFACE}; }}
    #nav_button:checked {{
        color: {TEXT};
        background-color: {SURFACE_2};
        border: 1px solid {HAIRLINE};
        border-top: 1px solid rgba(255, 255, 255, 0.10);
    }}
    #nav_button:focus {{ border: 1px solid {HAIRLINE_STRONG}; }}

    /* ------------------------------------------------------------ rodapé */
    #footer {{
        background-color: {BG_DEEP};
        border-top: 1px solid {HAIRLINE};
    }}
    #footer_text {{ color: {TEXT_2}; font-size: 12px; }}
    #footer_muted {{ color: {TEXT_3}; font-size: 12px; }}
    #footer_mono {{ color: {TEXT_3}; font-size: 12px; font-family: "{mono}"; }}
    #footer_link {{
        background: transparent;
        border: none;
        color: {TEXT_2};
        font-size: 12px;
        padding: 0 8px;
        border-radius: {RADIUS_SMALL}px;
        min-height: 24px;
    }}
    #footer_link:hover {{ color: {TEXT}; background: {SURFACE}; }}

    /* ------------------------------------------------------------ tipografia */
    #page_title {{ font-size: 28px; font-weight: 500; }}
    #hero_title {{ font-size: 28px; font-weight: 500; }}
    #card_title {{ font-size: 15px; font-weight: 500; }}
    #subtitle, #muted {{ color: {TEXT_2}; font-size: 14px; }}
    #meta {{ color: {TEXT_3}; font-size: 12px; }}
    #mono_meta {{ color: {TEXT_2}; font-size: 12px; font-family: "{mono}"; }}
    #field_label {{ color: {TEXT_2}; font-size: 13px; font-weight: 500; }}
    #videoTitle {{ font-size: 16px; font-weight: 500; color: {TEXT}; }}
    #videoTitle[empty="true"] {{ color: {TEXT_3}; font-weight: 400; }}

    /* ------------------------------------------------------------ superfícies */
    #card {{
        background-color: {SURFACE};
        border: 1px solid {HAIRLINE};
        border-radius: {RADIUS_PANEL}px;
    }}
    #inner_card {{
        background-color: {BG};
        border: 1px solid {HAIRLINE};
        border-radius: {RADIUS_CONTROL}px;
    }}

    /* ------------------------------------------------------------ campos */
    QLineEdit {{
        background-color: {SURFACE_2};
        border: 1px solid {HAIRLINE};
        border-radius: {RADIUS_CONTROL}px;
        padding: 0 12px;
        color: {TEXT};
        font-size: 14px;
        selection-background-color: {ACCENT};
        selection-color: {ON_ACCENT};
    }}
    QLineEdit:hover {{ border: 1px solid {HAIRLINE_STRONG}; }}
    QLineEdit:focus {{ border: 1px solid {TEXT_3}; }}

    QComboBox {{
        background-color: {SURFACE_2};
        border: 1px solid {HAIRLINE};
        border-radius: {RADIUS_CONTROL}px;
        padding: 0 32px 0 12px;
        color: {TEXT};
        font-size: 14px;
    }}
    QComboBox:hover {{ border: 1px solid {HAIRLINE_STRONG}; }}
    QComboBox:focus, QComboBox:on {{ border: 1px solid {TEXT_3}; }}
    QComboBox:disabled {{ color: {TEXT_3}; }}
    QComboBox::drop-down {{ border: none; width: 32px; background: transparent; }}
    QComboBox::down-arrow {{ image: url("{chevron}"); width: 12px; height: 12px; }}
    QComboBox QAbstractItemView {{
        background-color: {SURFACE_2};
        border: 1px solid {HAIRLINE_STRONG};
        color: {TEXT};
        padding: 4px;
        selection-background-color: {SURFACE_3};
        selection-color: {TEXT};
    }}

    /* ------------------------------------------------------------ botões */
    #secondary_button {{
        background-color: {SURFACE_2};
        border: 1px solid {HAIRLINE};
        border-top: 1px solid rgba(255, 255, 255, 0.10);
        border-radius: {RADIUS_CONTROL}px;
        color: {TEXT};
        font-size: 14px;
        font-weight: 500;
        padding: 0 16px;
    }}
    #secondary_button:hover {{ background-color: {SURFACE_3}; }}
    #secondary_button:pressed {{ background-color: {SURFACE}; }}
    #secondary_button:focus {{ border: 1px solid {TEXT_3}; }}
    #secondary_button:disabled {{ color: {TEXT_3}; }}
    #ghost_button {{
        background: transparent;
        border: 1px solid transparent;
        border-radius: {RADIUS_CONTROL}px;
        color: {TEXT_2};
        font-size: 13px;
        padding: 0 8px;
    }}
    #ghost_button:hover {{ color: {TEXT}; background: {SURFACE_2}; }}
    #ghost_button:pressed {{ background: {SURFACE}; }}
    #ghost_button:focus {{ border: 1px solid {HAIRLINE_STRONG}; }}
    #danger_button {{
        background: transparent;
        border: 1px solid {HAIRLINE};
        border-radius: {RADIUS_CONTROL}px;
        color: {TEXT_2};
        font-size: 13px;
        padding: 0 12px;
    }}
    #danger_button:hover {{ color: {NEGATIVE}; border: 1px solid rgba(229, 72, 77, 0.4); }}
    #danger_button:disabled {{ color: {TEXT_3}; }}

    /* ------------------------------------------------------------ downloads */
    #download_row {{
        background-color: transparent;
        border: none;
        border-bottom: 1px solid {HAIRLINE};
        border-radius: 0;
    }}
    #download_row:hover {{ background-color: {SURFACE}; }}
    #row_title {{ font-size: 14px; font-weight: 500; }}
    #row_meta {{ color: {TEXT_3}; font-size: 12px; font-family: "{mono}"; }}
    #download_status_completed, #download_status_error, #download_status_missing {{
        color: {TEXT_2};
        font-size: 13px;
    }}
    #download_error {{ color: {NEGATIVE}; font-size: 13px; }}

    /* ------------------------------------------------------------ progresso */
    QProgressBar {{
        background-color: {SURFACE_2};
        border: none;
        border-radius: 2px;
        min-height: 4px;
        max-height: 4px;
        color: transparent;
    }}
    QProgressBar::chunk {{ border-radius: 2px; background: {ACCENT}; }}

    /* ------------------------------------------------------------ rolagem */
    QScrollArea {{ border: none; background: transparent; }}
    QScrollArea > QWidget > QWidget {{ background: transparent; }}
    QScrollBar:vertical {{ background: transparent; width: 8px; margin: 4px 0 4px 0; }}
    QScrollBar::handle:vertical {{ background: {SURFACE_3}; border-radius: 4px; min-height: 40px; }}
    QScrollBar::handle:vertical:hover {{ background: {TEXT_3}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; height: 0; }}
    """
