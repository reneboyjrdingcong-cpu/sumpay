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
    back             = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")

        self._phrases: list[str] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(40, 16, 40, 32)
        root.setSpacing(0)

        # ── Back button ─────────────────────────────────────────────── #
        top_bar = QHBoxLayout()
        back_btn = QPushButton("‹ Back")
        back_btn.setFlat(True)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet(
            f"color: {theme.TEXT_HINT}; font-size: {theme.FONT_SIZE_HINT}px; "
            "font-weight: 300; background: transparent; border: none;"
        )
        back_btn.clicked.connect(self.back)
        top_bar.addWidget(back_btn)
        top_bar.addStretch()
        root.addLayout(top_bar)
        root.addSpacing(8)

        # ── Camera surface ──────────────────────────────────────────── #
        cam_card = GlassCard(deep=False)
        cam_layout = QVBoxLayout(cam_card)
        cam_layout.setContentsMargins(0, 0, 0, 0)

        self._video = VideoWidget(cam_card)
        self._video.setObjectName("videoCanvas")
        cam_layout.addWidget(self._video)

        root.addWidget(cam_card, stretch=7)
        root.addSpacing(24)

        # ── Translation card (Continue button lives inside) ─────────── #
        trans_card = GlassCard(deep=True)
        trans_layout = QVBoxLayout(trans_card)
        trans_layout.setContentsMargins(24, 16, 24, 16)

        self._translation_label = QLabel("Signing detected text will appear here…")
        self._translation_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._translation_label.setWordWrap(True)
        self._translation_label.setStyleSheet(
            f"color: {theme.TEXT_HINT}; "
            f"font-size: {theme.FONT_SIZE_BODY}px; "
            "font-weight: 300; "
            "background: transparent;"
        )
        trans_layout.addWidget(self._translation_label, stretch=1)

        continue_btn = QPushButton("Continue →")
        continue_btn.setObjectName("continueBtn")
        continue_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        continue_btn.clicked.connect(self.continue_clicked)
        continue_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        continue_row = QHBoxLayout()
        continue_row.setContentsMargins(0, 8, 0, 0)
        continue_row.addStretch()
        continue_row.addWidget(continue_btn)
        trans_layout.addLayout(continue_row)

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(trans_card)
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
