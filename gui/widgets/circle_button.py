"""CircleButton — 64×64 circle button with a side label.

Variant colors follow the Clinical Light palette (gui/theme.py):
    confirm   → teal   (proceed / success)
    retry     → brick  (destructive / restart)
    edit      → amber  (caution / modify)
    secondary → white  (neutral; e.g. Replay paired with a primary action)

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


_BUTTON_PX = 64
_BUTTON_RADIUS = theme.RADIUS_CIRCLE


# Token-driven variant palette — base / hover / pressed
_VARIANT_STYLES = {
    "confirm": (theme.ACCENT_PRIMARY, theme.ACCENT_PRIMARY_HOVER, theme.ACCENT_PRIMARY_PRESSED),
    "retry":   (theme.ACCENT_DANGER,  theme.ACCENT_DANGER_HOVER,  theme.ACCENT_DANGER_PRESSED),
    "edit":    (theme.ACCENT_EDIT,    theme.ACCENT_EDIT_HOVER,    theme.ACCENT_EDIT_PRESSED),
}


def _variant_qss(base: str, hover: str, pressed: str) -> str:
    return (
        f"QPushButton {{"
        f"  background-color: {base};"
        f"  border: none;"
        f"  border-radius: {_BUTTON_RADIUS}px;"
        f"  min-width: {_BUTTON_PX}px; min-height: {_BUTTON_PX}px;"
        f"  max-width: {_BUTTON_PX}px; max-height: {_BUTTON_PX}px;"
        f"  color: #FFFFFF;"
        f"}}"
        f"QPushButton:hover   {{ background-color: {hover}; }}"
        f"QPushButton:pressed {{ background-color: {pressed}; }}"
    )


def _secondary_qss() -> str:
    """White pill with hairline + dark text — neutral pairing for primary actions."""
    return (
        f"QPushButton {{"
        f"  background-color: {theme.BG_GLASS};"
        f"  border: 1px solid {theme.BORDER_HAIRLINE};"
        f"  border-radius: {_BUTTON_RADIUS}px;"
        f"  min-width: {_BUTTON_PX}px; min-height: {_BUTTON_PX}px;"
        f"  max-width: {_BUTTON_PX}px; max-height: {_BUTTON_PX}px;"
        f"  color: {theme.TEXT_PRIMARY};"
        f"}}"
        f"QPushButton:hover   {{ background-color: {theme.BG_GLASS_DEEP}; }}"
        f"QPushButton:pressed {{ background-color: {theme.BORDER_HAIRLINE}; }}"
    )


class CircleButton(QWidget):
    clicked = pyqtSignal()

    def __init__(self, label: str, variant: str = "default", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self._btn = QPushButton(parent=self)
        self._btn.setFixedSize(_BUTTON_PX, _BUTTON_PX)
        self._btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn.clicked.connect(self.clicked)

        if variant in _VARIANT_STYLES:
            self._btn.setObjectName(f"circleBtn{variant.capitalize()}")
            self._btn.setStyleSheet(_variant_qss(*_VARIANT_STYLES[variant]))
        elif variant == "secondary":
            self._btn.setObjectName("circleBtnSecondary")
            self._btn.setStyleSheet(_secondary_qss())
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
