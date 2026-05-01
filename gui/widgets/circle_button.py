"""CircleButton — 56×56 circle button with a side label.

Variant colors follow macOS traffic-light convention:
    confirm → green   (proceed / success)
    retry   → red     (destructive / restart)
    edit    → yellow  (caution / modify)

The variant style is applied as an inline stylesheet on the inner QPushButton
so it always wins the QSS cascade regardless of when the global stylesheet
is loaded relative to widget construction.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

from gui import theme


# macOS traffic-light palette — base / hover / pressed
_VARIANT_STYLES = {
    "confirm": ("#34C759", "#30D158", "#248A3D"),  # systemGreen
    "retry":   ("#FF3B30", "#FF453A", "#D70015"),  # systemRed
    "edit":    ("#FFCC00", "#FFD60A", "#B58B00"),  # systemYellow
}


def _variant_qss(base: str, hover: str, pressed: str) -> str:
    return (
        f"QPushButton {{"
        f"  background-color: {base};"
        f"  border: none;"
        f"  border-radius: 28px;"
        f"  min-width: 56px; min-height: 56px;"
        f"  max-width: 56px; max-height: 56px;"
        f"}}"
        f"QPushButton:hover   {{ background-color: {hover}; }}"
        f"QPushButton:pressed {{ background-color: {pressed}; }}"
    )


class CircleButton(QWidget):
    clicked = pyqtSignal()

    def __init__(self, label: str, variant: str = "default", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self._btn = QPushButton(parent=self)
        self._btn.setFixedSize(56, 56)
        self._btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn.clicked.connect(self.clicked)

        if variant in _VARIANT_STYLES:
            self._btn.setObjectName(f"circleBtn{variant.capitalize()}")
            self._btn.setStyleSheet(_variant_qss(*_VARIANT_STYLES[variant]))
        else:
            self._btn.setObjectName("circleBtn")

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
