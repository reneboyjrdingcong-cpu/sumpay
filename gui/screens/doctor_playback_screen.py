"""DoctorPlaybackScreen — Screen 9: plays the matched ASL video clip."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
)

from gui import theme
from gui.widgets.glass_card import GlassCard


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

        inner_card = GlassCard(deep=True)
        inner_layout = QVBoxLayout(inner_card)
        inner_layout.setContentsMargins(0, 0, 0, 0)

        self._video_widget = QVideoWidget()
        self._video_widget.setObjectName("videoCanvas")
        self._video_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        inner_layout.addWidget(self._video_widget)

        self._placeholder = QLabel("Playing ASL response…")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet(
            f"color: {theme.TEXT_SECONDARY}; "
            "font-size: 28px; "
            "font-weight: 300; "
            "background: transparent;"
        )
        inner_layout.addWidget(self._placeholder)
        self._placeholder.setVisible(True)
        self._video_widget.setVisible(False)

        outer_layout.addWidget(inner_card)
        root.addWidget(outer_card, stretch=5)

        root.addSpacing(16)

        # ── Footer: caption pill + tap hint ─────────────────────────────── #
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

        root.addSpacing(10)

        # Tap-to-continue hint — always visible so user is never stuck
        self._hint_lbl = QLabel("Tap anywhere to continue →")
        self._hint_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hint_lbl.setStyleSheet(
            f"color: {theme.TEXT_HINT}; "
            f"font-size: {theme.FONT_SIZE_HINT}px; "
            "font-weight: 300; "
            "background: transparent;"
        )
        root.addWidget(self._hint_lbl)

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
            self._placeholder.setText("ASL clip not found\n(tap to continue)")
            self._placeholder.setVisible(True)
            self._video_widget.setVisible(False)
            return

        self._placeholder.setVisible(False)
        self._video_widget.setVisible(True)
        self._player.stop()
        self._player.setSource(QUrl.fromLocalFile(str(p.resolve())))
        self._player.play()

    def reset(self) -> None:
        self._player.stop()
        self._placeholder.setText("Playing ASL response…")
        self._placeholder.setVisible(True)
        self._video_widget.setVisible(False)
        self._caption_lbl.setText("")

    # ------------------------------------------------------------------ #

    @pyqtSlot(QMediaPlayer.MediaStatus)
    def _on_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._player.stop()

    # Always tappable — user is never stuck on this screen
    def mousePressEvent(self, event) -> None:
        self.done.emit()
