"""TranscriptPanel — scrolling list of recognised ASL sentences."""
from __future__ import annotations

from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QSizePolicy
from PyQt6.QtCore import Qt


class TranscriptPanel(QListWidget):
    MAX_ENTRIES = 50

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setWordWrap(True)
        self.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)

    def append_sentence(self, text: str) -> None:
        if not text.strip():
            return
        item = QListWidgetItem(f"  {text}")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        self.addItem(item)
        if self.count() > self.MAX_ENTRIES:
            self.takeItem(0)
        self.scrollToBottom()
