"""CircleButton — 56×56 circle button with a side label."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

from gui import theme


_VARIANT_OBJ = {
    "confirm": "circleBtnConfirm",
    "retry":   "circleBtnRetry",
    "edit":    "circleBtnEdit",
    "default": "circleBtn",
}


class CircleButton(QWidget):
    clicked = pyqtSignal()

    def __init__(self, label: str, variant: str = "default", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self._btn = QPushButton(parent=self)
        self._btn.setObjectName(_VARIANT_OBJ.get(variant, "circleBtn"))
        self._btn.setFixedSize(56, 56)
        self._btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn.clicked.connect(self.clicked)

        shadow = QGraphicsDropShadowEffect(self._btn)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 20))
        self._btn.setGraphicsEffect(shadow)

        lbl = QLabel(label, self)
        lbl.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; font-size: {theme.FONT_SIZE_BODY}px; "
            "font-weight: 400; background: transparent;"
        )

        layout.addWidget(self._btn)
        layout.addWidget(lbl)
        layout.addStretch()
