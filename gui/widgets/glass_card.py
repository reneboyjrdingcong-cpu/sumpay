"""GlassCard — reusable rounded translucent surface with soft shadow."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QFrame, QGraphicsDropShadowEffect


class GlassCard(QFrame):
    def __init__(self, parent=None, deep: bool = False):
        super().__init__(parent)
        self.setObjectName("glassCardDeep" if deep else "glassCard")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(shadow)
