"""CameraScreen — Screen 2: live ASL preview + accumulating translation card."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy,
)
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

from gui import theme
from gui.video_widget import VideoWidget
from gui.widgets.glass_card import GlassCard


class CameraScreen(QWidget):
    continue_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")

        self._phrases: list[str] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 32)
        root.setSpacing(0)

        # ── Camera surface ──────────────────────────────────────────── #
        cam_card = GlassCard(deep=False)
        cam_layout = QVBoxLayout(cam_card)
        cam_layout.setContentsMargins(0, 0, 0, 0)

        self._video = VideoWidget(cam_card)
        # Override the object name so the rounded QSS applies via the card, not
        # the label's own rule — we paint inside the card frame directly.
        self._video.setObjectName("videoCanvas")
        cam_layout.addWidget(self._video)

        root.addWidget(cam_card, stretch=7)
        root.addSpacing(24)

        # ── Translation card ────────────────────────────────────────── #
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        trans_card = GlassCard(deep=True)
        trans_layout = QVBoxLayout(trans_card)
        trans_layout.setContentsMargins(24, 16, 24, 16)

        self._translation_label = QLabel("")
        self._translation_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._translation_label.setWordWrap(True)
        self._translation_label.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; "
            f"font-size: {theme.FONT_SIZE_BODY}px; "
            "font-weight: 300; "
            "background: transparent;"
        )
        self._translation_label.setText("Signing detected text will appear here…")
        self._translation_label.setStyleSheet(
            f"color: {theme.TEXT_HINT}; "
            f"font-size: {theme.FONT_SIZE_BODY}px; "
            "font-weight: 300; "
            "background: transparent;"
        )
        trans_layout.addWidget(self._translation_label)

        continue_btn = QPushButton("Continue →")
        continue_btn.setObjectName("continueBtn")
        continue_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        continue_btn.clicked.connect(self.continue_clicked)
        continue_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        bottom_row.addWidget(trans_card, stretch=1)
        bottom_row.addWidget(continue_btn, alignment=Qt.AlignmentFlag.AlignBottom)

        root.addLayout(bottom_row, stretch=2)

    # ------------------------------------------------------------------ #

    @pyqtSlot(object)
    def update_frame(self, frame) -> None:
        self._video.update_frame(frame)

    @pyqtSlot(str)
    def append_phrase(self, text: str) -> None:
        self._phrases.append(text)
        joined = " ".join(self._phrases)
        self._translation_label.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; "
            f"font-size: {theme.FONT_SIZE_BODY}px; "
            "font-weight: 300; "
            "background: transparent;"
        )
        self._translation_label.setText(joined)

    def clear_phrases(self) -> None:
        self._phrases.clear()
        self._translation_label.setStyleSheet(
            f"color: {theme.TEXT_HINT}; "
            f"font-size: {theme.FONT_SIZE_BODY}px; "
            "font-weight: 300; "
            "background: transparent;"
        )
        self._translation_label.setText("Signing detected text will appear here…")

    def current_text(self) -> str:
        return " ".join(self._phrases)
