"""Patient panel — left column: live webcam + ASL transcript."""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QSizePolicy
from gui.video_widget import VideoWidget
from gui.transcript_panel import TranscriptPanel


class PatientPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("PATIENT  ·  Sign Language → Voice & Text")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        self.video = VideoWidget()
        layout.addWidget(self.video, stretch=3)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        transcript_label = QLabel("  Recognised sentences")
        transcript_label.setProperty("role", "section")
        layout.addWidget(transcript_label)

        self.transcript = TranscriptPanel()
        layout.addWidget(self.transcript, stretch=2)

    def update_frame(self, frame) -> None:
        self.video.update_frame(frame)

    def append_sentence(self, text: str) -> None:
        self.transcript.append_sentence(text)
