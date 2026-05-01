"""Connector — QStackedWidget state machine managing all 9 screens.

Screen indices:
    0 — SplashScreen          (patient/doctor landing)
    1 — RoleScreen            (choose patient or doctor)
    2 — CameraScreen          (patient: live ASL capture)
    3 — ConfirmScreen         (patient: review translated text)
    4 — AudioScreen           (patient: TTS playback)
    5 — DoctorChoiceScreen    (doctor: record vs type)
    6 — DoctorRecordScreen    (doctor: live waveform + stop)
    7 — DoctorConfirmScreen   (doctor: review/edit text)
    8 — DoctorPlaybackScreen  (doctor: ASL video playback)
"""
from __future__ import annotations

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QStackedWidget

from gui.screens.splash_screen        import SplashScreen
from gui.screens.role_screen          import RoleScreen
from gui.screens.camera_screen        import CameraScreen
from gui.screens.confirm_screen       import ConfirmScreen
from gui.screens.audio_screen         import AudioScreen
from gui.screens.doctor_choice_screen import DoctorChoiceScreen
from gui.screens.doctor_record_screen import DoctorRecordScreen
from gui.screens.doctor_confirm_screen import DoctorConfirmScreen
from gui.screens.doctor_playback_screen import DoctorPlaybackScreen


_SPLASH          = 0
_ROLE            = 1
_CAMERA          = 2
_CONFIRM         = 3
_AUDIO           = 4
_DOC_CHOICE      = 5
_DOC_RECORD      = 6
_DOC_CONFIRM     = 7
_DOC_PLAYBACK    = 8


