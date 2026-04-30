"""Feature extraction from MediaPipe landmark dicts.

All functions are pure (no side effects) so they are straightforward to
unit-test without a camera or model.
"""
from __future__ import annotations

import numpy as np
import config


def normalize_hand(landmarks: list[tuple[float, float, float]]) -> np.ndarray:
    """Normalize a single hand's 21 landmarks to be wrist-relative and unit-scale.

    Returns a flat array of length 63 (21 points × x/y/z).

    Transformation:
    1. Translate so wrist (index 0) is the origin.
    2. Scale so the maximum absolute coordinate value is 1.0.
    """
    pts = np.array(landmarks, dtype=np.float32)  # (21, 3)
    pts -= pts[0]  # wrist to origin
    scale = np.max(np.abs(pts))
    if scale > 1e-6:
        pts /= scale
    return pts.flatten()  # (63,)


def build_frame_vector(landmarks: dict) -> np.ndarray:
    """Assemble a per-frame feature vector of length PER_FRAME_FEATURE_DIM.

    Layout: [hand_0 (63), hand_1 (63), blendshapes (52)] — zero-padded when a
    hand is absent or blendshapes unavailable.
    """
    vec = np.zeros(config.PER_FRAME_FEATURE_DIM, dtype=np.float32)

    hands = landmarks.get("hands", [])
    hand0 = normalize_hand(hands[0]) if len(hands) > 0 else np.zeros(63, dtype=np.float32)
    hand1 = normalize_hand(hands[1]) if len(hands) > 1 else np.zeros(63, dtype=np.float32)
    blendshapes = landmarks.get("blendshapes", [])
    bs = np.array(blendshapes[:config.FACE_BLENDSHAPES_DIM], dtype=np.float32)
    if bs.shape[0] < config.FACE_BLENDSHAPES_DIM:
        bs = np.pad(bs, (0, config.FACE_BLENDSHAPES_DIM - bs.shape[0]))

    vec[:63] = hand0
    vec[63:126] = hand1
    vec[126:] = bs
    return vec


def is_empty(landmarks: dict) -> bool:
    """True when no hand landmarks are present (patient is not signing)."""
    return len(landmarks.get("hands", [])) == 0
