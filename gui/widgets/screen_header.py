"""ScreenHeader — shared back-button + optional title row for patient-flow screens.

Replaces the four near-duplicate top bars in splash/camera/confirm/audio. A
screen connects to the `back` signal and optionally passes a `title`.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from gui import theme


class ScreenHeader(QWidget):
    back = pyqtSignal()

    def __init__(self, title: str | None = None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(theme.SPACE_SM)

        self._back_btn = QPushButton("‹ Back")
        self._back_btn.setFlat(True)
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.setStyleSheet(
            f"color: {theme.TEXT_HINT}; "
            f"font-size: {theme.FONT_SIZE_HINT}px; "
            f"font-weight: {theme.WEIGHT_LIGHT}; "
            "background: transparent; border: none;"
        )
        self._back_btn.clicked.connect(self.back)
        layout.addWidget(self._back_btn)

        if title:
            self._title_lbl = QLabel(title)
            self._title_lbl.setStyleSheet(
                f"color: {theme.TEXT_PRIMARY}; "
                f"font-size: {theme.FONT_SIZE_BODY_LG}px; "
                f"font-weight: {theme.WEIGHT_REGULAR}; "
                "background: transparent;"
            )
            layout.addSpacing(theme.SPACE_MD)
            layout.addWidget(self._title_lbl)
        else:
            self._title_lbl = None

        layout.addStretch()