class Connector(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Patient-flow state
        self._accumulated: list[str] = []
        self._tts_worker = None

        # Doctor-flow state
        self._doctor_recording = False
        self._router = None

        # ── Screen instances ─────────────────────────────────────────────── #
        self._splash        = SplashScreen()
        self._role          = RoleScreen()
        self._camera        = CameraScreen()
        self._confirm       = ConfirmScreen()
        self._audio         = AudioScreen()
        self._doc_choice    = DoctorChoiceScreen()
        self._doc_record    = DoctorRecordScreen()
        self._doc_confirm   = DoctorConfirmScreen()
        self._doc_playback  = DoctorPlaybackScreen()

        for screen in (
            self._splash, self._role, self._camera, self._confirm, self._audio,
            self._doc_choice, self._doc_record, self._doc_confirm, self._doc_playback,
        ):
            self.addWidget(screen)

        # ── Signal wiring ────────────────────────────────────────────────── #

        # Splash → Role
        self._splash.advance.connect(self._go_role)

        # Role → patient or doctor flow
        self._role.role_selected.connect(self._on_role_selected)

        # Patient flow (unchanged behaviour)
        self._camera.continue_clicked.connect(self._go_patient_confirm)
        self._confirm.confirmed.connect(self._go_audio)
        self._confirm.retry.connect(self._go_camera_retry)
        self._audio.done.connect(self._go_splash)

        # Doctor flow — forward
        self._doc_choice.record_clicked.connect(self._go_doc_record)
        self._doc_choice.type_clicked.connect(self._go_doc_type)
        self._doc_record.recording_stopped.connect(self._go_doc_confirm_with_text)
        self._doc_confirm.confirmed.connect(self._on_doc_confirmed)
        self._doc_confirm.retry.connect(self._go_doc_choice)
        self._doc_playback.done.connect(self._go_splash)

        # Doctor flow — back navigation
        self._doc_choice.back.connect(self._go_role)
        self._doc_record.back.connect(self._go_doc_choice)
        self._doc_confirm.back.connect(self._go_doc_choice)
        self._doc_playback.back.connect(self._go_doc_confirm_back)

        self.setCurrentIndex(_SPLASH)

    # ================================================================== #
    # Public API (called by MainWindow / main.py)
    # ================================================================== #

    def set_tts_worker(self, tts_worker) -> None:
        self._tts_worker = tts_worker
        if tts_worker is not None:
            tts_worker.busy_changed.connect(self._audio.on_busy)

    def set_router(self, router) -> None:
        self._router = router
        if router is not None:
            router.play_video.connect(self.on_play_video)

    # ── Patient slots ────────────────────────────────────────────────── #

    @pyqtSlot(object)
    def on_frame(self, frame) -> None:
        self._camera.update_frame(frame)

    @pyqtSlot(str, float)
    def on_recognized(self, sentence: str, confidence: float) -> None:
        self._accumulated.append(sentence)
        self._camera.append_phrase(sentence)

    @pyqtSlot(bool)
    def on_tts_busy(self, busy: bool) -> None:
        self._audio.on_busy(busy)

    # ── Doctor / STT slots (gated by _doctor_recording) ─────────────── #

    @pyqtSlot(str)
    def on_partial_transcript(self, text: str) -> None:
        if self._doctor_recording:
            self._doc_record.on_partial(text)

    @pyqtSlot(str)
    def on_final_transcript(self, text: str) -> None:
        if self._doctor_recording:
            self._doc_record.on_final(text)

    @pyqtSlot(float)
    def on_mic_level(self, level: float) -> None:
        if self._doctor_recording:
            self._doc_record.on_mic_level(level)

    @pyqtSlot(str)
    def on_play_video(self, path: str) -> None:
        self._doc_playback.play_video(path)

    # ================================================================== #
    # Transitions
    # ================================================================== #

    def _go_splash(self) -> None:
        self._accumulated.clear()
        self._camera.clear_phrases()
        self._doctor_recording = False
        self._doc_playback.reset()
        self.setCurrentIndex(_SPLASH)

    def _go_role(self) -> None:
        self.setCurrentIndex(_ROLE)

    @pyqtSlot(str)
    def _on_role_selected(self, role: str) -> None:
        if role == "patient":
            self._accumulated.clear()
            self._camera.clear_phrases()
            self.setCurrentIndex(_CAMERA)
        else:
            self.setCurrentIndex(_DOC_CHOICE)

    # Patient transitions
    def _go_patient_confirm(self) -> None:
        text = self._camera.current_text()
        self._confirm.set_text(text)
        self.setCurrentIndex(_CONFIRM)

    @pyqtSlot(str)
    def _go_audio(self, text: str) -> None:
        self._audio.reset()
        self.setCurrentIndex(_AUDIO)
        if self._tts_worker and text:
            self._tts_worker.speak(text)
        else:
            self._audio.on_busy(False)

    def _go_camera_retry(self) -> None:
        self._accumulated.clear()
        self._camera.clear_phrases()
        self.setCurrentIndex(_CAMERA)

    # Doctor transitions
    def _go_doc_record(self) -> None:
        self._doctor_recording = True
        self._doc_record.reset()
        self.setCurrentIndex(_DOC_RECORD)

    def _go_doc_type(self) -> None:
        self._doctor_recording = False
        self._doc_confirm.set_text("", editable=True)
        self.setCurrentIndex(_DOC_CONFIRM)

    @pyqtSlot(str)
    def _go_doc_confirm_with_text(self, text: str) -> None:
        self._doctor_recording = False
        self._doc_confirm.set_text(text, editable=True)
        self.setCurrentIndex(_DOC_CONFIRM)

    def _go_doc_choice(self) -> None:
        self._doctor_recording = False
        # Ensure waveform timer is stopped if we back out mid-recording
        self._doc_record._cleanup()
        self.setCurrentIndex(_DOC_CHOICE)

    def _go_doc_confirm_back(self) -> None:
        """Back from playback — return to the confirm screen so the doctor
        can re-read or re-confirm without losing their text."""
        self.setCurrentIndex(_DOC_CONFIRM)

    @pyqtSlot(str)
    def _on_doc_confirmed(self, text: str) -> None:
        self._doc_playback.set_text(text)
        self.setCurrentIndex(_DOC_PLAYBACK)
        if self._router:
            self._router.match(text)
        else:
            # No router — mark playback as immediately clickable
            self._doc_playback.reset()
            self._doc_playback._finished = True
