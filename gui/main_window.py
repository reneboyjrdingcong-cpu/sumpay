"""MainWindow — full-screen kiosk Connector (patient + doctor flows)."""
from __future__ import annotations

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout

import config
from gui.connector import Connector
from gui.status_bar import SumpayStatusBar
from gui import theme


def _load_stylesheet() -> str:
    qss = config.STYLES_QSS.read_text(encoding="utf-8")
    subs = {
        "@BG_PRIMARY@":    theme.BG_PRIMARY,
        "@BG_GLASS@":      theme.BG_GLASS,
        "@BG_GLASS_DEEP@": theme.BG_GLASS_DEEP,
        "@TEXT_PRIMARY@":  theme.TEXT_PRIMARY,
        "@TEXT_SECONDARY@": theme.TEXT_SECONDARY,
        "@FONT_FAMILY@":   theme.FONT_FAMILY,
        "@FONT_SIZE_BODY@": str(theme.FONT_SIZE_BODY),
        "@FONT_SIZE_HINT@": str(theme.FONT_SIZE_HINT),
    }
    for token, value in subs.items():
        qss = qss.replace(token, value)
    return qss


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(theme.WINDOW_TITLE)
        self.setMinimumSize(theme.WINDOW_MIN_WIDTH, theme.WINDOW_MIN_HEIGHT)
        self.setStyleSheet(_load_stylesheet())

        self._status_bar = SumpayStatusBar(self)
        self.setStatusBar(self._status_bar)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._connector = Connector()
        layout.addWidget(self._connector)

    # ------------------------------------------------------------------ #
    # Public API called by main.py
    # ------------------------------------------------------------------ #

    def set_tts_worker(self, tts_worker) -> None:
        self._connector.set_tts_worker(tts_worker)

    def set_router(self, router) -> None:
        self._connector.set_router(router)

    # ------------------------------------------------------------------ #
    # Slots wired by main.py
    # ------------------------------------------------------------------ #

    @pyqtSlot(object)
    def on_frame(self, frame) -> None:
        self._connector.on_frame(frame)

    @pyqtSlot(float)
    def on_fps(self, fps: float) -> None:
        self._status_bar.set_fps(fps)

    @pyqtSlot(str, float)
    def on_recognized(self, sentence: str, confidence: float) -> None:
        self._connector.on_recognized(sentence, confidence)
        self._status_bar.set_confidence(confidence)

    @pyqtSlot(bool)
    def on_tts_busy(self, busy: bool) -> None:
        self._status_bar.set_tts_busy(busy)

    @pyqtSlot(float)
    def on_mic_level(self, level: float) -> None:
        self._connector.on_mic_level(level)
        self._status_bar.set_mic_level(level)
