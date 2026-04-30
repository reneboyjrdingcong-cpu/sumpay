"""RecognizerWorker — continuous ASL sentence recognition engine.

Runs in its own QThread. Consumes landmark dicts emitted by CameraWorker,
builds a rolling feature buffer, and classifies on a fixed stride.

A dwell-time + confidence debounce prevents the same sentence from firing
multiple times during a single signing event.

Emits:
  recognized(str, float) — (sentence_text, confidence) when a phrase is detected
"""
from __future__ import annotations

import queue
from collections import deque

import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot

import config
from core.features import build_frame_vector, is_empty
from core.classifier import ASLClassifier


class RecognizerWorker(QThread):
    recognized: pyqtSignal = pyqtSignal(str, float)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._queue: queue.Queue = queue.Queue(maxsize=120)
        self._running = False

    def run(self) -> None:
        self._running = True
        classifier = ASLClassifier()

        if not classifier.ready:
            print("[recognizer] classifier not ready — recognition disabled")

        buffer: deque[np.ndarray] = deque(maxlen=config.WINDOW_LENGTH)
        frames_since_last = 0          # signing frames since last stride
        dwell_count = 0                # consecutive confident windows
        cooldown = 0                   # frames to wait before firing again
        last_label = ""
        empty_streak = 0              # consecutive frames with no hands

        while self._running:
            try:
                landmarks = self._queue.get(timeout=0.05)
            except queue.Empty:
                continue

            if not classifier.ready:
                continue

            if cooldown > 0:
                cooldown -= 1

            if is_empty(landmarks):
                empty_streak += 1
                if empty_streak == 30:  # ~1 s of no hands → wipe stale data
                    buffer.clear()
                    frames_since_last = 0
                    dwell_count = 0
                    last_label = ""
                continue  # never add empty frames to the buffer

            # Hands present — accumulate signing frames only
            empty_streak = 0
            vec = build_frame_vector(landmarks)
            buffer.append(vec)
            frames_since_last += 1

            if (
                len(buffer) == config.WINDOW_LENGTH
                and frames_since_last >= config.WINDOW_STRIDE
            ):
                frames_since_last = 0
                window = np.stack(list(buffer), axis=0)  # (T, F)
                label, conf = classifier.predict(window)

                print(f"[recognizer] pred={label!r}  conf={conf:.2f}  dwell={dwell_count}  cooldown={cooldown}")

                if conf >= config.CONFIDENCE_THRESHOLD and label:
                    if label == last_label:
                        dwell_count += 1
                    else:
                        dwell_count = 1
                        last_label = label

                    if dwell_count >= config.DWELL_FRAMES and cooldown == 0:
                        self.recognized.emit(label, conf)
                        cooldown = config.COOLDOWN_FRAMES
                        dwell_count = 0
                else:
                    dwell_count = 0
                    if conf < 0.4:
                        last_label = ""

    @pyqtSlot(object)
    def push_landmarks(self, landmarks: dict) -> None:
        try:
            self._queue.put_nowait(landmarks)
        except queue.Full:
            pass  # drop the oldest implicitly by ignoring

    def stop(self) -> None:
        self._running = False
