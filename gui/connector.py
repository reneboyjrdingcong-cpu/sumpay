"""Connector — QStackedWidget state machine for the 4-screen Phase 1 flow.

Screen indices:
    0 — SplashScreen
    1 — CameraScreen
    2 — ConfirmScreen
    3 — AudioScreen
"""
from __future__ import annotations

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QStackedWidget

from gui.screens.splash_screen import SplashScreen
from gui.screens.camera_screen import CameraScreen
from gui.screens.confirm_screen import ConfirmScreen
from gui.screens.audio_screen import AudioScreen


_SPLASH  = 0
_CAMERA  = 1
_CONFIRM = 2
_AUDIO   = 3


class Connector(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._accumulated: list[str] = []
        self._tts_worker = None

        self._splash  = SplashScreen()
        self._camera  = CameraScreen()
        self._confirm = ConfirmScreen()
        self._audio   = AudioScreen()

        self.addWidget(self._splash)   # index 0
        self.addWidget(self._camera)   # index 1
        self.addWidget(self._confirm)  # index 2
        self.addWidget(self._audio)    # index 3

        # ── Internal signal wiring ─────────────────────────────────── #
        self._splash.advance.connect(self._go_camera)
        self._camera.continue_clicked.connect(self._go_confirm)
        self._confirm.confirmed.connect(self._go_audio)
        self._confirm.retry.connect(self._go_camera_retry)
        self._audio.done.connect(self._go_splash)

        self.setCurrentIndex(_SPLASH)

    # ------------------------------------------------------------------ #
    # Public API (called by main.py)
    # ------------------------------------------------------------------ #

    def set_tts_worker(self, tts_worker) -> None:
        self._tts_worker = tts_worker
        if tts_worker is not None:
            tts_worker.busy_changed.connect(self._audio.on_busy)

    @pyqtSlot(object)
    def on_frame(self, frame) -> None:
        self._camera.update_frame(frame)

    @pyqtSlot(str, float)
    def on_recognized(self, sentence: str, confidence: float) -> None:
        self._accumulated.append(sentence)
        self._camera.append_phrase(sentence)

    @pyqtSlot(bool)
    def on_tts_busy(self, busy: bool) -> None:
        self._audio.on_busy(busy)

    # ------------------------------------------------------------------ #
    # Transitions
    # ------------------------------------------------------------------ #

    def _go_camera(self) -> None:
        self._accumulated.clear()
        self._camera.clear_phrases()
        self.setCurrentIndex(_CAMERA)

    def _go_confirm(self) -> None:
        text = self._camera.current_text()
        self._confirm.set_text(text)
        self.setCurrentIndex(_CONFIRM)

    @pyqtSlot(str)
    def _go_audio(self, text: str) -> None:
        self._audio.reset()
        self.setCurrentIndex(_AUDIO)
        if self._tts_worker and text:
            self._tts_worker.speak(text)
        else:
            # No TTS available — mark finished immediately so click works
            self._audio.on_busy(False)

    def _go_camera_retry(self) -> None:
        self._accumulated.clear()
        self._camera.clear_phrases()
        self.setCurrentIndex(_CAMERA)

    def _go_splash(self) -> None:
        self._accumulated.clear()
        self._camera.clear_phrases()
        self.setCurrentIndex(_SPLASH)
