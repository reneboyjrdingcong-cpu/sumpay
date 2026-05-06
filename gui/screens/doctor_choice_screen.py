"""DoctorChoiceScreen — Screen 6: record speech or type message."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QPointF
from PyQt6.QtGui import QColor, QPainter, QPen, QPainterPath
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGraphicsDropShadowEffect,
)

from gui import theme
from gui.widgets.glass_card import GlassCard
from gui.widgets.screen_header import ScreenHeader


# ---------------------------------------------------------------------------
# Painter-drawn icons
# ---------------------------------------------------------------------------

class _MicIcon(QWidget):
    """Thin-stroke microphone."""

    def __init__(self, size: int = 72, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(theme.TEXT_PRIMARY), 1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        w, h = self.width(), self.height()
        cx = w / 2

        cap_w, cap_h = w * 0.28, h * 0.42
        cap_x = cx - cap_w / 2
        cap_y = h * 0.06
        p.drawRoundedRect(int(cap_x), int(cap_y), int(cap_w), int(cap_h),
                          int(cap_w / 2), int(cap_w / 2))

        arch = QPainterPath()
        r = cap_w * 0.9
        arch.moveTo(cx - r, h * 0.54)
        arch.cubicTo(cx - r, h * 0.80, cx + r, h * 0.80, cx + r, h * 0.54)
        p.drawPath(arch)

        p.drawLine(int(cx), int(h * 0.78), int(cx), int(h * 0.92))
        p.drawLine(int(cx - r * 0.7), int(h * 0.92), int(cx + r * 0.7), int(h * 0.92))

        p.end()


class _PencilIcon(QWidget):
    """Thin-stroke pencil / edit."""

    def __init__(self, size: int = 72, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(theme.TEXT_PRIMARY), 1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        w, h = self.width(), self.height()

        path = QPainterPath()
        path.moveTo(w * 0.25, h * 0.82)
        path.lineTo(w * 0.72, h * 0.22)
        path.lineTo(w * 0.82, h * 0.32)
        path.lineTo(w * 0.35, h * 0.92)
        path.closeSubpath()
        p.drawPath(path)

        p.drawLine(int(w * 0.72), int(h * 0.22), int(w * 0.78), int(h * 0.16))
        p.drawLine(int(w * 0.18), int(h * 0.88), int(w * 0.42), int(h * 0.96))

        p.end()


# ---------------------------------------------------------------------------
# Choice tile
# ---------------------------------------------------------------------------

class _ChoiceTile(GlassCard):
    """Large clickable glass tile: icon above caption with hover shadow tween."""

    def __init__(self, icon: QWidget, caption: str, parent=None):
        super().__init__(parent, deep=True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(260, 260)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(theme.SPACE_MD)
        layout.setContentsMargins(
            theme.SPACE_LG, theme.SPACE_XL, theme.SPACE_LG, theme.SPACE_XL
        )

        layout.addStretch()
        layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel(caption)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            f"color: {theme.TEXT_SECONDARY}; "
            f"font-size: {theme.FONT_SIZE_BODY}px; "
            f"font-weight: {theme.WEIGHT_LIGHT}; "
            "background: transparent;"
        )
        layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(theme.HOVER_BLUR_REST)
        self._shadow.setOffset(0, 8)
        self._shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(self._shadow)

        self._blur_anim = QPropertyAnimation(self._shadow, b"blurRadius", self)
        self._blur_anim.setDuration(180)
        self._blur_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._offset_anim = QPropertyAnimation(self._shadow, b"offset", self)
        self._offset_anim.setDuration(180)
        self._offset_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _animate(self, blur: int, offset_y: int, alpha: int) -> None:
        self._blur_anim.stop()
        self._blur_anim.setStartValue(self._shadow.blurRadius())
        self._blur_anim.setEndValue(blur)
        self._blur_anim.start()

        self._offset_anim.stop()
        self._offset_anim.setStartValue(self._shadow.offset())
        self._offset_anim.setEndValue(QPointF(0, offset_y))
        self._offset_anim.start()

        self._shadow.setColor(QColor(0, 0, 0, alpha))

    def enterEvent(self, event) -> None:
        self._animate(theme.HOVER_BLUR_ACTIVE, 14, 32)

    def leaveEvent(self, event) -> None:
        self._animate(theme.HOVER_BLUR_REST, 8, 20)


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
        root.setContentsMargins(
            theme.SCREEN_PADDING_H, theme.SCREEN_PADDING_TOP,
            theme.SCREEN_PADDING_H, theme.SCREEN_PADDING_BOTTOM,
        )
        root.setSpacing(0)

        header = ScreenHeader()
        header.back.connect(self.back)
        root.addWidget(header)

        root.addStretch(2)

        title = QLabel("What would you like to do?")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; "
            f"font-size: {theme.FONT_SIZE_TITLE}px; "
            f"font-weight: {theme.WEIGHT_LIGHT}; "
            "background: transparent;"
        )
        root.addWidget(title)
        root.addSpacing(theme.SPACE_XL)

        tiles_row = QHBoxLayout()
        tiles_row.setSpacing(theme.SPACE_2XL)
        tiles_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._record_tile = _ChoiceTile(_MicIcon(72), "Record speech")
        self._type_tile   = _ChoiceTile(_PencilIcon(72), "Type message")

        self._record_tile.mousePressEvent = lambda _: self.record_clicked.emit()
        self._type_tile.mousePressEvent   = lambda _: self.type_clicked.emit()

        tiles_row.addWidget(self._record_tile)
        tiles_row.addWidget(self._type_tile)

        root.addLayout(tiles_row)
        root.addStretch(3)
