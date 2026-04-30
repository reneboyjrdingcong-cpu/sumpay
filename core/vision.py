"""VisionProcessor — MediaPipe Hand + Face Landmarker wrapper.

Called synchronously inside CameraWorker's loop. Falls back gracefully if
the .task model files are not yet present (returns empty landmark dicts).
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np

_mp_available = False
try:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_tasks
    from mediapipe.tasks.python import vision as mp_vision
    _mp_available = True
except ImportError:
    pass


def _hand_connections():
    if _mp_available:
        from mediapipe.tasks.python.vision.hand_landmarker import HandLandmarkerResult
    # MediaPipe standard hand connections (21 landmark pairs)
    return [
        (0, 1), (1, 2), (2, 3), (3, 4),
        (0, 5), (5, 6), (6, 7), (7, 8),
        (0, 9), (9, 10), (10, 11), (11, 12),
        (0, 13), (13, 14), (14, 15), (15, 16),
        (0, 17), (17, 18), (18, 19), (19, 20),
        (5, 9), (9, 13), (13, 17),
    ]


HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17),
]

# Key face indices to draw (eyes, brows, mouth corners, nose tip)
FACE_KEY_INDICES = [
    1, 4, 5, 6, 7, 8, 10, 13, 14, 17, 21, 33, 37, 39, 40, 46,
    52, 53, 54, 55, 58, 61, 63, 65, 66, 67, 70, 78, 80, 81, 82,
    84, 87, 88, 91, 93, 95, 103, 105, 107, 109, 127, 132, 133,
    136, 144, 145, 153, 154, 155, 157, 158, 159, 160, 161, 163,
    172, 173, 176, 178, 181, 185, 191, 234, 246, 249, 251, 263,
    267, 269, 270, 276, 282, 283, 284, 285, 288, 291, 293, 295,
    296, 297, 300, 308, 310, 311, 312, 314, 317, 318, 321, 323,
    324, 332, 334, 336, 338, 356, 361, 362, 365, 373, 374, 380,
    381, 382, 384, 385, 386, 387, 388, 390, 397, 398, 400, 402,
    405, 409, 415, 454, 466, 468, 469, 470, 471, 472, 473, 474,
]


class VisionProcessor:
    def __init__(self, hand_model_path: Path, face_model_path: Path) -> None:
        self._hand_landmarker = None
        self._face_landmarker = None
        self._start_ms: float = time.monotonic() * 1000.0

        if not _mp_available:
            print("[vision] mediapipe not installed — tracking disabled")
            return

        if hand_model_path.exists():
            try:
                h_opts = mp_vision.HandLandmarkerOptions(
                    base_options=mp_tasks.BaseOptions(
                        model_asset_path=str(hand_model_path)
                    ),
                    running_mode=mp_vision.RunningMode.VIDEO,
                    num_hands=2,
                    min_hand_detection_confidence=0.5,
                    min_hand_presence_confidence=0.5,
                    min_tracking_confidence=0.5,
                )
                self._hand_landmarker = mp_vision.HandLandmarker.create_from_options(h_opts)
            except Exception as exc:
                print(f"[vision] hand landmarker failed to load: {exc}")
        else:
            print(f"[vision] hand model missing: {hand_model_path}")

        if face_model_path.exists():
            try:
                f_opts = mp_vision.FaceLandmarkerOptions(
                    base_options=mp_tasks.BaseOptions(
                        model_asset_path=str(face_model_path)
                    ),
                    running_mode=mp_vision.RunningMode.VIDEO,
                    output_face_blendshapes=True,
                    num_faces=1,
                    min_face_detection_confidence=0.5,
                    min_face_presence_confidence=0.5,
                    min_tracking_confidence=0.5,
                )
                self._face_landmarker = mp_vision.FaceLandmarker.create_from_options(f_opts)
            except Exception as exc:
                print(f"[vision] face landmarker failed to load: {exc}")
        else:
            print(f"[vision] face model missing: {face_model_path}")

    def process(self, bgr_frame: np.ndarray) -> dict[str, Any]:
        """Return a landmarks dict and the frame annotated with overlay."""
        ts_ms = int(time.monotonic() * 1000.0 - self._start_ms)
        result: dict[str, Any] = {
            "hands": [],       # list of up to 2 lists of (x, y, z) tuples
            "blendshapes": [], # list of 52 float scores (empty if no face)
        }

        if not _mp_available:
            return result

        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        if self._hand_landmarker is not None:
            try:
                hr = self._hand_landmarker.detect_for_video(mp_image, ts_ms)
                for hand in (hr.hand_landmarks or []):
                    result["hands"].append([(lm.x, lm.y, lm.z) for lm in hand])
            except Exception:
                pass

        if self._face_landmarker is not None:
            try:
                fr = self._face_landmarker.detect_for_video(mp_image, ts_ms)
                if fr.face_blendshapes:
                    result["blendshapes"] = [c.score for c in fr.face_blendshapes[0]]
                result["face_landmarks"] = []
                if fr.face_landmarks:
                    result["face_landmarks"] = [(lm.x, lm.y, lm.z) for lm in fr.face_landmarks[0]]
            except Exception:
                pass

        return result

    def draw_overlay(self, bgr_frame: np.ndarray, landmarks: dict[str, Any]) -> np.ndarray:
        frame = bgr_frame.copy()
        h, w = frame.shape[:2]

        HAND_COLOR = (0, 229, 255)
        FACE_COLOR = (0, 171, 255)
        CONN_COLOR = (79, 195, 247)

        for hand in landmarks.get("hands", []):
            pts = [(int(lm[0] * w), int(lm[1] * h)) for lm in hand]
            for a, b in HAND_CONNECTIONS:
                if a < len(pts) and b < len(pts):
                    cv2.line(frame, pts[a], pts[b], CONN_COLOR, 2, cv2.LINE_AA)
            for pt in pts:
                cv2.circle(frame, pt, 5, HAND_COLOR, -1, cv2.LINE_AA)

        face_pts = landmarks.get("face_landmarks", [])
        for idx in FACE_KEY_INDICES:
            if idx < len(face_pts):
                x = int(face_pts[idx][0] * w)
                y = int(face_pts[idx][1] * h)
                cv2.circle(frame, (x, y), 2, FACE_COLOR, -1, cv2.LINE_AA)

        return frame

    def close(self) -> None:
        if self._hand_landmarker:
            self._hand_landmarker.close()
        if self._face_landmarker:
            self._face_landmarker.close()
