"""Componentes visuais reutilizáveis (botões, progresso, segmentado, indicadores).

Regras: cor sólida, profundidade por degraus de superfície e linhas finas, sem
brilhos. Movimento só quando explica algo, com uma única curva de easing.
"""
from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPointF,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
    QTimer,
    QVariantAnimation,
    Signal,
)
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QWidget,
)

from app.ui.components import icons
from app.ui.styles import theme


def ease() -> QEasingCurve:
    """cubic-bezier(0.22, 1, 0.36, 1) — a única curva usada no app."""
    curve = QEasingCurve(QEasingCurve.Type.BezierSpline)
    curve.addCubicBezierSegment(QPointF(0.22, 1.0), QPointF(0.36, 1.0), QPointF(1.0, 1.0))
    return curve


def _mix(a: QColor, b: QColor, t: float) -> QColor:
    return QColor(
        int(a.red() + (b.red() - a.red()) * t),
        int(a.green() + (b.green() - a.green()) * t),
        int(a.blue() + (b.blue() - a.blue()) * t),
    )


# ====================================================================== botão principal
class PrimaryButton(QPushButton):
    """Ação principal: laranja sólido com texto escuro, hover por troca de cor e estado de carregamento."""

    def __init__(self, text: str = "", icon_name: str | None = None, parent=None):
        super().__init__(text, parent)
        self._icon_name = icon_name
        self._hover = 0.0
        self._pressed = False
        self._loading = False
        self._spin = 0.0
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(44)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self._hover_anim = QVariantAnimation(self, duration=theme.EASE_DURATION_FAST)
        self._hover_anim.setEasingCurve(ease())
        self._hover_anim.valueChanged.connect(self._set_hover)

        # O giro só existe enquanto há um download de fato em andamento.
        self._spin_timer = QTimer(self, interval=16)
        self._spin_timer.timeout.connect(self._tick_spin)

    def set_loading(self, loading: bool, text: str | None = None):
        self._loading = loading
        if text is not None:
            self.setText(text)
        self._spin_timer.start() if loading else self._spin_timer.stop()
        self.update()

    def is_loading(self) -> bool:
        return self._loading

    def _tick_spin(self):
        self._spin = (self._spin + 6) % 360
        self.update()

    def _set_hover(self, value):
        self._hover = float(value)
        self.update()

    def _animate_hover(self, target: float):
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover)
        self._hover_anim.setEndValue(target)
        self._hover_anim.start()

    def enterEvent(self, event):
        if self.isEnabled():
            self._animate_hover(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate_hover(0.0)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._pressed = True
        self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(event)

    def sizeHint(self) -> QSize:
        fm = self.fontMetrics()
        return QSize(fm.horizontalAdvance(self.text()) + 64, 44)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        if self._pressed:
            # Leve redução ao pressionar (≈0.98)
            dx, dy = rect.width() * 0.01, rect.height() * 0.01
            rect = rect.adjusted(dx, dy, -dx, -dy)
        radius = theme.RADIUS_CONTROL
        active = self.isEnabled() or self._loading

        if active:
            base = QColor(theme.ACCENT_PRESSED if self._pressed else theme.ACCENT)
            fill = _mix(base, QColor(theme.ACCENT_HOVER), self._hover * (0 if self._pressed else 1))
            fg = QColor(theme.ON_ACCENT)
        else:
            fill = QColor(theme.SURFACE_2)
            fg = QColor(theme.TEXT_3)

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        p.fillPath(path, fill)
        if active:
            # Realce superior discreto (inset 0 1px 0 rgba(255,255,255,0.12))
            p.save()
            p.setClipPath(path)
            p.setPen(QPen(QColor(255, 255, 255, 30), 1))
            p.drawLine(QPointF(rect.left() + radius, rect.top() + 1), QPointF(rect.right() - radius, rect.top() + 1))
            p.restore()

        font = QFont(self.font())
        font.setPixelSize(14)
        font.setWeight(QFont.Weight.DemiBold)
        p.setFont(font)
        text = self.text()
        fm = p.fontMetrics()
        text_w = fm.horizontalAdvance(text)
        icon_w = 16 if (self._loading or self._icon_name) else 0
        gap = 8 if icon_w and text else 0
        x = rect.center().x() - (icon_w + gap + text_w) / 2
        cy = rect.center().y()

        if self._loading:
            pen = QPen(fg, 1.5)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawArc(QRectF(x + 2, cy - 6, 12, 12), int(-self._spin * 16), 270 * 16)
        elif self._icon_name:
            p.drawPixmap(QPointF(x, cy - 8), icons.pixmap(self._icon_name, fg.name(), 16))

        p.setPen(fg)
        p.drawText(QRectF(x + icon_w + gap, rect.top(), text_w + 2, rect.height()), Qt.AlignmentFlag.AlignVCenter, text)
        p.end()


GlowButton = PrimaryButton  # nome antigo, mantido para compatibilidade


# ====================================================================== progresso
class AnimatedProgressBar(QProgressBar):
    """Barra fina com o valor interpolado. Sem valor ainda, mostra um segmento indeterminado."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0, 100)
        self.setTextVisible(False)
        self.setFixedHeight(4)
        self._display = 0.0
        self._phase = 0.0
        self._busy = False

        self._anim = QPropertyAnimation(self, b"displayValue", self)
        self._anim.setDuration(theme.EASE_DURATION_ENTER)
        self._anim.setEasingCurve(ease())

        self._timer = QTimer(self, interval=33)  # só no modo indeterminado
        self._timer.timeout.connect(self._tick)

    def _get_display(self) -> float:
        return self._display

    def _set_display(self, value: float):
        self._display = float(value)
        self._sync_timer()
        self.update()

    displayValue = Property(float, _get_display, _set_display)

    def setValue(self, value: int):
        previous = self.value()
        super().setValue(value)
        self._anim.stop()
        if value < previous or value == 0:
            self._set_display(value)
        else:
            self._anim.setStartValue(self._display)
            self._anim.setEndValue(float(value))
            self._anim.start()

    def set_busy(self, busy: bool):
        self._busy = busy
        self._sync_timer()
        self.update()

    def _indeterminate(self) -> bool:
        return self._busy and self._display <= 0.001

    def _sync_timer(self):
        if self._indeterminate() and self.isVisible():
            if not self._timer.isActive():
                self._timer.start()
        else:
            self._timer.stop()

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_timer()

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)

    def _tick(self):
        self._phase = (self._phase + 0.015) % 1.0
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect())
        r = rect.height() / 2
        track = QPainterPath()
        track.addRoundedRect(rect, r, r)
        p.fillPath(track, QColor(theme.SURFACE_2))

        if self._indeterminate():
            seg_w = rect.width() * 0.24
            x = -seg_w + (rect.width() + seg_w) * self._phase
            p.setClipPath(track)
            p.fillRect(QRectF(x, 0, seg_w, rect.height()), QColor(theme.TEXT_3))
            p.end()
            return

        span = max(1, self.maximum() - self.minimum())
        fraction = max(0.0, min(1.0, (self._display - self.minimum()) / span))
        if fraction > 0:
            fill = QPainterPath()
            fill.addRoundedRect(QRectF(0, 0, max(rect.height(), rect.width() * fraction), rect.height()), r, r)
            p.fillPath(fill, QColor(theme.ACCENT))
        p.end()


# ====================================================================== segmentado
class SegmentedControl(QWidget):
    """Seletor segmentado com indicador que desliza entre as opções.

    Expõe a API do QComboBox usada pela aplicação: ``addItem``, ``currentData``,
    ``currentIndex``, ``setCurrentIndex``, ``count``, ``itemData``, ``findData`` e
    o sinal ``currentIndexChanged``.
    """

    currentIndexChanged = Signal(int)
    OUTER_RADIUS = 10
    PADDING = 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list[tuple[str, object, str | None]] = []
        self._buttons: list[QPushButton] = []
        self._index = -1
        self._indicator_x = 0.0
        self.setFixedHeight(40)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(self.PADDING, self.PADDING, self.PADDING, self.PADDING)
        self._layout.setSpacing(4)
        self._anim = QVariantAnimation(self, duration=200)
        self._anim.setEasingCurve(ease())
        self._anim.valueChanged.connect(self._on_anim)

    def addItem(self, label: str, data=None, icon_name: str | None = None):
        index = len(self._items)
        self._items.append((label, data, icon_name))
        button = QPushButton(label)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFlat(True)
        button.setCheckable(True)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        button.setStyleSheet(
            "QPushButton { background: transparent; border: none; color: %s; font-size: 14px; font-weight: 500; }"
            "QPushButton:checked { color: %s; }"
            "QPushButton:hover:!checked { color: %s; }" % (theme.TEXT_2, theme.TEXT, theme.TEXT)
        )
        if icon_name:
            button.setIconSize(icons.icon_size(16))
        button.clicked.connect(lambda _=False, i=index: self.setCurrentIndex(i))
        self._buttons.append(button)
        self._layout.addWidget(button)
        if self._index < 0:
            self.setCurrentIndex(0, animate=False)
        else:
            self._refresh_icons()

    def _refresh_icons(self):
        for i, button in enumerate(self._buttons):
            icon_name = self._items[i][2]
            if icon_name:
                color = theme.TEXT if i == self._index else theme.TEXT_3
                button.setIcon(icons.icon(icon_name, color, 16))

    def count(self) -> int:
        return len(self._items)

    def itemData(self, index: int):
        return self._items[index][1]

    def currentIndex(self) -> int:
        return self._index

    def currentData(self):
        return self._items[self._index][1] if 0 <= self._index < len(self._items) else None

    def findData(self, data) -> int:
        for i, item in enumerate(self._items):
            if item[1] == data:
                return i
        return -1

    def setCurrentIndex(self, index: int, animate: bool = True):
        if not 0 <= index < len(self._items):
            return
        changed = index != self._index
        self._index = index
        for i, button in enumerate(self._buttons):
            button.setChecked(i == index)
        self._refresh_icons()
        target = self._target_x()
        if animate and self.isVisible():
            self._anim.stop()
            self._anim.setStartValue(self._indicator_x)
            self._anim.setEndValue(target)
            self._anim.start()
        else:
            self._indicator_x = target
            self.update()
        if changed:
            self.currentIndexChanged.emit(index)

    def _target_x(self) -> float:
        if not 0 <= self._index < len(self._buttons):
            return 0.0
        return float(self._buttons[self._index].geometry().x())

    def _on_anim(self, value):
        self._indicator_x = float(value)
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self._snap)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._snap)

    def _snap(self):
        if self._anim.state() != QVariantAnimation.State.Running:
            self._indicator_x = self._target_x()
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        outer = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(QPen(QColor(237, 237, 237, 20), 1))
        p.setBrush(QColor(theme.BG))
        p.drawRoundedRect(outer, self.OUTER_RADIUS, self.OUTER_RADIUS)
        if 0 <= self._index < len(self._buttons):
            b = self._buttons[self._index].geometry()
            pill = QRectF(self._indicator_x, b.y(), b.width(), b.height())
            inner = max(4, self.OUTER_RADIUS - self.PADDING)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(theme.SURFACE_3 if self.isEnabled() else theme.SURFACE_2))
            p.drawRoundedRect(pill, inner, inner)
            # Realce superior fino no item ativo
            p.setPen(QPen(QColor(255, 255, 255, 26), 1))
            p.drawLine(QPointF(pill.left() + inner, pill.top() + 0.5), QPointF(pill.right() - inner, pill.top() + 0.5))
        p.end()


# ====================================================================== indicador de status
class StatusDot(QWidget):
    """Ponto de status. Estático; pulsa devagar apenas enquanto algo está de fato em andamento."""

    COLORS = {
        "idle": theme.POSITIVE,
        "busy": theme.ACCENT,
        "success": theme.POSITIVE,
        "error": theme.NEGATIVE,
        "warning": theme.CAUTION,
    }

    def __init__(self, size: int = 8, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._state = "idle"
        self._opacity = 1.0
        self._anim = QVariantAnimation(self, startValue=1.0, endValue=1.0, duration=1400)
        self._anim.setKeyValueAt(0.5, 0.45)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._anim.setLoopCount(-1)
        self._anim.valueChanged.connect(self._on_anim)

    def set_state(self, state: str):
        self._state = state if state in self.COLORS else "idle"
        if self._state == "busy":
            if self._anim.state() != QVariantAnimation.State.Running:
                self._anim.start()
        else:
            self._anim.stop()
            self._opacity = 1.0
        self.update()

    def state(self) -> str:
        return self._state

    def _on_anim(self, value):
        self._opacity = float(value)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(self.COLORS[self._state])
        color.setAlphaF(self._opacity)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color)
        r = min(self.width(), self.height()) / 2
        p.drawEllipse(QPointF(self.width() / 2, self.height() / 2), r, r)
        p.end()


# ====================================================================== transição de páginas
class FadeStackedWidget(QStackedWidget):
    """QStackedWidget com um fade curto na página que entra (a única entrada animada)."""

    def __init__(self, parent=None, duration: int = 200):
        super().__init__(parent)
        self._duration = duration
        self._anim: QPropertyAnimation | None = None

    def setCurrentIndex(self, index: int):
        if index == self.currentIndex():
            return
        super().setCurrentIndex(index)
        widget = self.currentWidget()
        if widget is None:
            return
        effect = QGraphicsOpacityEffect(widget)
        effect.setOpacity(0.0)
        widget.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(self._duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(ease())
        # Remove o efeito ao final para a página voltar à renderização normal.
        anim.finished.connect(lambda w=widget: w.setGraphicsEffect(None))
        if self._anim is not None:
            self._anim.stop()
        self._anim = anim
        anim.start()


# ====================================================================== logotipo
class LogoMark(QWidget):
    """Marca plana: seta de download sobre uma linha de base, em laranja sólido."""

    def __init__(self, size: int = 20, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = float(min(self.width(), self.height()))
        pen = QPen(QColor(theme.ACCENT), s * 0.12)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        cx = s / 2
        p.drawLine(QPointF(cx, s * 0.14), QPointF(cx, s * 0.62))
        p.drawPolyline([QPointF(s * 0.28, s * 0.42), QPointF(cx, s * 0.64), QPointF(s * 0.72, s * 0.42)])
        p.drawLine(QPointF(s * 0.16, s * 0.86), QPointF(s * 0.84, s * 0.86))
        p.end()
