"""AudioScreen — Screen 4: TTS playback with speaker icon, replay, and done."""
from __future__ import annotations

import math

from PyQt6.QtCore import (
    Qt, pyqtSignal, pyqtSlot, QPropertyAnimation, QEasingCurve,
)
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget,
)

from gui import theme
from gui.widgets.glass_card import GlassCard
from gui.widgets.primary_button import PrimaryButton
from gui.widgets.screen_header import ScreenHeader


class _SpeakerIcon(QWidget):
    """Speaker cone + 2 concentric sound-wave arcs.

    `wave_opacity` is animated by AudioScreen to pulse while TTS is active.
    """

    def __init__(self, size: int = 160, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
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

        pen_w = max(2.5, w * 0.022)
        pen = QPen(QColor(29, 29, 31), pen_w)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        bx = w * 0.18
        by = h * 0.38
        bw = w * 0.20
        bh = h * 0.25
        p.drawRoundedRect(int(bx), int(by), int(bw), int(bh), 3, 3)

        cone = QPainterPath()
        cone.moveTo(bx + bw, by)
        cone.lineTo(w * 0.50, h * 0.20)
        cone.lineTo(w * 0.50, h * 0.80)
        cone.lineTo(bx + bw, by + bh)
        cone.closeSubpath()
        p.drawPath(cone)

        cx_w = w * 0.58
        cy_w = h * 0.50
        for radius, base_alpha in [(w * 0.16, 0.85), (w * 0.26, 0.45)]:
            c = QColor(29, 29, 31)
            c.setAlphaF(max(0.0, min(1.0, self._wave_opacity * base_alpha)))
            wp = QPen(c, pen_w)
            wp.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(wp)
            arc = QPainterPath()
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
    done             = pyqtSignal()   # Done → return to splash
    back             = pyqtSignal()   # ‹ Back → ConfirmScreen
    replay_requested = pyqtSignal()   # Replay button

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")

        self._tts_busy  = False
        self._finished  = False
        self._text      = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(
            theme.SCREEN_PADDING_H, theme.SCREEN_PADDING_TOP,
            theme.SCREEN_PADDING_H, theme.SCREEN_PADDING_BOTTOM,
        )
        root.setSpacing(0)

        # ── Header ───────────────────────────────────────────────────── #
        header = ScreenHeader()
        header.back.connect(self.back)
        root.addWidget(header)

        root.addStretch(1)

        # ── Speaker halo (glass card containing the speaker icon) ────── #
        halo = GlassCard(deep=False)
        halo.setFixedSize(280, 280)
        halo_layout = QVBoxLayout(halo)
        halo_layout.setContentsMargins(0, 0, 0, 0)
        halo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._speaker = _SpeakerIcon(size=160)
        halo_layout.addWidget(self._speaker, alignment=Qt.AlignmentFlag.AlignCenter)

        halo_row = QHBoxLayout()
        halo_row.setContentsMargins(0, 0, 0, 0)
        halo_row.addStretch()
        halo_row.addWidget(halo)
        halo_row.addStretch()
        root.addLayout(halo_row)

        root.addSpacing(theme.SPACE_MD)

        # ── Pulse dot ────────────────────────────────────────────────── #
        self._pulse = _PulseIndicator()
        root.addWidget(self._pulse, alignment=Qt.AlignmentFlag.AlignCenter)

        root.addSpacing(theme.SPACE_SM)

        # ── Hint label ───────────────────────────────────────────────── #
        self._hint_lbl = QLabel("Reading your message aloud…")
        self._hint_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hint_lbl.setStyleSheet(
            f"color: {theme.TEXT_HINT}; "
            f"font-size: {theme.FONT_SIZE_HINT}px; "
            f"font-weight: {theme.WEIGHT_LIGHT}; "
            "background: transparent;"
        )
        root.addWidget(self._hint_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        root.addSpacing(theme.SPACE_SM)

        # ── Transcript preview ───────────────────────────────────────── #
        self._transcript_lbl = QLabel("")
        self._transcript_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._transcript_lbl.setWordWrap(True)
        self._transcript_lbl.setMaximumWidth(600)
        self._transcript_lbl.setStyleSheet(
            f"color: {theme.TEXT_SECONDARY}; "
            f"font-size: {theme.FONT_SIZE_BODY}px; "
            f"font-weight: {theme.WEIGHT_LIGHT}; "
            "font-style: italic; "
            "background: transparent;"
        )
        transcript_row = QHBoxLayout()
        transcript_row.setContentsMargins(0, 0, 0, 0)
        transcript_row.addStretch()
        transcript_row.addWidget(self._transcript_lbl)
        transcript_row.addStretch()
        root.addLayout(transcript_row)

        root.addSpacing(theme.SPACE_XL)

        # ── Action row: Replay (left) + Done (right) ─────────────────── #
        action_pair = QWidget()
        action_pair.setFixedWidth(360)
        pair_layout = QHBoxLayout(action_pair)
        pair_layout.setContentsMargins(0, 0, 0, 0)
        pair_layout.setSpacing(0)

        self._replay_btn = PrimaryButton("Replay", variant="retry")
        self._replay_btn.clicked.connect(self.replay_requested)
        self._replay_btn.setEnabled(False)
        pair_layout.addWidget(self._replay_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        pair_layout.addStretch()

        self._done_btn = PrimaryButton("Done", variant="confirm")
        self._done_btn.clicked.connect(self.done)
        pair_layout.addWidget(self._done_btn, alignment=Qt.AlignmentFlag.AlignRight)

        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.addStretch()
        action_row.addWidget(action_pair)
        action_row.addStretch()

        root.addLayout(action_row)
        root.addStretch(1)

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

    def set_text(self, text: str) -> None:
        """Set the transcript preview shown below the hint."""
        self._text = text or ""
        if self._text:
            self._transcript_lbl.setText(f'"{self._text}"')
        else:
            self._transcript_lbl.setText("")

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
