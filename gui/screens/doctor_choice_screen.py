"""DoctorChoiceScreen — Screen 6: record speech or type message."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QPainterPath
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect,
)

from gui import theme
from gui.widgets.glass_card import GlassCard


# ---------------------------------------------------------------------------
# Painter-drawn icons
# ---------------------------------------------------------------------------

class _MicIcon(QWidget):
    """Thin-stroke microphone."""

    def __init__(self, size: int = 80, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(theme.TEXT_PRIMARY), 2.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        w, h = self.width(), self.height()
        cx = w / 2

        # Mic capsule (rounded rect)
        cap_w, cap_h = w * 0.28, h * 0.42
        cap_x = cx - cap_w / 2
        cap_y = h * 0.06
        p.drawRoundedRect(int(cap_x), int(cap_y), int(cap_w), int(cap_h), int(cap_w / 2), int(cap_w / 2))

        # Arch
        arch = QPainterPath()
        r = cap_w * 0.9
        arch.moveTo(cx - r, h * 0.54)
        arch.cubicTo(cx - r, h * 0.80, cx + r, h * 0.80, cx + r, h * 0.54)
        p.drawPath(arch)

        # Stand
        p.drawLine(int(cx), int(h * 0.78), int(cx), int(h * 0.92))
        p.drawLine(int(cx - r * 0.7), int(h * 0.92), int(cx + r * 0.7), int(h * 0.92))

        p.end()


class _PencilIcon(QWidget):
    """Thin-stroke pencil / edit."""

    def __init__(self, size: int = 80, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(theme.TEXT_PRIMARY), 2.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        w, h = self.width(), self.height()

        # Diagonal pencil body
        path = QPainterPath()
        path.moveTo(w * 0.25, h * 0.82)
        path.lineTo(w * 0.72, h * 0.22)
        path.lineTo(w * 0.82, h * 0.32)
        path.lineTo(w * 0.35, h * 0.92)
        path.closeSubpath()
        p.drawPath(path)

        # Eraser top
        p.drawLine(int(w * 0.72), int(h * 0.22), int(w * 0.78), int(h * 0.16))

        # Bottom baseline
        p.drawLine(int(w * 0.18), int(h * 0.88), int(w * 0.42), int(h * 0.96))

        p.end()


# ---------------------------------------------------------------------------
# Choice tile
# ---------------------------------------------------------------------------

class _ChoiceTile(GlassCard):
    """Large clickable glass tile: icon above caption."""

    def __init__(self, icon: QWidget, caption: str, parent=None):
        super().__init__(parent, deep=True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(260, 260)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(24)
        layout.setContentsMargins(32, 40, 32, 40)

        layout.addStretch()
        layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel(caption)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            f"color: {theme.TEXT_SECONDARY}; "
            f"font-size: {theme.FONT_SIZE_BODY}px; "
            "font-weight: 300; "
            "background: transparent;"
        )
        layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(40)
        self._shadow.setOffset(0, 8)
        self._shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(self._shadow)

    def enterEvent(self, event) -> None:
        self._shadow.setBlurRadius(60)
        self._shadow.setColor(QColor(0, 0, 0, 32))

    def leaveEvent(self, event) -> None:
        self._shadow.setBlurRadius(40)
        self._shadow.setColor(QColor(0, 0, 0, 20))


# ---------------------------------------------------------------------------
# Screen
# ---------------------------------------------------------------------------

class DoctorChoiceScreen(QWidget):
    record_clicked = pyqtSignal()
    type_clicked   = pyqtSignal()
    back           = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.setContentsMargins(60, 32, 60, 60)
        root.setSpacing(0)

        # ── Back button ──────────────────────────────────────────────────── #
        top_bar = QHBoxLayout()
        back_btn = QPushButton("‹ Back")
        back_btn.setFlat(True)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet(
            f"color: {theme.TEXT_HINT}; "
            f"font-size: {theme.FONT_SIZE_HINT}px; "
            "font-weight: 300; background: transparent; border: none;"
        )
        back_btn.clicked.connect(self.back)
        top_bar.addWidget(back_btn)
        top_bar.addStretch()
        root.addLayout(top_bar)

        root.addStretch(2)

        header = QLabel("What would you like to do?")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; "
            f"font-size: {theme.FONT_SIZE_HEADER}px; "
            "font-weight: 300; "
            "background: transparent; "
            "margin-bottom: 56px;"
        )
        root.addWidget(header)

        tiles_row = QHBoxLayout()
        tiles_row.setSpacing(80)
        tiles_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._record_tile = _ChoiceTile(_MicIcon(72), "Record speech")
        self._type_tile   = _ChoiceTile(_PencilIcon(72), "Type message")

        self._record_tile.mousePressEvent = lambda _: self.record_clicked.emit()
        self._type_tile.mousePressEvent   = lambda _: self.type_clicked.emit()

        tiles_row.addWidget(self._record_tile)
        tiles_row.addWidget(self._type_tile)

        root.addLayout(tiles_row)
        root.addStretch(3)
