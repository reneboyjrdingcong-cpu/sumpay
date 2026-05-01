"""RoleScreen — Screen 2: doctor-or-patient choice after splash."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QPainter, QPen, QPainterPath, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QGraphicsDropShadowEffect,
)

from gui import theme
from gui.widgets.glass_card import GlassCard


# ---------------------------------------------------------------------------
# Icon painters
# ---------------------------------------------------------------------------

class _HandIcon(QWidget):
    """Thin-stroke open hand — represents patient / sign language."""

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

        # Palm arc
        path = QPainterPath()
        path.moveTo(cx - 20, h * 0.72)
        path.cubicTo(cx - 26, h * 0.90, cx + 26, h * 0.90, cx + 20, h * 0.72)
        p.drawPath(path)

        # Five fingers (simplified as upward curved strokes)
        finger_data = [
            (cx - 22, h * 0.72, cx - 28, h * 0.28),
            (cx - 10, h * 0.68, cx - 12, h * 0.18),
            (cx,      h * 0.66, cx,      h * 0.16),
            (cx + 10, h * 0.68, cx + 12, h * 0.18),
            (cx + 22, h * 0.72, cx + 26, h * 0.36),
        ]
        for bx, by, tx, ty in finger_data:
            fp = QPainterPath()
            fp.moveTo(bx, by)
            fp.cubicTo(bx, (by + ty) / 2, tx, (by + ty) / 2, tx, ty)
            p.drawPath(fp)

        p.end()


class _StethoIcon(QWidget):
    """Thin-stroke stethoscope — represents doctor."""

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

        # Earpieces — two small arcs at top
        for dx in (-14, 14):
            arc = QPainterPath()
            arc.moveTo(w / 2 + dx - 4, h * 0.15)
            arc.cubicTo(w / 2 + dx - 4, h * 0.08, w / 2 + dx + 4, h * 0.08, w / 2 + dx + 4, h * 0.15)
            p.drawPath(arc)

        # Tube from earpieces down
        left = QPainterPath()
        left.moveTo(w / 2 - 10, h * 0.15)
        left.cubicTo(w / 2 - 10, h * 0.42, w / 2, h * 0.42, w / 2, h * 0.50)
        p.drawPath(left)

        right = QPainterPath()
        right.moveTo(w / 2 + 10, h * 0.15)
        right.cubicTo(w / 2 + 10, h * 0.42, w / 2, h * 0.42, w / 2, h * 0.50)
        p.drawPath(right)

        # Tube looping down and right to chest piece
        tube = QPainterPath()
        tube.moveTo(w / 2, h * 0.50)
        tube.cubicTo(w / 2, h * 0.72, w * 0.72, h * 0.72, w * 0.72, h * 0.55)
        p.drawPath(tube)

        # Chest piece circle
        p.drawEllipse(int(w * 0.62), int(h * 0.50), 16, 16)

        p.end()


# ---------------------------------------------------------------------------
# Role card
# ---------------------------------------------------------------------------

class _RoleCard(GlassCard):
    """Clickable glass tile with an icon + label. Emits clicked(role)."""

    def __init__(self, role: str, icon: QWidget, label: str, parent=None):
        super().__init__(parent, deep=True)
        self._role = role
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(300, 240)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(32, 32, 32, 32)

        layout.addStretch()
        layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel(label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; "
            f"font-size: {theme.FONT_SIZE_BODY}px; "
            "font-weight: 400; "
            "background: transparent;"
        )
        layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        # hover shadow
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(40)
        self._shadow.setOffset(0, 8)
        self._shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(self._shadow)

    def enterEvent(self, event) -> None:
        self._shadow.setBlurRadius(60)
        self._shadow.setOffset(0, 14)
        self._shadow.setColor(QColor(0, 0, 0, 35))

    def leaveEvent(self, event) -> None:
        self._shadow.setBlurRadius(40)
        self._shadow.setOffset(0, 8)
        self._shadow.setColor(QColor(0, 0, 0, 20))

    def mousePressEvent(self, event) -> None:
        self.parentWidget().role_selected.emit(self._role)


# ---------------------------------------------------------------------------
# Screen
# ---------------------------------------------------------------------------

class RoleScreen(QWidget):
    role_selected = pyqtSignal(str)   # "patient" | "doctor"
    back          = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.setSpacing(0)
        root.setContentsMargins(60, 32, 60, 60)

        top_bar = QHBoxLayout()
        back_btn = QPushButton("‹ Back")
        back_btn.setFlat(True)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet(
            f"color: {theme.TEXT_HINT}; font-size: {theme.FONT_SIZE_HINT}px; "
            "font-weight: 300; background: transparent; border: none;"
        )
        back_btn.clicked.connect(self.back)
        top_bar.addWidget(back_btn)
        top_bar.addStretch()
        root.addLayout(top_bar)

        root.addStretch(2)

        title = QLabel("Who are you using this for?")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; "
            f"font-size: {theme.FONT_SIZE_HEADER}px; "
            "font-weight: 300; "
            "background: transparent;"
        )
        root.addWidget(title)

        hint = QLabel("Tap to choose")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(
            f"color: {theme.TEXT_HINT}; "
            f"font-size: {theme.FONT_SIZE_HINT}px; "
            "font-weight: 300; "
            "background: transparent; "
            "margin-top: 8px; margin-bottom: 48px;"
        )
        root.addWidget(hint)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(60)
        cards_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        patient_card = _RoleCard("patient", _HandIcon(64), "Patient")
        doctor_card  = _RoleCard("doctor",  _StethoIcon(64), "Doctor")

        cards_row.addWidget(patient_card)
        cards_row.addWidget(doctor_card)

        root.addLayout(cards_row)
        root.addStretch(3)
