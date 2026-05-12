"""SplashScreen — Screen 1: warm off-white canvas, centered greeting, click to advance."""
from __future__ import annotations

import math

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from gui import theme


class _HintDot(QWidget):
    """12×12 teal circle that pulses in both opacity (0.40↔1.00) and scale (0.94↔1.04)
    with a single sine wave so the two properties stay perfectly in phase."""

    _DURATION_MS = 1400
    _TICK_MS = 16

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self._elapsed = 0
        self._opacity = 0.40
        self._scale = 0.94

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(self._TICK_MS)

    def _tick(self) -> None:
        self._elapsed = (self._elapsed + self._TICK_MS) % self._DURATION_MS
        s = math.sin(self._elapsed / self._DURATION_MS * math.pi)  # 0→1→0 per loop
        self._opacity = 0.40 + 0.60 * s
        self._scale = 0.94 + 0.10 * s
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.translate(6.0, 6.0)
        p.scale(self._scale, self._scale)
        c = QColor(theme.ACCENT_PRIMARY)
        c.setAlphaF(self._opacity)
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(-6, -6, 12, 12)
        p.end()


class SplashScreen(QWidget):
    advance = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        root = QVBoxLayout(self)
        # Padding: 32 top · 48 left · 48 right · 48 bottom
        root.setContentsMargins(48, 32, 48, 48)
        root.setSpacing(0)

        # ── Zone 1 — Wordmark ─────────────────────────────────────────── #
        wordmark = QLabel("SUMPAY")
        wordmark.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        wordmark.setStyleSheet(
            "color: %s;"
            "font-size: 13px;"
            "font-weight: 600;"
            "letter-spacing: 4px;"
            "background: transparent;"
            % theme.TEXT_HINT
        )
        root.addWidget(wordmark)

        # Stretch absorbs space between zone 1 and zone 2
        root.addStretch(1)

        # ── Zone 2 — Greeting block ───────────────────────────────────── #
        greeting = QLabel("Hello.")
        greeting.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        greeting.setStyleSheet(
            "color: %s;"
            "font-size: 96px;"
            "font-weight: 300;"
            "letter-spacing: -4px;"
            "line-height: 1.0;"
            "background: transparent;"
            % theme.TEXT_PRIMARY
        )
        root.addWidget(greeting)

        root.addSpacing(24)

        subtitle_en = QLabel("Welcome. We'll help you talk with your doctor.")
        subtitle_en.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        subtitle_en.setStyleSheet(
            "color: %s;"
            "font-size: 22px;"
            "font-weight: 400;"
            "background: transparent;"
            % theme.TEXT_SECONDARY
        )
        root.addWidget(subtitle_en)

        root.addSpacing(14)

        subtitle_pt = QLabel("Tabangan ka namo makig-storya sa imohang doctor.")
        subtitle_pt.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        subtitle_pt.setStyleSheet(
            "color: %s;"
            "font-size: 15px;"
            "font-weight: 400;"
            "font-style: italic;"
            "background: transparent;"
            % theme.TEXT_HINT
        )
        root.addWidget(subtitle_pt)

        # Stretch absorbs space between zone 2 and zone 3
        root.addStretch(1)

        # ── Zone 3 — Bottom prompt row ────────────────────────────────── #
        hint_row = QHBoxLayout()
        hint_row.setContentsMargins(0, 0, 0, 0)
        hint_row.setSpacing(12)
        hint_row.addStretch()

        self._dot = _HintDot()
        hint_row.addWidget(self._dot, alignment=Qt.AlignmentFlag.AlignVCenter)

        hint_lbl = QLabel("Touch anywhere to begin")
        hint_lbl.setStyleSheet(
            "color: %s;"
            "font-size: 15px;"
            "font-weight: 500;"
            "background: transparent;"
            % theme.TEXT_SECONDARY
        )
        hint_row.addWidget(hint_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)
        hint_row.addStretch()

        root.addLayout(hint_row)

    def mousePressEvent(self, event) -> None:
        self.advance.emit()
