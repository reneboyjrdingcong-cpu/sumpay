"""CameraScreen — Screen 3: live ASL preview + accumulating translation card."""
from __future__ import annotations

import math

from PyQt6.QtCore import Qt, QRectF, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QBitmap, QColor, QPainter, QPainterPath, QRegion
from PyQt6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QStackedLayout, QVBoxLayout, QWidget,
)

from gui import theme
from gui.video_widget import VideoWidget
from gui.widgets.screen_header import ScreenHeader


# ── Pulsing status dot ─────────────────────────────────────────────────── #

class _SyncDot(QWidget):
    """10×10 dot; when pulsing, scale (0.94↔1.04) and opacity (0.40↔1.00)
    stay in phase via a single sine wave (1 400 ms loop)."""

    _DURATION = 1400
    _TICK = 16

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(10, 10)
        self._elapsed = 0
        self._color = QColor(theme.TEXT_HINT)
        self._pulsing = False
        self._opacity = 1.0
        self._scale = 1.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def set_state(self, color: str, pulsing: bool) -> None:
        self._color = QColor(color)
        self._pulsing = pulsing
        if pulsing:
            if not self._timer.isActive():
                self._elapsed = 0
                self._timer.start(self._TICK)
        else:
            self._timer.stop()
            self._opacity = 1.0
            self._scale = 1.0
        self.update()

    def _tick(self) -> None:
        self._elapsed = (self._elapsed + self._TICK) % self._DURATION
        s = math.sin(self._elapsed / self._DURATION * math.pi)
        self._opacity = 0.40 + 0.60 * s
        self._scale = 0.94 + 0.10 * s
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.translate(5.0, 5.0)
        p.scale(self._scale, self._scale)
        c = QColor(self._color)
        c.setAlphaF(self._opacity)
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(-5, -5, 10, 10)
        p.end()


# ── Blinking text caret ────────────────────────────────────────────────── #

