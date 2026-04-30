"""ConfirmScreen — Screen 3: show accumulated text, Confirm / Retry / Edit."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QTextEdit, QSizePolicy,
)

from gui import theme
from gui.widgets.glass_card import GlassCard
from gui.widgets.circle_button import CircleButton


class ConfirmScreen(QWidget):
    confirmed = pyqtSignal(str)
    retry = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")

        self._text = ""
        self._editing = False

        root = QVBoxLayout(self)
        root.setContentsMargins(60, 50, 60, 50)
        root.setSpacing(20)

        # ── Header card ─────────────────────────────────────────────── #
        header_card = GlassCard(deep=False)
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(28, 14, 28, 14)

        header_lbl = QLabel("Is this all you want to share?")
        header_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_lbl.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; "
            "font-size: 20px; "
            "font-weight: 400; "
            "background: transparent;"
        )
        header_layout.addWidget(header_lbl)

        root.addWidget(header_card)

        # ── Main row: text card + buttons ───────────────────────────── #
        content_row = QHBoxLayout()
        content_row.setSpacing(30)

        # Text card
        text_card = GlassCard(deep=True)
        text_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        text_layout = QVBoxLayout(text_card)
        text_layout.setContentsMargins(32, 32, 32, 32)

        self._text_label = QLabel("")
        self._text_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self._text_label.setWordWrap(True)
        self._text_label.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; "
            "font-size: 25px; "
            "font-weight: 300; "
            "background: transparent;"
        )

        self._text_edit = QTextEdit()
        self._text_edit.setObjectName("editableText")
        self._text_edit.setVisible(False)
        self._text_edit.setStyleSheet(
            "QTextEdit#editableText { "
            f"  color: {theme.TEXT_PRIMARY}; "
            "  font-size: 25px; "
            "  font-weight: 300; "
            "  background: transparent; "
            "  border: none; "
            "  selection-background-color: rgba(0, 122, 255, 60); "
            "}"
        )

        text_layout.addWidget(self._text_label)
        text_layout.addWidget(self._text_edit)

        # Buttons column
        btn_col = QVBoxLayout()
        btn_col.setSpacing(20)
        btn_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._confirm_btn = CircleButton("Confirm")
        self._retry_btn   = CircleButton("Retry")
        self._edit_btn    = CircleButton("Edit")

        self._confirm_btn.clicked.connect(self._on_confirm)
        self._retry_btn.clicked.connect(self._on_retry)
        self._edit_btn.clicked.connect(self._on_edit)

        btn_col.addWidget(self._confirm_btn)
        btn_col.addWidget(self._retry_btn)
        btn_col.addWidget(self._edit_btn)

        content_row.addWidget(text_card, stretch=3)
        content_row.addLayout(btn_col, stretch=0)

        root.addLayout(content_row, stretch=1)

    # ------------------------------------------------------------------ #

    def set_text(self, text: str) -> None:
        self._text = text
        self._editing = False
        self._text_label.setText(text if text else "(no text captured)")
        self._text_label.setVisible(True)
        self._text_edit.setVisible(False)

    # ------------------------------------------------------------------ #

    def _on_confirm(self) -> None:
        if self._editing:
            self._text = self._text_edit.toPlainText().strip()
        self.confirmed.emit(self._text)

    def _on_retry(self) -> None:
        self._editing = False
        self._text_label.setVisible(True)
        self._text_edit.setVisible(False)
        self.retry.emit()

    def _on_edit(self) -> None:
        if not self._editing:
            self._editing = True
            self._text_edit.setPlainText(self._text)
            self._text_label.setVisible(False)
            self._text_edit.setVisible(True)
            self._text_edit.setFocus()
