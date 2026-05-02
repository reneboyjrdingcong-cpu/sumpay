"""SplashScreen — Screen 1: full white, centered greeting, click to advance."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from gui import theme


class _HintDot(QWidget):
    """Small pulsing dot used as a 'click to begin' affordance."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(10, 10)
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
        c = QColor(161, 161, 166)  # TEXT_HINT
        c.setAlphaF(max(0.0, min(1.0, self._opacity)))
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(self.rect())
        p.end()


class SplashScreen(QWidget):
    advance = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, theme.SCREEN_PADDING_TOP, 0, theme.SCREEN_PADDING_BOTTOM)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # ── Wordmark (top) ───────────────────────────────────────────── #
        wordmark = QLabel("SUMPAY")
        wordmark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wordmark.setStyleSheet(
            f"color: {theme.TEXT_HINT}; "
            f"font-size: {theme.FONT_SIZE_HINT}px; "
            f"font-weight: {theme.WEIGHT_MEDIUM}; "
            "letter-spacing: 4px; "
            "background: transparent;"
        )
        root.addWidget(wordmark)
        root.addStretch(1)

        # ── Greeting block ───────────────────────────────────────────── #
        greeting = QLabel("Hello.")
        greeting.setAlignment(Qt.AlignmentFlag.AlignCenter)
        greeting.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; "
            f"font-size: {theme.FONT_SIZE_DISPLAY}px; "
            f"font-weight: {theme.WEIGHT_LIGHT}; "
            "background: transparent;"
        )
        root.addWidget(greeting)

        root.addSpacing(theme.SPACE_SM)

        subtitle = QLabel("Welcome to Sumpay")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(
            f"color: {theme.TEXT_SECONDARY}; "
            f"font-size: {theme.FONT_SIZE_BODY_LG}px; "
            f"font-weight: {theme.WEIGHT_LIGHT}; "
            "background: transparent;"
        )
        root.addWidget(subtitle)

        root.addStretch(1)

        # ── Click-to-begin hint with pulsing dot ─────────────────────── #
        hint_row = QHBoxLayout()
        hint_row.setContentsMargins(0, 0, 0, 0)
        hint_row.setSpacing(theme.SPACE_XS)
        hint_row.addStretch()

        self._dot = _HintDot()
        hint_row.addWidget(self._dot, alignment=Qt.AlignmentFlag.AlignVCenter)

        hint_lbl = QLabel("Click anywhere to begin")
        hint_lbl.setObjectName("hintLabel")
        hint_lbl.setStyleSheet(
            f"color: {theme.TEXT_HINT}; "
            f"font-size: {theme.FONT_SIZE_HINT}px; "
            f"font-weight: {theme.WEIGHT_LIGHT}; "
            "background: transparent;"
        )
        hint_row.addWidget(hint_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)
        hint_row.addStretch()

        root.addLayout(hint_row)
        root.addStretch(1)

        # Pulse animation for the hint dot
        self._anim = QPropertyAnimation(self._dot, b"opacity", self)
        self._anim.setDuration(1400)
        self._anim.setStartValue(0.25)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.SineCurve)
        self._anim.setLoopCount(-1)
        self._anim.start()

    def mousePressEvent(self, event) -> None:
        self.advance.emit()
