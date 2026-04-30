"""Custom status bar with live diagnostic labels."""
from __future__ import annotations

from PyQt6.QtWidgets import QStatusBar, QLabel


class SumpayStatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._fps = self._make("FPS: --")
        self._confidence = self._make("Conf: --")
        self._tts = self._make("TTS: idle")
        self._mic = self._make("Mic: --")
        self._stt = self._make("STT: idle")
        for lbl in (self._fps, self._confidence, self._tts, self._mic, self._stt):
            self.addPermanentWidget(lbl)

    def _make(self, text: str) -> QLabel:
        lbl = QLabel(text)
        return lbl

    def set_fps(self, fps: float) -> None:
        self._fps.setText(f"FPS: {fps:.1f}")
        self._fps.setProperty("role", "ok" if fps >= 20 else "warn")
        self._fps.style().unpolish(self._fps)
        self._fps.style().polish(self._fps)

    def set_confidence(self, conf: float) -> None:
        self._confidence.setText(f"Conf: {conf * 100:.0f}%")

    def set_tts_busy(self, busy: bool) -> None:
        self._tts.setText("TTS: speaking" if busy else "TTS: idle")
        self._tts.setProperty("role", "warn" if busy else "ok")
        self._tts.style().unpolish(self._tts)
        self._tts.style().polish(self._tts)

    def set_mic_level(self, level: float) -> None:
        bars = int(level * 8)
        self._mic.setText("Mic: " + "█" * bars + "░" * (8 - bars))

    def set_stt_busy(self, busy: bool) -> None:
        self._stt.setText("STT: listening" if busy else "STT: idle")
        self._stt.setProperty("role", "warn" if busy else "ok")
        self._stt.style().unpolish(self._stt)
        self._stt.style().polish(self._stt)
