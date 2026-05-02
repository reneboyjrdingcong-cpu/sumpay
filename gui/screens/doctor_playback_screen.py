"""DoctorPlaybackScreen — Screen 9: plays the matched ASL video clip."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QStackedLayout,
)

from gui import theme
from gui.widgets.glass_card import GlassCard
from gui.widgets.circle_button import CircleButton


class _AspectRatioWidget(QWidget):
    """Centers a single child widget at exactly 16:9 inside its bounds."""

    def __init__(self, content: QWidget, parent=None):
        super().__init__(parent)
        self._content = content
        self._content.setParent(self)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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
        root.setContentsMargins(60, 32, 60, 32)
        root.setSpacing(0)

        # ── Top bar with back button ─────────────────────────────────────── #
        top_bar = QHBoxLayout()
        back_btn = QPushButton("‹ Back")
        back_btn.setFlat(True)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet(
            f"color: {theme.TEXT_HINT}; "
            f"font-size: {theme.FONT_SIZE_HINT}px; "
            "font-weight: 300; background: transparent; border: none;"
        )
        back_btn.clicked.connect(self.back)
        top_bar.addWidget(back_btn)
        top_bar.addStretch()
        root.addLayout(top_bar)
        root.addSpacing(12)

        # ── Outer glass card wraps the video ────────────────────────────── #
        outer_card = GlassCard(deep=False)
        outer_layout = QVBoxLayout(outer_card)
        outer_layout.setContentsMargins(20, 20, 20, 20)

        # Inner widget owns the stacked layout of placeholder + video widget.
        # _AspectRatioWidget re-parents and resizes it to a centered 16:9 rect.
        inner = QWidget()
        self._stack = QStackedLayout(inner)
        self._stack.setStackingMode(QStackedLayout.StackingMode.StackAll)
        self._stack.setContentsMargins(0, 0, 0, 0)

        self._placeholder = QLabel("Playing ASL response…")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet(
            f"color: {theme.TEXT_SECONDARY}; "
            "font-size: 28px; "
            "font-weight: 300; "
            f"background: {theme.BG_GLASS_DEEP};"
        )

        self._video_widget = QVideoWidget()
        self._video_widget.setObjectName("videoCanvas")

        self._stack.addWidget(self._placeholder)   # index 0
        self._stack.addWidget(self._video_widget)  # index 1
        self._stack.setCurrentIndex(0)

        self._video_area = _AspectRatioWidget(inner)
        outer_layout.addWidget(self._video_area)
        root.addWidget(outer_card, stretch=1)

        root.addSpacing(16)

        # ── Footer: caption pill ────────────────────────────────────────── #
        footer_card = GlassCard(deep=True)
        footer_layout = QVBoxLayout(footer_card)
        footer_layout.setContentsMargins(24, 10, 24, 10)

        self._caption_lbl = QLabel("")
        self._caption_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._caption_lbl.setWordWrap(True)
        self._caption_lbl.setStyleSheet(
            f"color: {theme.TEXT_SECONDARY}; "
            f"font-size: {theme.FONT_SIZE_HINT}px; "
            "font-style: italic; "
            "font-weight: 300; "
            "background: transparent;"
        )
        footer_layout.addWidget(self._caption_lbl)
        root.addWidget(footer_card, stretch=0)

        root.addSpacing(16)

        # ── Action row: Replay (red) + Continue (green) ─────────────────── #
        action_row = QHBoxLayout()
        action_row.setSpacing(40)
        action_row.addStretch()

        self._replay_btn = CircleButton("Replay", variant="retry")
        self._replay_btn.clicked.connect(self._on_replay)
        action_row.addWidget(self._replay_btn)

        self._continue_btn = CircleButton("Continue", variant="confirm")
        self._continue_btn.clicked.connect(self.done)
        action_row.addWidget(self._continue_btn)

        action_row.addStretch()
        root.addLayout(action_row)

        # ── Media player ─────────────────────────────────────────────────── #
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
