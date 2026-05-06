"""DoctorConfirmScreen — Screen 8: review/edit transcribed or typed text.

Mirrors the patient ConfirmScreen visual grammar: read-only label by default,
swap to QTextEdit when Edit is pressed; editing-state hairline + "Editing"
pill while modifying. For the Type path the connector hands an empty string,
so we auto-enter editing mode whenever set_text is called with empty text.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QSizePolicy, QTextEdit, QVBoxLayout, QWidget,
)

from gui import theme
from gui.widgets.glass_card import GlassCard
from gui.widgets.primary_button import PrimaryButton
from gui.widgets.screen_header import ScreenHeader


class DoctorConfirmScreen(QWidget):
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

        header = ScreenHeader(title="Is this what you want to share?")
        header.back.connect(self.back)
        root.addWidget(header)
        root.addSpacing(theme.SPACE_LG)

        # ── Main row: text card + buttons ────────────────────────────── #
        content_row = QHBoxLayout()
        content_row.setSpacing(theme.SPACE_LG)

        self._text_card = GlassCard(deep=True)
        self._text_card.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        text_layout = QVBoxLayout(self._text_card)
        text_layout.setContentsMargins(
            theme.SPACE_LG, theme.SPACE_LG, theme.SPACE_LG, theme.SPACE_LG
        )
        text_layout.setSpacing(theme.SPACE_SM)

        # Editing pill (right-aligned, hidden by default)
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

        # Body label (read-only) and editor (editable), swapped
        self._text_label = QLabel("")
        self._text_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        self._text_label.setWordWrap(True)
        self._text_label.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; "
            f"font-size: {theme.FONT_SIZE_HEADING}px; "
            f"font-weight: {theme.WEIGHT_LIGHT}; "
            "background: transparent;"
        )

        self._text_edit = QTextEdit()
        self._text_edit.setObjectName("editableText")
        self._text_edit.setPlaceholderText("Type or edit the message you want to share…")
        self._text_edit.setStyleSheet(
            "QTextEdit#editableText { "
            f"  color: {theme.TEXT_PRIMARY}; "
            f"  font-size: {theme.FONT_SIZE_HEADING}px; "
            f"  font-weight: {theme.WEIGHT_LIGHT}; "
            "  background: transparent; "
            "  border: none; "
            f"  selection-background-color: {theme.TEXT_SELECTION}; "
            "}"
        )
        self._text_edit.setVisible(False)
        self._text_edit.textChanged.connect(self._on_edit_changed)

        text_layout.addWidget(self._text_label, stretch=1)
        text_layout.addWidget(self._text_edit, stretch=1)

        # Char/word count caption
        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(
            f"color: {theme.TEXT_HINT}; "
            f"font-size: {theme.FONT_SIZE_HINT}px; "
            f"font-weight: {theme.WEIGHT_REGULAR}; "
            "background: transparent;"
        )
        text_layout.addWidget(self._count_lbl, alignment=Qt.AlignmentFlag.AlignLeft)

        # Button column — Confirm / Retry / Edit (mirrors Phase 1)
        btn_col = QVBoxLayout()
        btn_col.setSpacing(theme.SPACE_MD)
        btn_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._confirm_btn = PrimaryButton("Confirm", variant="confirm")
        self._retry_btn   = PrimaryButton("Retry",   variant="retry")
        self._edit_btn    = PrimaryButton("Edit",    variant="edit")

        self._confirm_btn.clicked.connect(self._on_confirm)
        self._retry_btn.clicked.connect(self._on_retry)
        self._edit_btn.clicked.connect(self._on_edit)

        btn_col.addWidget(self._confirm_btn)
        btn_col.addWidget(self._retry_btn)
        btn_col.addWidget(self._edit_btn)

        content_row.addWidget(self._text_card, stretch=3)
        content_row.addLayout(btn_col, stretch=0)

        root.addLayout(content_row, stretch=1)

    # ------------------------------------------------------------------ #

    def set_text(self, text: str, editable: bool = True) -> None:
        self._text = text or ""
        # Empty text (Type path) starts in edit mode so the doctor can type
        # straight away; non-empty text (Record path) starts read-only.
        if editable and not self._text:
            self._enter_edit_mode(initial="")
        else:
            self._exit_edit_mode()
            display = self._text if self._text else "(no text captured)"
            self._text_label.setText(display)
            self._update_counts(self._text)

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

    def _enter_edit_mode(self, initial: str | None = None) -> None:
        self._editing = True
        if initial is None:
            initial = self._text
        self._text_edit.blockSignals(True)
        self._text_edit.setPlainText(initial)
        self._text_edit.blockSignals(False)
        self._text_label.setVisible(False)
        self._text_edit.setVisible(True)
        self._editing_pill.setVisible(True)
        self._set_card_editing(True)
        self._text_edit.setFocus()
        self._update_counts(initial)

    def _exit_edit_mode(self) -> None:
        self._editing = False
        self._text_label.setVisible(True)
        self._text_edit.setVisible(False)
        self._editing_pill.setVisible(False)
        self._set_card_editing(False)

    def _on_confirm(self) -> None:
        if self._editing:
            self._text = self._text_edit.toPlainText().strip()
        if self._text:
            self.confirmed.emit(self._text)

    def _on_retry(self) -> None:
        self._exit_edit_mode()
        self._text_edit.clear()
        self._text = ""
        self.retry.emit()

    def _on_edit(self) -> None:
        if not self._editing:
            self._enter_edit_mode()

    def _on_edit_changed(self) -> None:
        if self._editing:
            self._update_counts(self._text_edit.toPlainText())
