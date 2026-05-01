"""DoctorRecordScreen — Screen 7: live waveform while STT is capturing."""
from __future__ import annotations

import math

from PyQt6.QtCore import (
    Qt, pyqtSignal, pyqtSlot,
    QPropertyAnimation, QEasingCurve, QRectF, QTimer,
)
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
)

from gui import theme
from gui.widgets.glass_card import GlassCard
from gui.widgets.circle_button import CircleButton


# ---------------------------------------------------------------------------
# Animated waveform — always alive, reacts to mic_level when available
# ---------------------------------------------------------------------------

class _LiveWaveform(QWidget):
    """
    Bar waveform that self-animates via QTimer.
    - Idle: gentle sine sweep at low amplitude.
    - When set_level() is called with real mic data, bars react immediately.
    The timer drives repaints at ~30 fps regardless of mic input, so the
    widget always looks alive even if STT isn't delivering mic_level yet.
    """

    _N_BARS    = 22
    _BAR_W     = 5
    _BAR_GAP   = 5
    _MIN_H     = 6
    _MAX_H     = 60
    _IDLE_AMP  = 0.18   # idle sine amplitude (fraction of MAX_H)

    def __init__(self, parent=None):
        super().__init__(parent)
        total_w = self._N_BARS * (self._BAR_W + self._BAR_GAP) - self._BAR_GAP
        self.setFixedSize(total_w, 80)

        self._bars     = [self._MIN_H] * self._N_BARS
        self._phase    = 0.0           # idle animation phase (radians)
        self._has_mic  = False         # True once real mic data arrives
        self._mic_idle = 0             # frames since last mic_level call

        # Drive repaints at 33 ms ≈ 30 fps
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._tick)

    def start(self) -> None:
        self._phase = 0.0
        self._bars  = [self._MIN_H] * self._N_BARS
        self._has_mic = False
        self._mic_idle = 0
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def set_level(self, level: float) -> None:
        """Called by the Connector when a real mic_level signal arrives."""
        self._has_mic = True
        self._mic_idle = 0
        level = max(0.0, min(1.0, level))
        new_h = self._MIN_H + level * (self._MAX_H - self._MIN_H)
        self._bars = self._bars[1:] + [new_h]
        self.update()

    def _tick(self) -> None:
        self._phase += 0.18            # advance phase each frame

        self._mic_idle += 1
        if self._mic_idle > 6:         # ~200 ms with no real data → idle mode
            self._has_mic = False

        if not self._has_mic:
            # Synthesise a gentle sine wave across all bars
            new_bars = []
            for i in range(self._N_BARS):
                angle = self._phase + i * 0.45
                amp   = self._IDLE_AMP + 0.10 * math.sin(self._phase * 0.4)
                h     = self._MIN_H + amp * (self._MAX_H - self._MIN_H) * (
                    0.5 + 0.5 * math.sin(angle)
                )
                new_bars.append(h)
            self._bars = new_bars

        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cy = self.height() / 2
        x  = 0
        for bar_h in self._bars:
            alpha = int(70 + 185 * (bar_h / self._MAX_H))
            color = QColor(29, 29, 31, alpha)
            p.setBrush(color)
            p.setPen(Qt.PenStyle.NoPen)
            r    = min(self._BAR_W / 2, bar_h / 2)
            rect = QRectF(x, cy - bar_h / 2, self._BAR_W, bar_h)
            p.drawRoundedRect(rect, r, r)
            x += self._BAR_W + self._BAR_GAP
        p.end()


# ---------------------------------------------------------------------------
# Pulse dot
# ---------------------------------------------------------------------------

