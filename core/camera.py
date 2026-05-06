"""CameraWorker — captures webcam frames, runs MediaPipe, emits results.

Runs in its own QThread so the GUI loop is never blocked.
Emits:
  frame_ready(np.ndarray)  — BGR frame with landmark overlay painted on it
  landmarks_ready(dict)    — raw landmark dict for the recognizer
  fps_updated(float)       — rolling FPS every 30 frames
"""
from __future__ import annotations

import time
from collections import deque

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

import config
from core.vision import VisionProcessor


class CameraWorker(QThread):
    frame_ready: pyqtSignal = pyqtSignal(object)
    landmarks_ready: pyqtSignal = pyqtSignal(object)
    fps_updated: pyqtSignal = pyqtSignal(float)

    def __init__(
        self,
        device_index: int = 0,
        width: int = 1280,
        height: int = 720,
        fps: int = 30,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._device_index = device_index
        self._width = width
        self._height = height
        self._target_fps = fps
        self._running = False
        self._vision = VisionProcessor(
            config.HAND_LANDMARKER_TASK,
            config.FACE_LANDMARKER_TASK,
        )

    def run(self) -> None:
        self._running = True
        cap = cv2.VideoCapture(self._device_index)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        cap.set(cv2.CAP_PROP_FPS, self._target_fps)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():
            print(f"[camera] could not open device {self._device_index}")
            return

        timestamps: deque[float] = deque(maxlen=30)

        while self._running:
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.01)
                continue

            t = time.monotonic()
            timestamps.append(t)

            landmarks = self._vision.process(frame)
            annotated = self._vision.draw_overlay(frame, landmarks)

            self.frame_ready.emit(annotated)
            self.landmarks_ready.emit(landmarks)

            if len(timestamps) == timestamps.maxlen:
                span = timestamps[-1] - timestamps[0]
                if span > 0:
                    self.fps_updated.emit((len(timestamps) - 1) / span)

        cap.release()
        self._vision.close()

    def stop(self) -> None:
        self._running = False
