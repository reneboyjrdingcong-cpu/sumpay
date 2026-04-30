"""MainWindow — two-column dashboard with header and status bar."""
from __future__ import annotations

import re
from pathlib import Path

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QFrame, QSplitter,
)
from PyQt6.QtCore import Qt

import config
from gui.patient_panel import PatientPanel
from gui.doctor_panel import DoctorPanel
from gui.status_bar import SumpayStatusBar
from gui import theme


def _load_stylesheet() -> str:
    qss = config.STYLES_QSS.read_text(encoding="utf-8")
    subs = {
        "@BG_PRIMARY@": theme.BG_PRIMARY,
        "@BG_SECONDARY@": theme.BG_SECONDARY,
        "@BG_PANEL@": theme.BG_PANEL,
        "@BORDER@": theme.BORDER,
        "@ACCENT@": theme.ACCENT,
        "@ACCENT_DIM@": theme.ACCENT_DIM,
        "@TEXT_PRIMARY@": theme.TEXT_PRIMARY,
        "@TEXT_SECONDARY@": theme.TEXT_SECONDARY,
        "@TEXT_MUTED@": theme.TEXT_MUTED,
        "@SUCCESS@": theme.SUCCESS,
        "@WARNING@": theme.WARNING,
        "@ERROR@": theme.ERROR,
        "@FONT_FAMILY@": theme.FONT_FAMILY,
        "@FONT_SIZE_BASE@": str(theme.FONT_SIZE_BASE),
        "@FONT_SIZE_HEADER@": str(theme.FONT_SIZE_HEADER),
        "@FONT_SIZE_TRANSCRIPT@": str(theme.FONT_SIZE_TRANSCRIPT),
        "@FONT_SIZE_CAPTION@": str(theme.FONT_SIZE_CAPTION),
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
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)

        self.patient_panel = PatientPanel()
        self.doctor_panel = DoctorPanel()
        splitter.addWidget(self.patient_panel)
        splitter.addWidget(self.doctor_panel)
        splitter.setSizes([700, 700])

        root.addWidget(splitter, stretch=1)

    # ------------------------------------------------------------------ #

    def _build_header(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("headerBar")
        lay = QVBoxLayout(bar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        title = QLabel("PROJECT SUMPAY")
        title.setObjectName("headerTitle")
        lay.addWidget(title)

        subtitle = QLabel(
            "Offline · Edge-AI · Two-Way Communication  ·  "
            "100% Private · Zero Cloud Dependencies"
        )
        subtitle.setObjectName("headerSubtitle")
        lay.addWidget(subtitle)

        return bar

    # ------------------------------------------------------------------ #
    # Slots wired by main.py
    # ------------------------------------------------------------------ #

    @pyqtSlot(object)
    def on_frame(self, frame) -> None:
        self.patient_panel.update_frame(frame)

    @pyqtSlot(float)
    def on_fps(self, fps: float) -> None:
        self._status_bar.set_fps(fps)

    @pyqtSlot(str, float)
    def on_recognized(self, sentence: str, confidence: float) -> None:
        self.patient_panel.append_sentence(sentence)
        self._status_bar.set_confidence(confidence)

    @pyqtSlot(bool)
    def on_tts_busy(self, busy: bool) -> None:
        self._status_bar.set_tts_busy(busy)

    @pyqtSlot(str)
    def on_partial_transcript(self, text: str) -> None:
        self.doctor_panel.update_partial(text)

    @pyqtSlot(str)
    def on_final_transcript(self, text: str) -> None:
        self.doctor_panel.update_final(text)

    @pyqtSlot(str)
    def on_play_video(self, path: str) -> None:
        self.doctor_panel.play_video(path)

    @pyqtSlot(float)
    def on_mic_level(self, level: float) -> None:
        self._status_bar.set_mic_level(level)