class _LiveDot(QWidget):
    """12×12 pulsing red dot — indicates active recording."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self._opacity = 1.0

        self._anim = QPropertyAnimation(self, b"opacity", self)
        self._anim.setDuration(800)
        self._anim.setStartValue(0.3)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.SineCurve)
        self._anim.setLoopCount(-1)

    def start(self) -> None:
        self._anim.start()

    def stop_anim(self) -> None:
        self._anim.stop()
        self._opacity = 0.0
        self.update()

    def get_opacity(self) -> float:
        return self._opacity

    def set_opacity(self, v: float) -> None:
        self._opacity = v
        self.update()

    opacity = property(get_opacity, set_opacity)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(220, 53, 69)
        color.setAlphaF(self._opacity)
        p.setBrush(color)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(self.rect())
        p.end()


# ---------------------------------------------------------------------------
# Waveform card
# ---------------------------------------------------------------------------

class _WaveformCard(GlassCard):
    def __init__(self, parent=None):
        super().__init__(parent, deep=False)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(40, 32, 40, 32)

        self._waveform = _LiveWaveform()
        layout.addWidget(self._waveform, alignment=Qt.AlignmentFlag.AlignCenter)

    def start(self) -> None:
        self._waveform.start()

    def stop(self) -> None:
        self._waveform.stop()

    def set_level(self, level: float) -> None:
        self._waveform.set_level(level)


# ---------------------------------------------------------------------------
# Screen
# ---------------------------------------------------------------------------

class DoctorRecordScreen(QWidget):
    recording_stopped = pyqtSignal(str)   # emits transcript text (may be empty)
    back              = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")

        self._transcript = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(40, 32, 40, 40)
        root.setSpacing(0)

        # ── Top bar: back ‹  |  dot + "Recording…" ─────────────────────── #
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        back_btn = QPushButton("‹ Back")
        back_btn.setFlat(True)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet(
            f"color: {theme.TEXT_HINT}; "
            f"font-size: {theme.FONT_SIZE_HINT}px; "
            "font-weight: 300; background: transparent; border: none;"
        )
        back_btn.clicked.connect(self._on_back)
        top_bar.addWidget(back_btn)

        top_bar.addStretch()

        self._dot = _LiveDot()
        top_bar.addWidget(self._dot, alignment=Qt.AlignmentFlag.AlignVCenter)

        rec_lbl = QLabel("Listening…  speak now")
        rec_lbl.setStyleSheet(
            f"color: {theme.TEXT_SECONDARY}; "
            f"font-size: {theme.FONT_SIZE_HINT}px; "
            "font-weight: 300; "
            "background: transparent;"
        )
        top_bar.addWidget(rec_lbl)

        root.addLayout(top_bar)
        root.addStretch(2)

        # ── Waveform card ───────────────────────────────────────────────── #
        self._wave_card = _WaveformCard()
        root.addWidget(self._wave_card, alignment=Qt.AlignmentFlag.AlignCenter)

        root.addSpacing(28)

        # ── Live partial caption ────────────────────────────────────────── #
        self._partial_lbl = QLabel("Waiting for speech…")
        self._partial_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._partial_lbl.setWordWrap(True)
        self._partial_lbl.setStyleSheet(
            f"color: {theme.TEXT_HINT}; "
            f"font-size: {theme.FONT_SIZE_HINT}px; "
            "font-style: italic; "
            "font-weight: 300; "
            "background: transparent;"
        )
        root.addWidget(self._partial_lbl)

        root.addStretch(2)

        # ── Stop button ─────────────────────────────────────────────────── #
        stop_btn = CircleButton("Stop")
        stop_btn.clicked.connect(self._on_stop)
        root.addWidget(stop_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        root.addStretch(1)

    # ------------------------------------------------------------------ #

    def reset(self) -> None:
        self._transcript = ""
        self._partial_lbl.setText("Waiting for speech…")
        self._dot.start()
        self._wave_card.start()

    def _cleanup(self) -> None:
        """Stop animations before leaving this screen."""
        self._dot.stop_anim()
        self._wave_card.stop()

    @pyqtSlot(float)
    def on_mic_level(self, level: float) -> None:
        self._wave_card.set_level(level)

    @pyqtSlot(str)
    def on_partial(self, text: str) -> None:
        if text:
            self._partial_lbl.setText(text)

    @pyqtSlot(str)
    def on_final(self, text: str) -> None:
        self._transcript = text
        self._partial_lbl.setText(text)

    def _on_stop(self) -> None:
        self._cleanup()
        text = self._transcript or self._partial_lbl.text()
        # Strip placeholder text if no real transcript arrived
        if text in ("Waiting for speech…", ""):
            text = ""
        self.recording_stopped.emit(text.strip())

    def _on_back(self) -> None:
        self._cleanup()
        self.back.emit()
