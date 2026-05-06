"""StatusPill — rounded glass pill with a colored dot and a label.

Used for live indicators that should sit near content rather than crowd the
header strip. The dot pulses opacity 0.3 → 1.0 on a sine loop so it reads as
"live" without being noisy.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

from gui import theme


class _PulseDot(QWidget):
    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(10, 10)
        self._color = QColor(color)
        self._opacity = 1.0

        self._anim = QPropertyAnimation(self, b"opacity", self)
        self._anim.setDuration(theme.PULSE_DURATION_MS)
        self._anim.setStartValue(0.3)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.SineCurve)
        self._anim.setLoopCount(-1)

    def start(self) -> None:
        self._anim.start()

    def stop(self) -> None:
        self._anim.stop()
        self._opacity = 0.0
        self.update()

    def get_opacity(self) -> float:
        return self._opacity

    def set_opacity(self, v: float) -> None:
        self._opacity = v
        self.update()

    opacity = property(get_opacity, set_opacity)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor(self._color)
        c.setAlphaF(self._opacity)
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(self.rect())
        p.end()


class StatusPill(QWidget):
    def __init__(
        self,
        label: str,
        dot_color: str = theme.STATUS_LIVE_DOT,
        pulse: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("statusPillLive")
        self.setStyleSheet(
            f"QWidget#statusPillLive {{"
            f"  background-color: {theme.BG_GLASS_DEEP};"
            f"  border-radius: 14px;"
            f"}}"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 14, 6)
        layout.setSpacing(8)

        self._dot = _PulseDot(dot_color)
        self._lbl = QLabel(label)
        self._lbl.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; "
            f"font-size: {theme.FONT_SIZE_HINT}px; "
            f"font-weight: {theme.WEIGHT_REGULAR}; "
            "background: transparent;"
        )

        layout.addWidget(self._dot, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._lbl, alignment=Qt.AlignmentFlag.AlignVCenter)

        if pulse:
            self._dot.start()

    def set_label(self, text: str) -> None:
        self._lbl.setText(text)

    def start(self) -> None:
        self._dot.start()

    def stop(self) -> None:
        self._dot.stop()
