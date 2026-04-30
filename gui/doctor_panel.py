"""Doctor panel — right column: live STT caption + ASL response video."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QSizePolicy,
)


class DoctorPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("CLINICIAN  ·  Voice → ASL Response")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        self._video_widget = QVideoWidget()
        self._video_widget.setObjectName("videoCanvas")
        self._video_widget.setMinimumHeight(260)
        self._video_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self._video_widget, stretch=3)

        self._player = QMediaPlayer(self)
        self._audio_out = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_out)
        self._player.setVideoOutput(self._video_widget)
        self._audio_out.setVolume(1.0)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        live_label = QLabel("  Live transcript")
        live_label.setProperty("role", "section")
        layout.addWidget(live_label)

        self._partial = QLabel("Waiting for speech...")
        self._partial.setObjectName("partialCaption")
        self._partial.setWordWrap(True)
        layout.addWidget(self._partial)

        self._final = QLabel("")
        self._final.setObjectName("liveCaption")
        self._final.setWordWrap(True)
        layout.addWidget(self._final, stretch=1)

    # ------------------------------------------------------------------ #
    def update_partial(self, text: str) -> None:
        self._partial.setText(text if text else "Listening...")

    def update_final(self, text: str) -> None:
        self._final.setText(text)
        self._partial.setText("")

    def play_video(self, path: str) -> None:
        p = Path(path)
        if not p.exists():
            return
        self._player.stop()
        self._player.setSource(QUrl.fromLocalFile(str(p.resolve())))
        self._player.play()
