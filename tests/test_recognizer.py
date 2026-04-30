"""Tests for the recognizer's debounce state machine logic.

We test the logic in isolation without starting a QThread.
"""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import numpy as np
import config


def _make_confident_window() -> np.ndarray:
    return np.zeros((config.WINDOW_LENGTH, config.PER_FRAME_FEATURE_DIM), dtype=np.float32)


class FakeClassifier:
    """Returns a fixed label + confidence every call."""
    def __init__(self, label: str = "test phrase", conf: float = 0.95):
        self.label = label
        self.conf = conf
        self.call_count = 0

    @property
    def ready(self):
        return True

    def predict(self, window):
        self.call_count += 1
        return self.label, self.conf


def _run_debounce(
    classifier,
    num_landmark_pushes: int = 200,
    dwell: int = config.DWELL_FRAMES,
    cooldown: int = config.COOLDOWN_FRAMES,
    stride: int = config.WINDOW_STRIDE,
    window_len: int = config.WINDOW_LENGTH,
) -> list[tuple[str, float]]:
    """Pure simulation of the recognizer state machine."""
    from collections import deque
    from core.features import build_frame_vector, is_empty

    buffer = deque(maxlen=window_len)
    frames_since_last = 0
    dwell_count = 0
    cooldown_count = 0
    last_label = ""
    emissions: list[tuple[str, float]] = []

    # Simulate non-empty landmarks
    fake_lm = {"hands": [[(float(i), float(i), 0.0) for i in range(21)]]}

    for _ in range(num_landmark_pushes):
        vec = build_frame_vector(fake_lm)
        buffer.append(vec)
        frames_since_last += 1
        if cooldown_count > 0:
            cooldown_count -= 1

        if len(buffer) == window_len and frames_since_last >= stride:
            frames_since_last = 0
            window = np.stack(list(buffer), axis=0)
            label, conf = classifier.predict(window)
            if conf >= config.CONFIDENCE_THRESHOLD and label:
                if label == last_label:
                    dwell_count += 1
                else:
                    dwell_count = 1
                    last_label = label
                if dwell_count >= dwell and cooldown_count == 0:
                    emissions.append((label, conf))
                    cooldown_count = cooldown
                    dwell_count = 0
            else:
                dwell_count = 0
                if conf < 0.4:
                    last_label = ""

    return emissions


def test_single_phrase_fires_once_in_cooldown_window():
    clf = FakeClassifier("yes", 0.99)
    emissions = _run_debounce(clf, num_landmark_pushes=200)
    assert len(emissions) >= 1, "expected at least one emission"
    # Should not fire more than ceiling(200 / (DWELL_FRAMES*STRIDE + COOLDOWN_FRAMES)) times
    max_expected = 200 // (config.DWELL_FRAMES * config.WINDOW_STRIDE + config.COOLDOWN_FRAMES) + 1
    assert len(emissions) <= max_expected, f"too many emissions: {len(emissions)} > {max_expected}"


def test_low_confidence_never_fires():
    clf = FakeClassifier("yes", 0.50)  # below 0.80 threshold
    emissions = _run_debounce(clf, num_landmark_pushes=300)
    assert emissions == [], "low-confidence classifier should never fire"


def test_label_change_resets_dwell():
    """If the predicted label flips mid-sequence the dwell counter resets."""

    class AlternatingClassifier:
        def __init__(self):
            self.call_count = 0

        @property
        def ready(self):
            return True

        def predict(self, _):
            self.call_count += 1
            # Alternate between two labels every call
            label = "yes" if self.call_count % 2 == 0 else "no"
            return label, 0.95

    clf = AlternatingClassifier()
    emissions = _run_debounce(clf, num_landmark_pushes=400)
    # Alternating labels means dwell never reaches DWELL_FRAMES in a row
    assert len(emissions) == 0, "alternating labels should never accumulate enough dwell"