class _Caret(QWidget):
    """2×28 px vertical bar, ACCENT_PRIMARY; blinks at 1.1 s / 50 % duty."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(2, 28)
        self._on = True
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._blink)
        self._timer.start(550)

    def _blink(self) -> None:
        self._on = not self._on
        self.update()

    def paintEvent(self, event) -> None:
        if not self._on:
            return
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(theme.ACCENT_PRIMARY))
        p.end()

    def stop(self) -> None:
        self._timer.stop()
        self._on = False
        self.update()

    def start(self) -> None:
        self._on = True
        self._timer.start(550)


# ── Camera screen ──────────────────────────────────────────────────────── #

# ── Camera frame with rounded-rect child clipping ─────────────────────── #

class _RoundedCamFrame(QFrame):
    """QFrame that masks itself (and all children) to a rounded rect on resize.
    Qt does not auto-clip child widgets to a parent's border-radius, so a
    QRegion mask is the reliable cross-platform fix."""

    _RADIUS = 24

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), self._RADIUS, self._RADIUS)
        bmp = QBitmap(self.size())
        bmp.fill(Qt.GlobalColor.color0)
        p = QPainter(bmp)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillPath(path, Qt.GlobalColor.color1)
        p.end()
        self.setMask(QRegion(bmp))


# ── Shared pill / button styles ────────────────────────────────────────── #

_PILL_BG   = "rgba(255, 255, 255, 245)"
_PILL_BORD = "rgba(255, 255, 255, 76)"

_CONTINUE_QSS = f"""
QPushButton {{
    background-color: {theme.ACCENT_PRIMARY};
    border: none;
    border-radius: 32px;
    min-height: 64px;
    padding-left: 28px;
    padding-right: 28px;
    color: #FFFFFF;
    font-size: 18px;
    font-weight: 600;
}}
QPushButton:hover   {{ background-color: {theme.ACCENT_PRIMARY_HOVER}; }}
QPushButton:pressed {{ background-color: {theme.ACCENT_PRIMARY_PRESSED}; }}
QPushButton:disabled {{
    background-color: rgba(31, 138, 126, 115);
    color: rgba(255, 255, 255, 153);
}}
"""


def _soft_shadow(parent: QWidget) -> QGraphicsDropShadowEffect:
    fx = QGraphicsDropShadowEffect(parent)
    fx.setBlurRadius(24)
    fx.setOffset(0, 8)
    fx.setColor(QColor(20, 20, 20, 15))
    return fx


class CameraScreen(QWidget):
    continue_clicked = pyqtSignal()
    back             = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")
        self._phrases: list[str] = []
        self._confidence: float = 0.0

        root = QVBoxLayout(self)
        root.setContentsMargins(
            theme.SCREEN_PADDING_H, theme.SCREEN_PADDING_TOP,
            theme.SCREEN_PADDING_H, theme.SCREEN_PADDING_BOTTOM,
        )
        root.setSpacing(0)

        # ── Zone A — Header (matches all other patient screens) ───────── #
        header = ScreenHeader(title="Sign your message")
        header.back.connect(self.back)
        root.addWidget(header)
        root.addSpacing(theme.SPACE_MD)

        # ── Zone B — Body ─────────────────────────────────────────────── #
        body_col = root
        body_col.setSpacing(0)

        # ── Camera surface ────────────────────────────────────────────── #
        cam_frame = _RoundedCamFrame()
        cam_frame.setObjectName("camFrame")
        cam_frame.setStyleSheet(
            "QFrame#camFrame {"
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            "      stop:0 #2A2A2E, stop:1 #1A1A1C);"
            f" border: 1px solid {theme.BORDER_HAIRLINE};"
            "  border-radius: 24px;"
            "}"
        )
        cam_frame.setGraphicsEffect(_soft_shadow(cam_frame))

        cam_stack = QStackedLayout(cam_frame)
        cam_stack.setStackingMode(QStackedLayout.StackingMode.StackAll)
        cam_stack.setContentsMargins(0, 0, 0, 0)

        # Layer 0 — live video
        self._video = VideoWidget()
        cam_stack.addWidget(self._video)

        # Layer 1 — status pill (top-left)
        pill_layer = QWidget()
        pill_layer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        pill_layer.setStyleSheet("background: transparent;")
        pl = QVBoxLayout(pill_layer)
        pl.setContentsMargins(16, 16, 16, 16)
        pl.setSpacing(0)

        self._status_pill = QWidget()
        self._status_pill.setObjectName("statusPill")
        self._status_pill.setStyleSheet(
            f"QWidget#statusPill {{ background-color: {_PILL_BG}; "
            f"border: 1px solid {_PILL_BORD}; border-radius: 999px; }}"
        )
        pill_fx = QGraphicsDropShadowEffect(self._status_pill)
        pill_fx.setBlurRadius(8)
        pill_fx.setOffset(0, 2)
        pill_fx.setColor(QColor(0, 0, 0, 51))
        self._status_pill.setGraphicsEffect(pill_fx)

        pill_inner = QHBoxLayout(self._status_pill)
        pill_inner.setContentsMargins(12, 8, 14, 8)
        pill_inner.setSpacing(10)

        self._status_dot = _SyncDot()
        pill_inner.addWidget(self._status_dot, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._status_lbl = QLabel("Show your hands")
        self._status_lbl.setStyleSheet(
            "color: #1D1D1F; font-size: 14px; font-weight: 500; background: transparent;"
        )
        pill_inner.addWidget(self._status_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)

        pill_top_row = QHBoxLayout()
        pill_top_row.setContentsMargins(0, 0, 0, 0)
        pill_top_row.addWidget(self._status_pill)
        pill_top_row.addStretch()
        pl.addLayout(pill_top_row)
        pl.addStretch()
        cam_stack.addWidget(pill_layer)

        # Layer 2 — tip chip (bottom-right)
        tip_layer = QWidget()
        tip_layer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        tip_layer.setStyleSheet("background: transparent;")
        tl = QVBoxLayout(tip_layer)
        tl.setContentsMargins(16, 16, 16, 16)
        tl.setSpacing(0)
        tl.addStretch()

        tip_chip = QWidget()
        tip_chip.setObjectName("tipChip")
        tip_chip.setStyleSheet(
            f"QWidget#tipChip {{ background-color: {_PILL_BG}; "
            f"border: 1px solid {_PILL_BORD}; border-radius: 12px; }}"
        )
        tip_inner = QHBoxLayout(tip_chip)
        tip_inner.setContentsMargins(14, 8, 14, 8)
        tip_lbl = QLabel("Frame your hands and face")
        tip_lbl.setStyleSheet(
            f"color: {theme.TEXT_SECONDARY}; font-size: 13px; "
            "font-weight: 500; background: transparent;"
        )
        tip_inner.addWidget(tip_lbl)

        tip_bot_row = QHBoxLayout()
        tip_bot_row.setContentsMargins(0, 0, 0, 0)
        tip_bot_row.addStretch()
        tip_bot_row.addWidget(tip_chip)
        tl.addLayout(tip_bot_row)
        cam_stack.addWidget(tip_layer)

        root.addWidget(cam_frame, stretch=80)
        root.addSpacing(theme.SPACE_MD)

        # ── Translation card ──────────────────────────────────────────── #
        trans_card = QFrame()
        trans_card.setObjectName("transCard")
        trans_card.setStyleSheet(
            f"QFrame#transCard {{ background-color: {theme.BG_GLASS_DEEP}; "
            f"border: 1px solid {theme.BORDER_HAIRLINE}; border-radius: 24px; }}"
        )
        trans_card.setGraphicsEffect(_soft_shadow(trans_card))
        trans_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        tc = QVBoxLayout(trans_card)
        tc.setContentsMargins(20, 20, 20, 20)
        tc.setSpacing(0)

        # Meta row
        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)

        meta_left = QLabel("DETECTED TEXT")
        meta_left.setStyleSheet(
            f"color: {theme.TEXT_HINT}; font-size: 12px; font-weight: 600; "
            "letter-spacing: 1.5px; background: transparent;"
        )
        meta_row.addWidget(meta_left)
        meta_row.addStretch()

        self._meta_right = QLabel("")
        self._meta_right.setStyleSheet(
            f"color: {theme.TEXT_HINT}; font-size: 13px; "
            "font-weight: 400; background: transparent;"
        )
        meta_row.addWidget(self._meta_right)
        tc.addLayout(meta_row)
        tc.addSpacing(12)

        # Text body + caret
        text_row = QHBoxLayout()
        text_row.setContentsMargins(0, 0, 0, 0)
        text_row.setSpacing(6)

        self._translation_label = QLabel("Waiting for signs…")
        self._translation_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._translation_label.setWordWrap(True)
        self._translation_label.setStyleSheet(
            f"color: {theme.TEXT_HINT}; font-size: 26px; font-weight: 400; "
            "font-style: italic; letter-spacing: -0.26px; background: transparent;"
        )
        text_row.addWidget(self._translation_label, stretch=1)

        self._caret = _Caret()
        text_row.addWidget(self._caret, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        text_row.addStretch()
        tc.addLayout(text_row, stretch=1)
        tc.addSpacing(16)

        # Footer row
        footer_row = QHBoxLayout()
        footer_row.setContentsMargins(0, 0, 0, 0)
        footer_row.setSpacing(16)
        footer_row.addStretch()

        footer_hint = QLabel("Pause signing when you're done")
        footer_hint.setStyleSheet(
            f"color: {theme.TEXT_HINT}; font-size: 13px; "
            "font-weight: 400; background: transparent;"
        )
        footer_row.addWidget(footer_hint, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._continue_btn = QPushButton("Continue")
        self._continue_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._continue_btn.setEnabled(False)
        self._continue_btn.setStyleSheet(_CONTINUE_QSS)
        self._continue_btn.clicked.connect(self.continue_clicked)
        footer_row.addWidget(self._continue_btn)

        tc.addLayout(footer_row)

        root.addWidget(trans_card, stretch=22)

    # ── State helpers ──────────────────────────────────────────────────── #

    def _set_idle(self) -> None:
        self._status_dot.set_state(theme.TEXT_HINT, False)
        self._status_lbl.setText("Show your hands")

    def _set_detecting(self) -> None:
        self._status_dot.set_state(theme.ACCENT_PRIMARY, True)
        self._status_lbl.setText("Signing — keep going")

    def _set_low_confidence(self) -> None:
        self._status_dot.set_state(theme.ACCENT_EDIT, False)
        self._status_lbl.setText("Sign more slowly")

    def _refresh_translation(self) -> None:
        if not self._phrases:
            self._translation_label.setText("Waiting for signs…")
            self._translation_label.setStyleSheet(
                f"color: {theme.TEXT_HINT}; font-size: 26px; font-weight: 400; "
                "font-style: italic; letter-spacing: -0.26px; background: transparent;"
            )
            self._meta_right.setText("")
            self._continue_btn.setEnabled(False)
        else:
            self._translation_label.setText(" ".join(self._phrases))
            self._translation_label.setStyleSheet(
                f"color: {theme.TEXT_PRIMARY}; font-size: 26px; font-weight: 400; "
                "letter-spacing: -0.26px; background: transparent;"
            )
            n = len(self._phrases)
            pct = int(self._confidence * 100)
            self._meta_right.setText(
                f"{n} phrase{'s' if n != 1 else ''} · {pct}% confidence"
            )
            self._continue_btn.setEnabled(True)

    # ── Public API ─────────────────────────────────────────────────────── #

    @pyqtSlot(object)
    def update_frame(self, frame) -> None:
        self._video.update_frame(frame)

    @pyqtSlot(str)
    def append_phrase(self, text: str) -> None:
        self._phrases.append(text)
        self._refresh_translation()
        self._set_detecting()

    @pyqtSlot(str, float)
    def on_recognized(self, label: str, confidence: float) -> None:
        """Called directly from the recognizer signal with label + confidence."""
        self._confidence = confidence
        self.append_phrase(label)

    def set_status_low_confidence(self) -> None:
        self._set_low_confidence()

    def set_status_idle(self) -> None:
        self._set_idle()

    def clear_phrases(self) -> None:
        self._phrases.clear()
        self._confidence = 0.0
        self._refresh_translation()
        self._set_idle()

    def current_text(self) -> str:
        return " ".join(self._phrases)

    # ── Lifecycle ──────────────────────────────────────────────────────── #

    def hideEvent(self, event) -> None:
        self._caret.stop()
        self._status_dot.set_state(theme.TEXT_HINT, False)
        super().hideEvent(event)

    def showEvent(self, event) -> None:
        self._caret.start()
        super().showEvent(event)
