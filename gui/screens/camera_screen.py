"""CameraScreen — Screen 2: live ASL preview + accumulating translation card."""
from __future__ import annotations

from PyQt6.QtCore import (
    Qt, pyqtSignal, pyqtSlot, QPropertyAnimation, QEasingCurve, QTimer,
)
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QSizePolicy, QStackedLayout, QVBoxLayout, QWidget,
)

from gui import theme
from gui.video_widget import VideoWidget
from gui.widgets.glass_card import GlassCard
from gui.widgets.primary_button import PrimaryButton
from gui.widgets.screen_header import ScreenHeader


class _StatusDot(QWidget):
    """10×10 colored dot — pulses green when active, holds gray when idle."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(10, 10)
        self._opacity = 1.0
        self._active = False

    def set_active(self, active: bool) -> None:
        self._active = active
        self.update()

    def set_opacity(self, v: float) -> None:
        self._opacity = v
        self.update()

    def get_opacity(self) -> float:
        return self._opacity

    opacity = property(get_opacity, set_opacity)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._active:
            c = QColor(theme.ACCENT_PRIMARY)
            c.setAlphaF(max(0.0, min(1.0, self._opacity)))
        else:
            c = QColor(theme.TEXT_HINT)
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(self.rect())
        p.end()


class CameraScreen(QWidget):
    continue_clicked = pyqtSignal()
    back             = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {theme.BG_PRIMARY};")

        self._phrases: list[str] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(
            theme.SCREEN_PADDING_H, theme.SCREEN_PADDING_TOP,
            theme.SCREEN_PADDING_H, theme.SCREEN_PADDING_BOTTOM,
        )
        root.setSpacing(0)

        # ── Header ───────────────────────────────────────────────────── #
        header = ScreenHeader(title="Sign your message")
        header.back.connect(self.back)
        root.addWidget(header)
        root.addSpacing(theme.SPACE_MD)

        # ── Camera surface (with overlay status pill) ────────────────── #
        cam_card = GlassCard(deep=False)
        cam_stack = QStackedLayout(cam_card)
        cam_stack.setStackingMode(QStackedLayout.StackingMode.StackAll)
        cam_stack.setContentsMargins(0, 0, 0, 0)

        self._video = VideoWidget()
        self._video.setObjectName("videoCanvas")
        cam_stack.addWidget(self._video)

        # Status pill overlays the top-left of the camera surface
        pill_overlay = QWidget()
        pill_overlay_layout = QVBoxLayout(pill_overlay)
        pill_overlay_layout.setContentsMargins(
            theme.SPACE_SM, theme.SPACE_SM, theme.SPACE_SM, theme.SPACE_SM
        )
        pill_overlay_layout.setSpacing(0)

        pill_row = QHBoxLayout()
        pill_row.setContentsMargins(0, 0, 0, 0)
        pill_row.setSpacing(theme.SPACE_XS)

        self._status_pill = QWidget()
        self._status_pill.setObjectName("statusPill")
        pill_inner = QHBoxLayout(self._status_pill)
        pill_inner.setContentsMargins(12, 6, 14, 6)
        pill_inner.setSpacing(theme.SPACE_XS)

        self._status_dot = _StatusDot()
        pill_inner.addWidget(self._status_dot, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._status_lbl = QLabel("Listening…")
        self._status_lbl.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; "
            f"font-size: {theme.FONT_SIZE_HINT}px; "
            f"font-weight: {theme.WEIGHT_REGULAR}; "
            "background: transparent;"
        )
        pill_inner.addWidget(self._status_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)

        pill_row.addWidget(self._status_pill)
        pill_row.addStretch()
        pill_overlay_layout.addLayout(pill_row)
        pill_overlay_layout.addStretch()
        pill_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        cam_stack.addWidget(pill_overlay)

        root.addWidget(cam_card, stretch=80)
        root.addSpacing(theme.SPACE_MD)

        # ── Translation card ─────────────────────────────────────────── #
        trans_card = GlassCard(deep=True)
        trans_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        trans_layout = QVBoxLayout(trans_card)
        trans_layout.setContentsMargins(
            theme.SPACE_MD, theme.SPACE_MD, theme.SPACE_MD, theme.SPACE_MD
        )
        trans_layout.setSpacing(theme.SPACE_XS)

        # Caption row: label on left, phrase count on right
        caption_row = QHBoxLayout()
        caption_row.setContentsMargins(0, 0, 0, 0)
        caption_row.setSpacing(theme.SPACE_SM)

        caption_lbl = QLabel("Detected text")
        caption_lbl.setStyleSheet(
            f"color: {theme.TEXT_HINT}; "
            f"font-size: {theme.FONT_SIZE_HINT}px; "
            f"font-weight: {theme.WEIGHT_REGULAR}; "
            "background: transparent; "
            "letter-spacing: 1px;"
        )
        caption_row.addWidget(caption_lbl)
        caption_row.addStretch()

        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(
            f"color: {theme.TEXT_HINT}; "
            f"font-size: {theme.FONT_SIZE_HINT}px; "
            f"font-weight: {theme.WEIGHT_REGULAR}; "
            "background: transparent;"
        )
        caption_row.addWidget(self._count_lbl)

        trans_layout.addLayout(caption_row)

        # Body text
        self._translation_label = QLabel("Waiting for signs…")
        self._translation_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self._translation_label.setWordWrap(True)
        trans_layout.addWidget(self._translation_label, stretch=1)

        # Continue action — bottom-right
        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, theme.SPACE_SM, 0, 0)
        action_row.addStretch()
        self._continue_btn = PrimaryButton("Continue", variant="confirm")
        self._continue_btn.clicked.connect(self.continue_clicked)
        action_row.addWidget(self._continue_btn)
        trans_layout.addLayout(action_row)

        root.addWidget(trans_card, stretch=22)

        # ── Animations ───────────────────────────────────────────────── #
        self._dot_anim = QPropertyAnimation(self._status_dot, b"opacity", self)
        self._dot_anim.setDuration(900)
        self._dot_anim.setStartValue(0.35)
        self._dot_anim.setEndValue(1.0)
        self._dot_anim.setEasingCurve(QEasingCurve.Type.SineCurve)
        self._dot_anim.setLoopCount(-1)

        # When append_phrase fires, briefly enter "Signing…" state
        self._signing_timer = QTimer(self)
        self._signing_timer.setSingleShot(True)
        self._signing_timer.setInterval(1500)
        self._signing_timer.timeout.connect(self._set_listening)

        self._apply_empty_state()

    # ------------------------------------------------------------------ #

    def _apply_empty_state(self) -> None:
        self._translation_label.setText("Waiting for signs…")
        self._translation_label.setStyleSheet(
            f"color: {theme.TEXT_HINT}; "
            f"font-size: {theme.FONT_SIZE_BODY_LG}px; "
            f"font-weight: {theme.WEIGHT_LIGHT}; "
            "background: transparent; "
            "font-style: italic;"
        )
        self._count_lbl.setText("")

    def _apply_populated_state(self, text: str) -> None:
        self._translation_label.setText(text)
        self._translation_label.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; "
            f"font-size: {theme.FONT_SIZE_BODY_LG}px; "
            f"font-weight: {theme.WEIGHT_LIGHT}; "
            "background: transparent;"
        )
        n = len(self._phrases)
        self._count_lbl.setText(f"{n} phrase{'s' if n != 1 else ''}")

    def _set_signing(self) -> None:
        self._status_lbl.setText("Signing…")
        self._status_dot.set_active(True)
        if self._dot_anim.state() != QPropertyAnimation.State.Running:
            self._dot_anim.start()
        self._signing_timer.start()

    def _set_listening(self) -> None:
        self._status_lbl.setText("Listening…")
        self._status_dot.set_active(False)
        self._dot_anim.stop()
        self._status_dot.set_opacity(1.0)

    # ------------------------------------------------------------------ #

    @pyqtSlot(object)
    def update_frame(self, frame) -> None:
        self._video.update_frame(frame)

    @pyqtSlot(str)
    def append_phrase(self, text: str) -> None:
        self._phrases.append(text)
        self._apply_populated_state(" ".join(self._phrases))
        self._set_signing()

    def clear_phrases(self) -> None:
        self._phrases.clear()
        self._apply_empty_state()
        self._set_listening()

    def current_text(self) -> str:
        return " ".join(self._phrases)
