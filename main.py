"""Project Sumpay — entry point.

Instantiates workers and wires Qt signals before showing the window.
Workers that depend on offline model files degrade gracefully if the
model file is missing (they emit a warning and stay idle).
"""
from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox

import config


def _check_assets() -> list[str]:
    """Return a list of missing critical asset paths (non-fatal warnings)."""
    warnings = []
    if not config.HAND_LANDMARKER_TASK.exists():
        warnings.append(f"Missing: {config.HAND_LANDMARKER_TASK}")
    if not config.FACE_LANDMARKER_TASK.exists():
        warnings.append(f"Missing: {config.FACE_LANDMARKER_TASK}")
    if not config.ASL_CLASSIFIER_PT.exists():
        warnings.append(f"Missing: {config.ASL_CLASSIFIER_PT}  (run training first)")
    if not config.VOSK_MODEL_DIR.exists():
        warnings.append(f"Missing: {config.VOSK_MODEL_DIR}")
    return warnings


def main() -> int:
    config.ensure_dirs()
    app = QApplication(sys.argv)
    app.setApplicationName("Project Sumpay")

    warnings = _check_assets()
    if warnings:
        msg = QMessageBox()
        msg.setWindowTitle("Project Sumpay — Asset check")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText(
            "Some offline assets are missing.\n"
            "The dashboard will open with those features disabled.\n\n"
            + "\n".join(warnings)
        )
        msg.exec()

    from gui.main_window import MainWindow
    window = MainWindow()

    # ------------------------------------------------------------------ #
    # Phase 1 workers: camera, recognizer (ASL + TTS)
    # ------------------------------------------------------------------ #
    try:
        from core.camera import CameraWorker
        camera = CameraWorker(
            device_index=config.CAMERA_INDEX,
            width=config.CAMERA_WIDTH,
            height=config.CAMERA_HEIGHT,
            fps=config.CAMERA_FPS,
        )
        camera.frame_ready.connect(window.on_frame)
        camera.fps_updated.connect(window.on_fps)
    except Exception as exc:
        print(f"[camera] failed to start: {exc}")
        camera = None

    try:
        from core.tts import TTSWorker
        tts_worker = TTSWorker()
        tts_worker.busy_changed.connect(window.on_tts_busy)
    except Exception as exc:
        print(f"[tts] failed to start: {exc}")
        tts_worker = None

    # Pass TTS worker to Connector — it will speak only after patient confirms.
    window.set_tts_worker(tts_worker)

    try:
        from core.recognizer import RecognizerWorker
        recognizer = RecognizerWorker()
        recognizer.recognized.connect(window.on_recognized)
        if camera:
            camera.landmarks_ready.connect(recognizer.push_landmarks)
    except Exception as exc:
        print(f"[recognizer] failed to start: {exc}")
        recognizer = None

    # ------------------------------------------------------------------ #
    # Phase 2 workers: STT + keyword router
    # ------------------------------------------------------------------ #
    try:
        from core.keyword_router import KeywordRouter
        router = KeywordRouter(config.KEYWORD_MAP, config.ASL_VIDEOS_DIR)
        router.play_video.connect(window.on_play_video)
    except Exception as exc:
        print(f"[router] failed to start: {exc}")
        router = None

    try:
        from core.stt import STTWorker
        stt = STTWorker(
            model_dir=str(config.VOSK_MODEL_DIR),
            sample_rate=config.MIC_SAMPLE_RATE,
            block_size=config.MIC_BLOCK_SIZE,
        )
        stt.partial_transcript.connect(window.on_partial_transcript)
        stt.final_transcript.connect(window.on_final_transcript)
        stt.mic_level.connect(window.on_mic_level)
        if router:
            stt.final_transcript.connect(router.match)
    except Exception as exc:
        print(f"[stt] failed to start: {exc}")
        stt = None

    # ------------------------------------------------------------------ #
    # Start threads and show window
    # ------------------------------------------------------------------ #
    for worker in (camera, tts_worker, recognizer, stt):
        if worker is not None:
            worker.start()

    window.showMaximized()
    result = app.exec()

    for worker in (camera, recognizer, tts_worker, stt):
        if worker is not None:
            worker.stop()
            worker.wait()

    return result


if __name__ == "__main__":
    sys.exit(main())
