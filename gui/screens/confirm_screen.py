"""ConfirmScreen — Screen 3: show accumulated text, Confirm / Retry / Edit."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QSizePolicy, QTextEdit, QVBoxLayout, QWidget,
)

from gui import theme
from gui.widgets.circle_button import CircleButton
from gui.widgets.glass_card import GlassCard
from gui.widgets.screen_header import ScreenHeader


class ConfirmScreen(QWidget):
    confirmed = pyqtSignal(str)
    retry     = pyqtSignal()
    back      = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")

        self._text = ""
        self._editing = False

        root = QVBoxLayout(self)
        root.setContentsMargins(
            theme.SCREEN_PADDING_H, theme.SCREEN_PADDING_TOP,
            theme.SCREEN_PADDING_H, theme.SCREEN_PADDING_BOTTOM,
        )
        root.setSpacing(0)

        # ── Header ───────────────────────────────────────────────────── #
        header = ScreenHeader(title="Is this all you want to share?")
        header.back.connect(self.back)
        root.addWidget(header)
        root.addSpacing(theme.SPACE_LG)

        # ── Main row: text card + buttons ────────────────────────────── #
        content_row = QHBoxLayout()
        content_row.setSpacing(theme.SPACE_LG)

        # Text card
        self._text_card = GlassCard(deep=True)
        self._text_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        text_layout = QVBoxLayout(self._text_card)
        text_layout.setContentsMargins(
            theme.SPACE_LG, theme.SPACE_LG, theme.SPACE_LG, theme.SPACE_LG
        )
        text_layout.setSpacing(theme.SPACE_SM)

        # Top row: editing pill (right-aligned, hidden by default)
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.addStretch()
        self._editing_pill = QLabel("Editing")
        self._editing_pill.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; "
            f"font-size: {theme.FONT_SIZE_HINT}px; "
            f"font-weight: {theme.WEIGHT_MEDIUM}; "
            f"background-color: {theme.ACCENT_EDIT_TINT}; "
            "border-radius: 10px; "
            "padding: 4px 10px; "
            "letter-spacing: 1px;"
        )
        self._editing_pill.setVisible(False)
        top_row.addWidget(self._editing_pill)
        text_layout.addLayout(top_row)

        # Body text (label OR edit, swapped)
        self._text_label = QLabel("")
        self._text_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self._text_label.setWordWrap(True)
        self._text_label.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; "
            f"font-size: {theme.FONT_SIZE_HEADING}px; "
            f"font-weight: {theme.WEIGHT_LIGHT}; "
            "background: transparent;"
        )

        self._text_edit = QTextEdit()
        self._text_edit.setObjectName("editableText")
        self._text_edit.setVisible(False)

        text_layout.addWidget(self._text_label, stretch=1)
        text_layout.addWidget(self._text_edit, stretch=1)

        # Caption row: char / word count
        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(
            f"color: {theme.TEXT_HINT}; "
            f"font-size: {theme.FONT_SIZE_HINT}px; "
            f"font-weight: {theme.WEIGHT_REGULAR}; "
            "background: transparent;"
        )
        text_layout.addWidget(self._count_lbl, alignment=Qt.AlignmentFlag.AlignLeft)

        # Button column
        btn_col = QVBoxLayout()
        btn_col.setSpacing(theme.SPACE_MD)
        btn_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._confirm_btn = CircleButton("Confirm", variant="confirm")
        self._retry_btn   = CircleButton("Retry",   variant="retry")
        self._edit_btn    = CircleButton("Edit",    variant="edit")

        self._confirm_btn.clicked.connect(self._on_confirm)
        self._retry_btn.clicked.connect(self._on_retry)
        self._edit_btn.clicked.connect(self._on_edit)

        btn_col.addWidget(self._confirm_btn)
        btn_col.addWidget(self._edit_btn)
        btn_col.addWidget(self._retry_btn)

        content_row.addWidget(self._text_card, stretch=3)
        content_row.addLayout(btn_col, stretch=0)

        root.addLayout(content_row, stretch=1)

    # ------------------------------------------------------------------ #

    def set_text(self, text: str) -> None:
        self._text = text
        self._editing = False
        display = text if text else "(no text captured)"
        self._text_label.setText(display)
        self._text_label.setVisible(True)
        self._text_edit.setVisible(False)
        self._editing_pill.setVisible(False)
        self._set_card_editing(False)
        self._update_counts(text)

    # ------------------------------------------------------------------ #

    def _update_counts(self, text: str) -> None:
        text = text or ""
        chars = len(text)
        words = len([w for w in text.split() if w])
        if chars == 0:
            self._count_lbl.setText("")
        else:
            self._count_lbl.setText(
                f"{chars} char{'s' if chars != 1 else ''} · "
                f"{words} word{'s' if words != 1 else ''}"
            )

    def _set_card_editing(self, editing: bool) -> None:
        self._text_card.setProperty("editing", "true" if editing else "false")
        self._text_card.style().unpolish(self._text_card)
        self._text_card.style().polish(self._text_card)

    def _on_confirm(self) -> None:
        if self._editing:
            self._text = self._text_edit.toPlainText().strip()
        self.confirmed.emit(self._text)

    def _on_retry(self) -> None:
        self._editing = False
        self._text_label.setVisible(True)
        self._text_edit.setVisible(False)
        self._editing_pill.setVisible(False)
        self._set_card_editing(False)
        self.retry.emit()

    def _on_edit(self) -> None:
        if not self._editing:
            self._editing = True
            self._text_edit.setPlainText(self._text)
            self._text_label.setVisible(False)
            self._text_edit.setVisible(True)
            self._editing_pill.setVisible(True)
            self._set_card_editing(True)
            self._text_edit.setFocus()
            self._text_edit.textChanged.connect(self._on_edit_changed)

    def _on_edit_changed(self) -> None:
        self._update_counts(self._text_edit.toPlainText())
