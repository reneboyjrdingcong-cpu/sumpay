"""AudioScreen — Screen 4: TTS playback with speaker icon, replay, and done."""
from __future__ import annotations

import math

from PyQt6.QtCore import (
    Qt, pyqtSignal, pyqtSlot, QPropertyAnimation, QEasingCurve, QRectF,
)
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
)

from gui import theme
from gui.widgets.circle_button import CircleButton


class _SpeakerIcon(QWidget):
    """Speaker cone + 2 concentric sound-wave arcs. 120×120 px.

    wave_opacity is animated by AudioScreen to pulse while TTS is active.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 120)
        self._wave_opacity = 1.0

    def set_wave_opacity(self, v: float) -> None:
        self._wave_opacity = v
        self.update()

    def get_wave_opacity(self) -> float:
        return self._wave_opacity

    wave_opacity = property(get_wave_opacity, set_wave_opacity)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        pen = QPen(QColor(29, 29, 31), 2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        # Speaker body rectangle (left-centre)
        bx = w * 0.18
        by = h * 0.38
        bw = w * 0.20
        bh = h * 0.25
        p.drawRoundedRect(int(bx), int(by), int(bw), int(bh), 3, 3)

        # Cone (trapezoid: narrow at body right edge, wide at 50% width)
        cone = QPainterPath()
        cone.moveTo(bx + bw, by)
        cone.lineTo(w * 0.50, h * 0.20)
        cone.lineTo(w * 0.50, h * 0.80)
        cone.lineTo(bx + bw, by + bh)
        cone.closeSubpath()
        p.drawPath(cone)

        # Sound waves (2 arcs emanating to the right)
        cx_w = w * 0.58
        cy_w = h * 0.50
        for radius, base_alpha in [(w * 0.16, 0.85), (w * 0.26, 0.45)]:
            c = QColor(29, 29, 31)
            c.setAlphaF(max(0.0, min(1.0, self._wave_opacity * base_alpha)))
            wp = QPen(c, 2.5)
            wp.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(wp)
            arc = QPainterPath()
            # Arc from ~150° to ~-150° (pointing right)
            arc.moveTo(cx_w + radius * math.cos(math.radians(150)),
                       cy_w + radius * math.sin(math.radians(150)))
            arc.quadTo(cx_w + radius * 1.05, cy_w,
                       cx_w + radius * math.cos(math.radians(-150)),
                       cy_w + radius * math.sin(math.radians(-150)))
            p.drawPath(arc)

        p.end()


class _PulseIndicator(QWidget):
    """28×28 circle that pulses opacity while TTS is busy."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(28, 28)
        self._opacity = 1.0

    def set_opacity(self, v: float) -> None:
        self._opacity = v
        self.update()

    def get_opacity(self) -> float:
        return self._opacity

    opacity = property(get_opacity, set_opacity)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(29, 29, 31)
        color.setAlphaF(self._opacity * 0.8)
        p.setBrush(color)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(self.rect())
        p.end()


class AudioScreen(QWidget):
    done             = pyqtSignal()   # "Done →" button → return to splash
    back             = pyqtSignal()   # "‹ Back" → return to ConfirmScreen
    replay_requested = pyqtSignal()   # Replay button

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")

        self._tts_busy  = False
        self._finished  = False

        root = QVBoxLayout(self)
        root.setContentsMargins(60, 32, 60, 60)
        root.setSpacing(0)

        # ── Back button ─────────────────────────────────────────────── #
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

        # ── Speaker icon ─────────────────────────────────────────────── #
        self._speaker = _SpeakerIcon()
        root.addWidget(self._speaker, alignment=Qt.AlignmentFlag.AlignCenter)
        root.addSpacing(20)

        # ── Pulse dot ────────────────────────────────────────────────── #
        self._pulse = _PulseIndicator()
        root.addWidget(self._pulse, alignment=Qt.AlignmentFlag.AlignCenter)
        root.addSpacing(12)

        # ── Hint label ───────────────────────────────────────────────── #
        self._hint_lbl = QLabel("Reading your message aloud…")
        self._hint_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hint_lbl.setStyleSheet(
            f"color: {theme.TEXT_HINT}; font-size: {theme.FONT_SIZE_HINT}px; "
            "font-weight: 300; background: transparent;"
        )
        root.addWidget(self._hint_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        root.addSpacing(40)

        # ── Action row: Replay + Done ────────────────────────────────── #
        action_row = QHBoxLayout()
        action_row.setSpacing(40)
        action_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._replay_btn = CircleButton("Replay")
        self._replay_btn.clicked.connect(self.replay_requested)
        self._replay_btn.setEnabled(False)
        action_row.addWidget(self._replay_btn)

        done_btn = QPushButton("Done →")
        done_btn.setObjectName("continueBtn")
        done_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        done_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        done_btn.clicked.connect(self.done)
        action_row.addWidget(done_btn)

        root.addLayout(action_row)
        root.addStretch(3)

        # ── Animations ───────────────────────────────────────────────── #
        self._anim = QPropertyAnimation(self._pulse, b"opacity", self)
        self._anim.setDuration(900)
        self._anim.setStartValue(0.25)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.SineCurve)
        self._anim.setLoopCount(-1)

        self._wave_anim = QPropertyAnimation(self._speaker, b"wave_opacity", self)
        self._wave_anim.setDuration(900)
        self._wave_anim.setStartValue(0.25)
        self._wave_anim.setEndValue(1.0)
        self._wave_anim.setEasingCurve(QEasingCurve.Type.SineCurve)
        self._wave_anim.setLoopCount(-1)

    # ------------------------------------------------------------------ #

    @pyqtSlot(bool)
    def on_busy(self, busy: bool) -> None:
        self._tts_busy = busy
        if busy:
            self._finished = False
            self._anim.start()
            self._wave_anim.start()
            self._hint_lbl.setText("Reading your message aloud…")
            self._replay_btn.setEnabled(False)
        else:
            self._anim.stop()
            self._wave_anim.stop()
            self._pulse.set_opacity(0.3)
            self._speaker.set_wave_opacity(0.3)
            self._finished = True
            self._hint_lbl.setText("Message delivered")
            self._replay_btn.setEnabled(True)

    def reset(self) -> None:
        self._finished = False
        self._tts_busy = False
        self._anim.stop()
        self._wave_anim.stop()
        self._pulse.set_opacity(1.0)
        self._speaker.set_wave_opacity(1.0)
        self._hint_lbl.setText("Reading your message aloud…")
        self._replay_btn.setEnabled(False)
