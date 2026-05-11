"""SpeakerHalo — circular speaker button with three rippling rings.

Pure QPainter + QPropertyAnimation. No images, no QSS keyframes.
"""
from __future__ import annotations

from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QTimer, pyqtProperty, QSize, QPointF,
)
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath
from PyQt6.QtWidgets import QWidget, QPushButton

from gui import theme


class _SpeakerButton(QPushButton):
    """Circular button that paints a flat 2-D speaker cone instead of an emoji.

    Icon is sized independently of the button so it has clean breathing room
    inside the circle (icon ≈ 40% of button — standard for circular icon buttons).
    """

    BUTTON_SIZE = 220
    ICON_SIZE   = 88   # 40% of BUTTON_SIZE

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self.BUTTON_SIZE, self.BUTTON_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

    def paintEvent(self, _ev) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0
        r = w / 2.0 - 1

        # Circular background — responds to hover / press
        if self.isDown():
            bg = QColor(theme.BORDER_HAIRLINE)
        elif self.underMouse():
            bg = QColor(theme.BG_GLASS_DEEP)
        else:
            bg = QColor(theme.BG_GLASS)

        p.setBrush(bg)
        p.setPen(QPen(QColor(theme.BORDER_HAIRLINE), 1))
        p.drawEllipse(QPointF(cx, cy), r, r)

        # Speaker glyph — drawn in its own 120-unit viewbox, centered in button
        s  = self.ICON_SIZE / 120.0
        ox = cx - self.ICON_SIZE / 2.0
        oy = cy - self.ICON_SIZE / 2.0

        def x(v: float) -> float: return ox + v * s
        def y(v: float) -> float: return oy + v * s

        pen_w = max(1.5, self.ICON_SIZE * 0.035)
        pen = QPen(QColor("#000000"), pen_w)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        cone = QPainterPath()
        cone.moveTo(x(30), y(45))
        cone.lineTo(x(42), y(45))
        cone.lineTo(x(62), y(28))
        cone.lineTo(x(62), y(92))
        cone.lineTo(x(42), y(75))
        cone.lineTo(x(30), y(75))
        cone.cubicTo(x(28), y(75), x(26), y(73), x(26), y(71))
        cone.lineTo(x(26), y(49))
        cone.cubicTo(x(26), y(47), x(28), y(45), x(30), y(45))
        cone.closeSubpath()
        p.drawPath(cone)

        inner = QPainterPath()
        inner.moveTo(x(76), y(42))
        inner.cubicTo(x(82), y(48), x(82), y(72), x(76), y(78))
        p.drawPath(inner)

        outer = QPainterPath()
        outer.moveTo(x(86), y(32))
        outer.cubicTo(x(96), y(42), x(96), y(78), x(86), y(88))
        p.drawPath(outer)

        p.end()


class _RippleRing(QWidget):
    """One animated stroke-only circle. progress 0→1 maps to scale + fade."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._progress = 0.0
        self._anim = QPropertyAnimation(self, b"progress", self)
        self._anim.setDuration(1500)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setLoopCount(-1)
        self._anim.setEasingCurve(QEasingCurve.Type.Linear)

    def get_progress(self) -> float:
        return self._progress

    def set_progress(self, v: float) -> None:
        self._progress = v
        self.update()

    progress = pyqtProperty(float, fget=get_progress, fset=set_progress)

    def start(self, delay_ms: int = 0) -> None:
        QTimer.singleShot(delay_ms, self._anim.start)

    def stop(self) -> None:
        self._anim.stop()
        self._progress = 0.0
        self.update()

    def paintEvent(self, _ev) -> None:
        if self._progress <= 0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        scale = 0.9 + 0.35 * self._progress
        alpha = int(160 * (1.0 - self._progress))
        color = QColor("#000000")
        color.setAlpha(alpha)
        p.setPen(QPen(color, 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        r = self.rect()
        cx, cy = r.center().x(), r.center().y()
        radius = (min(r.width(), r.height()) / 2) * scale
        p.drawEllipse(int(cx - radius), int(cy - radius),
                      int(radius * 2), int(radius * 2))


class SpeakerHalo(QWidget):
    """Round speaker button + 3 rippling rings. Toggle via set_playing()."""

    SIZE = 280

    def __init__(self, on_click=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(self.SIZE, self.SIZE)
        self._rings = [_RippleRing(self) for _ in range(3)]
        for ring in self._rings:
            ring.setGeometry(0, 0, self.SIZE, self.SIZE)

        self._button = _SpeakerButton(self)
        self._button.setObjectName("speakerButton")
        btn_size = self._button.BUTTON_SIZE
        self._button.move((self.SIZE - btn_size) // 2, (self.SIZE - btn_size) // 2)
        self._button.raise_()
        if on_click is not None:
            self._button.clicked.connect(on_click)

        self._playing = False

    def sizeHint(self) -> QSize:
        return QSize(self.SIZE, self.SIZE)

    def set_playing(self, on: bool) -> None:
        if on == self._playing:
            return
        self._playing = on
        if on:
            for i, ring in enumerate(self._rings):
                ring.start(delay_ms=i * 500)
        else:
            for ring in self._rings:
                ring.stop()
