"""SplashScreen — Screen 1: full white, centered greeting, click to advance."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont

from gui import theme


class SplashScreen(QWidget):
    advance = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(0)

        greeting = QLabel("Hello.")
        greeting.setAlignment(Qt.AlignmentFlag.AlignCenter)
        greeting.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; "
            f"font-size: {theme.FONT_SIZE_GREETING}px; "
            "font-weight: 300; "
            "background: transparent;"
        )

        subtitle = QLabel("Welcome to Sumpay")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(
            f"color: {theme.TEXT_SECONDARY}; "
            "font-size: 18px; "
            "font-weight: 300; "
            "background: transparent; "
            "margin-top: 12px;"
        )

        hint = QLabel("Click to begin")
        hint.setObjectName("hintLabel")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(
            f"color: {theme.TEXT_HINT}; "
            f"font-size: {theme.FONT_SIZE_HINT}px; "
            "font-weight: 300; "
            "background: transparent; "
            "margin-top: 48px;"
        )

        layout.addStretch(2)
        layout.addWidget(greeting)
        layout.addWidget(subtitle)
        layout.addStretch(1)
        layout.addWidget(hint)
        layout.addStretch(1)

    def mousePressEvent(self, event) -> None:
        self.advance.emit()
