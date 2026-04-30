"""AudioScreen — Screen 4: TTS playback indicator, click to return to splash."""
from __future__ import annotations

import math

from PyQt6.QtCore import (
    Qt, pyqtSignal, pyqtSlot, QPropertyAnimation, QEasingCurve,
    QRectF, QSize,
)
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy

from gui import theme
from gui.widgets.glass_card import GlassCard


class _WaveformCard(QWidget):
    """Small card that draws a waveform-style static bar with QPainter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(349, 91)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Card background
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 20, 20)
        p.fillPath(path, QColor(245, 245, 247, 217))

        # Three thin horizontal rounded bars (waveform symbol)
        pen = QPen(QColor(29, 29, 31), 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)

        cx = self.width() / 2
        cy = self.height() / 2
        widths = [120, 80, 50]
        offsets = [-18, 0, 18]
        for w, dy in zip(widths, offsets):
            y = cy + dy
            p.drawLine(int(cx - w / 2), int(y), int(cx + w / 2), int(y))

        p.end()


class _PulseIndicator(QWidget):
    """28×28 circle that pulses opacity while TTS is busy."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(28, 28)
        self._opacity = 1.0

    def set_opacity(self, v: float) -> None:
        self._opacity = v
        self.update()

    def get_opacity(self) -> float:
        return self._opacity

    opacity = property(get_opacity, set_opacity)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(29, 29, 31)
        color.setAlphaF(self._opacity * 0.8)
        p.setBrush(color)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(self.rect())
        p.end()


class AudioScreen(QWidget):
    done = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._tts_busy = False
        self._finished = False

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.setSpacing(16)

        self._pulse = _PulseIndicator(self)
        root.addWidget(self._pulse, alignment=Qt.AlignmentFlag.AlignCenter)

        self._waveform = _WaveformCard(self)
        root.addWidget(self._waveform, alignment=Qt.AlignmentFlag.AlignCenter)

        # Pulse animation
        self._anim = QPropertyAnimation(self._pulse, b"opacity", self)
        self._anim.setDuration(900)
        self._anim.setStartValue(0.25)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.SineCurve)
        self._anim.setLoopCount(-1)

    # ------------------------------------------------------------------ #

    @pyqtSlot(bool)
    def on_busy(self, busy: bool) -> None:
        self._tts_busy = busy
        if busy:
            self._finished = False
            self._anim.start()
        else:
            self._anim.stop()
            self._pulse.set_opacity(0.3)
            self._finished = True

    def reset(self) -> None:
        self._finished = False
        self._tts_busy = False

    def mousePressEvent(self, event) -> None:
        if self._finished:
            self.done.emit()
