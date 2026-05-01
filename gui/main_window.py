"""MainWindow — Connector (patient flow) left + DoctorPanel (clinician) right."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter

import config
from gui.connector import Connector
from gui.doctor_panel import DoctorPanel
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
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)

        self._connector = Connector()
        self._doctor    = DoctorPanel()

        splitter.addWidget(self._connector)
        splitter.addWidget(self._doctor)
        splitter.setSizes([800, 480])

        layout.addWidget(splitter)

    # ------------------------------------------------------------------ #
    # Public API called by main.py
    # ------------------------------------------------------------------ #

    def set_tts_worker(self, tts_worker) -> None:
        """Pass the TTSWorker to the Connector so AudioScreen can trigger it."""
        self._connector.set_tts_worker(tts_worker)

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

    @pyqtSlot(str)
    def on_partial_transcript(self, text: str) -> None:
        self._doctor.update_partial(text)

    @pyqtSlot(str)
    def on_final_transcript(self, text: str) -> None:
        self._doctor.update_final(text)

    @pyqtSlot(str)
    def on_play_video(self, path: str) -> None:
        self._doctor.play_video(path)

    @pyqtSlot(float)
    def on_mic_level(self, level: float) -> None:
        self._status_bar.set_mic_level(level)
