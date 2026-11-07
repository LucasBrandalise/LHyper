"""Superfícies com o brilho laranja característico da identidade LHyper.

O brilho é desenhado em baixa resolução e ampliado com suavização — isso produz
um "blur" barato, sem QGraphicsBlurEffect, e o resultado fica em cache até o
próximo redimensionamento.
"""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import QFrame

from app.ui.styles import theme


def _ring(p: QPainter, rect: QRectF, center: QPointF, radius: float, width: float, color: QColor, alpha: int):
    """Anel luminoso suave: degradê radial transparente → cor → transparente."""
    inner = max(0.0, (radius - width) / (radius + width))
    mid = radius / (radius + width)
    grad = QRadialGradient(center, radius + width)
    c0 = QColor(color)
    c0.setAlpha(0)
    c1 = QColor(color)
    c1.setAlpha(alpha)
    grad.setColorAt(0.0, c0)
    grad.setColorAt(inner, c0)
    grad.setColorAt(mid, c1)
    grad.setColorAt(1.0, c0)
    p.fillRect(rect, QBrush(grad))


def paint_swoosh(width: int, height: int, intensity: float = 1.0, anchor: str = "right") -> QPixmap:
    """Pinta um arco luminoso laranja/vermelho sobre fundo preto (luz de longa exposição).

    O desenho é feito numa tela de proporção fixa e depois redimensionado, então o
    arco mantém a mesma forma em cartões largos (hero) ou 16:9 (thumbnail).
    """
    width, height = max(1, width), max(1, height)
    cw = min(width, 900)  # resolução de trabalho limitada: rápido e naturalmente suave
    ch = int(cw * (0.55 if anchor == "right" else 0.62))
    pm = QPixmap(cw, ch)
    pm.fill(QColor(theme.BG))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    rect = QRectF(0, 0, cw, ch)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)

    if anchor == "right":
        center = QPointF(cw * 0.84, cw * 0.66)
        radius = cw * 0.50
    else:
        center = QPointF(cw * 0.70, cw * 0.78)
        radius = cw * 0.58

    k = intensity
    _ring(p, rect, center, radius, cw * 0.22, QColor(170, 32, 8), int(80 * k))
    _ring(p, rect, center, radius, cw * 0.075, QColor(255, 87, 10), int(200 * k))
    _ring(p, rect, center, radius * 0.965, cw * 0.022, QColor(255, 130, 50), int(170 * k))
    _ring(p, rect, center, radius * 1.015, cw * 0.006, QColor(255, 180, 130), int(150 * k))
    _ring(p, rect, center, radius * 0.90, cw * 0.004, QColor(255, 170, 110), int(110 * k))
    _ring(p, rect, center, radius * 0.80, cw * 0.035, QColor(190, 40, 10), int(90 * k))
    _ring(p, rect, center, radius * 1.10, cw * 0.003, QColor(255, 150, 90), int(80 * k))

    hot = QPointF(center.x() - radius * 0.62, center.y() - radius * 0.70)
    core = QRadialGradient(hot, cw * 0.20)
    core.setColorAt(0.0, QColor(255, 160, 90, int(80 * k)))
    core.setColorAt(1.0, QColor(255, 87, 10, 0))
    p.fillRect(rect, QBrush(core))
    p.end()

    result = pm.scaled(width, height, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
    if anchor == "right":
        p = QPainter(result)
        vignette = QLinearGradient(QPointF(0, 0), QPointF(width, 0))
        vignette.setColorAt(0.0, QColor(11, 11, 11, 225))
        vignette.setColorAt(0.38, QColor(11, 11, 11, 140))
        vignette.setColorAt(0.70, QColor(11, 11, 11, 0))
        p.fillRect(QRectF(0, 0, width, height), QBrush(vignette))
        p.end()
    return result


class GlowFrame(QFrame):
    """QFrame arredondado com o brilho laranja pintado ao fundo."""

    def __init__(self, parent=None, radius: int = theme.RADIUS_LG, intensity: float = 1.0, anchor: str = "right"):
        super().__init__(parent)
        self._radius = radius
        self._intensity = intensity
        self._anchor = anchor
        self._cache: QPixmap | None = None
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def set_intensity(self, value: float):
        if abs(value - self._intensity) > 0.01:
            self._intensity = value
            self._cache = None
            self.update()

    def resizeEvent(self, event):
        self._cache = None
        super().resizeEvent(event)

    def paintEvent(self, event):
        ratio = self.devicePixelRatioF()
        if self._cache is None or self._cache.width() != int(self.width() * ratio):
            pm = paint_swoosh(int(self.width() * ratio), int(self.height() * ratio), self._intensity, self._anchor)
            pm.setDevicePixelRatio(ratio)
            self._cache = pm

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(rect, self._radius, self._radius)
        p.setClipPath(path)
        p.drawPixmap(0, 0, self._cache)
        p.setClipping(False)
        p.setPen(QPen(QColor(255, 255, 255, 22), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)
        p.end()
