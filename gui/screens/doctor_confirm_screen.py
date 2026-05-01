"""DoctorConfirmScreen — Screen 8: review/edit transcribed or typed text."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QSizePolicy,
    QPushButton,
)

from gui import theme
from gui.widgets.glass_card import GlassCard
from gui.widgets.circle_button import CircleButton


class DoctorConfirmScreen(QWidget):
    confirmed = pyqtSignal(str)
    retry     = pyqtSignal()
    back      = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")

        self._text = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(60, 32, 60, 50)
        root.setSpacing(0)

        # ── Back button ──────────────────────────────────────────────────── #
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
        root.addSpacing(18)

        # ── Header card ─────────────────────────────────────────────────── #
        header_card = GlassCard(deep=False)
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(28, 14, 28, 14)

        header_lbl = QLabel("Is this what you want to share?")
        header_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_lbl.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; "
            "font-size: 20px; "
            "font-weight: 400; "
            "background: transparent;"
        )
        header_layout.addWidget(header_lbl)
        root.addWidget(header_card)

        # ── Main row: text card + buttons ───────────────────────────────── #
        content_row = QHBoxLayout()
        content_row.setSpacing(30)

        text_card = GlassCard(deep=True)
        text_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        text_layout = QVBoxLayout(text_card)
        text_layout.setContentsMargins(32, 32, 32, 32)

        self._text_edit = QTextEdit()
        self._text_edit.setObjectName("editableText")
        self._text_edit.setPlaceholderText("Type or edit the message you want to share…")
        self._text_edit.setStyleSheet(
            "QTextEdit#editableText { "
            f"  color: {theme.TEXT_PRIMARY}; "
            "  font-size: 25px; "
            "  font-weight: 300; "
            "  background: transparent; "
            "  border: none; "
            f"  selection-background-color: rgba(0, 122, 255, 60); "
            "}"
        )
        text_layout.addWidget(self._text_edit)

        # Buttons column
        btn_col = QVBoxLayout()
        btn_col.setSpacing(20)
        btn_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._confirm_btn = CircleButton("Confirm")
        self._retry_btn   = CircleButton("Retry")

        self._confirm_btn.clicked.connect(self._on_confirm)
        self._retry_btn.clicked.connect(self._on_retry)

        btn_col.addWidget(self._confirm_btn)
        btn_col.addWidget(self._retry_btn)

        content_row.addWidget(text_card, stretch=3)
        content_row.addLayout(btn_col, stretch=0)

        root.addLayout(content_row, stretch=1)

    # ------------------------------------------------------------------ #

    def set_text(self, text: str, editable: bool = True) -> None:
        self._text = text
        self._text_edit.setPlainText(text)
        if editable:
            self._text_edit.setFocus()

    # ------------------------------------------------------------------ #

    def _on_confirm(self) -> None:
        text = self._text_edit.toPlainText().strip()
        if text:
            self.confirmed.emit(text)

    def _on_retry(self) -> None:
        self._text_edit.clear()
        self.retry.emit()
