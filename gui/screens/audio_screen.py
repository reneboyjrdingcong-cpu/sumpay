"""AudioScreen — Screen 5: TTS playback with rippling speaker halo, replay, done."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from gui import theme
from gui.widgets.primary_button import PrimaryButton
from gui.widgets.screen_header import ScreenHeader
from gui.widgets.speaker_halo import SpeakerHalo


class AudioScreen(QWidget):
    done             = pyqtSignal()
    back             = pyqtSignal()
    replay_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")

        self._tts_busy = False
        self._finished = False
        self._text     = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(
            theme.SCREEN_PADDING_H, theme.SCREEN_PADDING_TOP,
            theme.SCREEN_PADDING_H, theme.SCREEN_PADDING_BOTTOM,
        )
        root.setSpacing(0)

        # Header
        header = ScreenHeader()
        header.back.connect(self.back)
        root.addWidget(header)

        root.addStretch(1)

        # Speaker halo
        self._halo = SpeakerHalo(on_click=self.replay_requested.emit)
        halo_row = QHBoxLayout()
        halo_row.setContentsMargins(0, 0, 0, 0)
        halo_row.addStretch()
        halo_row.addWidget(self._halo)
        halo_row.addStretch()
        root.addLayout(halo_row)

        root.addSpacing(theme.SPACE_MD)

        # Hint label
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

        # Transcript preview
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

        # Action row: Replay (left) + Done (right)
        action_pair = QWidget()
        action_pair.setFixedWidth(360)
        pair_layout = QHBoxLayout(action_pair)
        pair_layout.setContentsMargins(0, 0, 0, 0)
        pair_layout.setSpacing(0)

        self._replay_btn = PrimaryButton("Replay", variant="secondary")
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

    def set_text(self, text: str) -> None:
        self._text = text or ""
        self._transcript_lbl.setText(f'"{self._text}"' if self._text else "")

    @pyqtSlot(bool)
    def on_busy(self, busy: bool) -> None:
        self._tts_busy = busy
        self._halo.set_playing(busy)
        if busy:
            self._finished = False
            self._hint_lbl.setText("Reading your message aloud…")
            self._replay_btn.setEnabled(False)
        else:
            self._finished = True
            self._hint_lbl.setText("Message delivered")
            self._replay_btn.setEnabled(True)

    def reset(self) -> None:
        self._halo.set_playing(False)
        self._hint_lbl.setText("Reading your message aloud…")
        self._replay_btn.setEnabled(False)
        self._finished = False
        self._tts_busy = False
