"""DoctorPlaybackScreen — Screen 9: plays the matched ASL video clip."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QStackedLayout,
)

from gui import theme
from gui.widgets.glass_card import GlassCard
from gui.widgets.primary_button import PrimaryButton
from gui.widgets.screen_header import ScreenHeader


class _AspectRatioWidget(QWidget):
    """Centers a single child widget at exactly 16:9 inside its bounds."""

    def __init__(self, content: QWidget, parent=None):
        super().__init__(parent)
        self._content = content
        self._content.setParent(self)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.setMinimumSize(640, 360)

    def resizeEvent(self, event):
        w, h = self.width(), self.height()
        if w * 9 > h * 16:
            new_h, new_w = h, h * 16 // 9
        else:
            new_w, new_h = w, w * 9 // 16
        x = (w - new_w) // 2
        y = (h - new_h) // 2
        self._content.setGeometry(x, y, new_w, new_h)
        super().resizeEvent(event)


class DoctorPlaybackScreen(QWidget):
    done = pyqtSignal()
    back = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")

        root = QVBoxLayout(self)
        root.setContentsMargins(
            theme.SCREEN_PADDING_H, theme.SCREEN_PADDING_TOP,
            theme.SCREEN_PADDING_H, theme.SCREEN_PADDING_BOTTOM,
        )
        root.setSpacing(0)

        header = ScreenHeader()
        header.back.connect(self.back)
        root.addWidget(header)
        root.addSpacing(theme.SPACE_MD)

        # ── Outer glass card wraps the video ────────────────────────── #
        outer_card = GlassCard(deep=False)
        outer_layout = QVBoxLayout(outer_card)
        outer_layout.setContentsMargins(
            theme.SPACE_MD, theme.SPACE_MD, theme.SPACE_MD, theme.SPACE_MD
        )

        inner = QWidget()
        self._stack = QStackedLayout(inner)
        self._stack.setStackingMode(QStackedLayout.StackingMode.StackAll)
        self._stack.setContentsMargins(0, 0, 0, 0)

        self._placeholder = QLabel("Playing ASL response…")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet(
            f"color: {theme.TEXT_SECONDARY}; "
            f"font-size: {theme.FONT_SIZE_HEADING}px; "
            f"font-weight: {theme.WEIGHT_LIGHT}; "
            f"background: {theme.BG_GLASS_DEEP};"
        )

        self._video_widget = QVideoWidget()
        self._video_widget.setObjectName("videoCanvas")

        self._stack.addWidget(self._placeholder)
        self._stack.addWidget(self._video_widget)
        self._stack.setCurrentIndex(0)

        self._video_area = _AspectRatioWidget(inner)
        outer_layout.addWidget(self._video_area)
        root.addWidget(outer_card, stretch=1)

        root.addSpacing(theme.SPACE_LG)

        # ── Caption card — promoted to body-LG (the message is content) ─ #
        caption_card = GlassCard(deep=True)
        caption_layout = QVBoxLayout(caption_card)
        caption_layout.setContentsMargins(
            theme.SPACE_LG, theme.SPACE_SM, theme.SPACE_LG, theme.SPACE_SM
        )

        self._caption_lbl = QLabel("")
        self._caption_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._caption_lbl.setWordWrap(True)
        self._caption_lbl.setStyleSheet(
            f"color: {theme.TEXT_SECONDARY}; "
            f"font-size: {theme.FONT_SIZE_CAPTION}px; "
            "font-style: italic; "
            f"font-weight: {theme.WEIGHT_LIGHT}; "
            "background: transparent;"
        )
        caption_layout.addWidget(self._caption_lbl)
        root.addWidget(caption_card, stretch=0)

        root.addSpacing(theme.SPACE_XL)

        # ── Action pair: Replay (left) + Continue (right), 360 px row ─── #
        action_pair = QWidget()
        action_pair.setFixedWidth(360)
        pair_layout = QHBoxLayout(action_pair)
        pair_layout.setContentsMargins(0, 0, 0, 0)
        pair_layout.setSpacing(0)

        self._replay_btn = PrimaryButton("Replay", variant="retry")
        self._replay_btn.clicked.connect(self._on_replay)
        pair_layout.addWidget(self._replay_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        pair_layout.addStretch()

        self._continue_btn = PrimaryButton("Continue", variant="confirm")
        self._continue_btn.clicked.connect(self.done)
        pair_layout.addWidget(self._continue_btn, alignment=Qt.AlignmentFlag.AlignRight)

        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.addStretch()
        action_row.addWidget(action_pair)
        action_row.addStretch()

        root.addLayout(action_row)
        root.addStretch(1)

        # ── Media player ─────────────────────────────────────────────── #
        self._player    = QMediaPlayer(self)
        self._audio_out = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_out)
        self._player.setVideoOutput(self._video_widget)
        self._audio_out.setVolume(1.0)

        self._player.mediaStatusChanged.connect(self._on_status_changed)

    # ------------------------------------------------------------------ #

    @pyqtSlot(str)
    def set_text(self, text: str) -> None:
        self._caption_lbl.setText(text)

    @pyqtSlot(str)
    def play_video(self, path: str) -> None:
        p = Path(path)
        if not p.exists():
            self._placeholder.setText("ASL clip not found")
            self._stack.setCurrentIndex(0)
            return

        self._stack.setCurrentIndex(1)
        self._player.stop()
        self._player.setSource(QUrl.fromLocalFile(str(p.resolve())))
        self._player.play()

    def reset(self) -> None:
        self._player.stop()
        self._placeholder.setText("Playing ASL response…")
        self._stack.setCurrentIndex(0)
        self._caption_lbl.setText("")

    # ------------------------------------------------------------------ #

    def _on_replay(self) -> None:
        self._player.setPosition(0)
        self._player.play()

    @pyqtSlot(QMediaPlayer.MediaStatus)
    def _on_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._player.stop()
