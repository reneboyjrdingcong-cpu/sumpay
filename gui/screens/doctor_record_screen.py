"""DoctorRecordScreen — Screen 7: live waveform while STT is capturing."""
from __future__ import annotations

import math

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QRectF, QTimer
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
)

from gui import theme
from gui.widgets.glass_card import GlassCard
from gui.widgets.primary_button import PrimaryButton
from gui.widgets.screen_header import ScreenHeader
from gui.widgets.status_pill import StatusPill


# ---------------------------------------------------------------------------
# Animated waveform — always alive, reacts to mic_level when available
# ---------------------------------------------------------------------------

class _LiveWaveform(QWidget):
    """
    Bar waveform that self-animates via QTimer.
    - Idle: gentle sine sweep at low amplitude.
    - When set_level() is called with real mic data, bars react immediately.
    """

    _N_BARS    = 22
    _BAR_W     = 5
    _BAR_GAP   = 5
    _MIN_H     = 6
    _MAX_H     = 60
    _IDLE_AMP  = 0.18

    def __init__(self, parent=None):
        super().__init__(parent)
        total_w = self._N_BARS * (self._BAR_W + self._BAR_GAP) - self._BAR_GAP
        self.setFixedSize(total_w, 80)

        self._bars     = [self._MIN_H] * self._N_BARS
        self._phase    = 0.0
        self._has_mic  = False
        self._mic_idle = 0

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
        self._has_mic = True
        self._mic_idle = 0
        level = max(0.0, min(1.0, level))
        new_h = self._MIN_H + level * (self._MAX_H - self._MIN_H)
        self._bars = self._bars[1:] + [new_h]
        self.update()

    def _tick(self) -> None:
        self._phase += 0.18

        self._mic_idle += 1
        if self._mic_idle > 6:
            self._has_mic = False

        if not self._has_mic:
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
        base = QColor(theme.WAVE_BAR)
        for bar_h in self._bars:
            alpha = int(70 + 185 * (bar_h / self._MAX_H))
            color = QColor(base.red(), base.green(), base.blue(), alpha)
            p.setBrush(color)
            p.setPen(Qt.PenStyle.NoPen)
            r    = min(self._BAR_W / 2, bar_h / 2)
            rect = QRectF(x, cy - bar_h / 2, self._BAR_W, bar_h)
            p.drawRoundedRect(rect, r, r)
            x += self._BAR_W + self._BAR_GAP
        p.end()


# ---------------------------------------------------------------------------
# Waveform card
# ---------------------------------------------------------------------------

class _WaveformCard(GlassCard):
    def __init__(self, parent=None):
        super().__init__(parent, deep=False)
        self.setMaximumWidth(720)
        self.setFixedHeight(200)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(
            theme.SPACE_LG, theme.SPACE_LG, theme.SPACE_LG, theme.SPACE_LG
        )

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
    recording_stopped = pyqtSignal(str)
    back              = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")

        self._transcript = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(
            theme.SCREEN_PADDING_H, theme.SCREEN_PADDING_TOP,
            theme.SCREEN_PADDING_H, theme.SCREEN_PADDING_BOTTOM,
        )
        root.setSpacing(0)

        header = ScreenHeader()
        header.back.connect(self._on_back)
        root.addWidget(header)

        root.addStretch(2)

        # Waveform card
        self._wave_card = _WaveformCard()
        wave_row = QHBoxLayout()
        wave_row.setContentsMargins(0, 0, 0, 0)
        wave_row.addStretch()
        wave_row.addWidget(self._wave_card)
        wave_row.addStretch()
        root.addLayout(wave_row)

        root.addSpacing(theme.SPACE_MD)

        # Status pill — "Listening… speak now"
        self._status_pill = StatusPill("Listening…  speak now")
        pill_row = QHBoxLayout()
        pill_row.setContentsMargins(0, 0, 0, 0)
        pill_row.addStretch()
        pill_row.addWidget(self._status_pill)
        pill_row.addStretch()
        root.addLayout(pill_row)

        root.addSpacing(theme.SPACE_SM)

        # Live partial caption
        self._partial_lbl = QLabel("Waiting for speech…")
        self._partial_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._partial_lbl.setWordWrap(True)
        self._partial_lbl.setMaximumWidth(600)
        self._partial_lbl.setStyleSheet(
            f"color: {theme.TEXT_HINT}; "
            f"font-size: {theme.FONT_SIZE_HINT}px; "
            "font-style: italic; "
            f"font-weight: {theme.WEIGHT_LIGHT}; "
            "background: transparent;"
        )
        partial_row = QHBoxLayout()
        partial_row.setContentsMargins(0, 0, 0, 0)
        partial_row.addStretch()
        partial_row.addWidget(self._partial_lbl)
        partial_row.addStretch()
        root.addLayout(partial_row)

        root.addStretch(2)

        # Stop button — destructive (ends live session) → red traffic-light
        stop_btn = PrimaryButton("Stop", variant="retry")
        stop_btn.clicked.connect(self._on_stop)
        root.addWidget(stop_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        root.addStretch(1)

    # ------------------------------------------------------------------ #

    def reset(self) -> None:
        self._transcript = ""
        self._partial_lbl.setText("Waiting for speech…")
        self._status_pill.start()
        self._wave_card.start()

    def _cleanup(self) -> None:
        self._status_pill.stop()
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
        if text in ("Waiting for speech…", ""):
            text = ""
        self.recording_stopped.emit(text.strip())

    def _on_back(self) -> None:
        self._cleanup()
        self.back.emit()
