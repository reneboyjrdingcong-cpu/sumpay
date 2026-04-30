"""Unit tests for core/features.py.

These run without a webcam or model — only numpy arithmetic.
"""
import numpy as np
import pytest
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from core.features import normalize_hand, build_frame_vector, is_empty
import config


# ---------------------------------------------------------------------- #
# normalize_hand
# ---------------------------------------------------------------------- #

def _random_hand(seed: int = 0) -> list[tuple[float, float, float]]:
    rng = np.random.default_rng(seed)
    pts = rng.uniform(0.1, 0.9, size=(21, 3))
    return [tuple(p) for p in pts]


def test_normalize_hand_wrist_at_origin():
    hand = _random_hand()
    vec = normalize_hand(hand)
    pts = vec.reshape(21, 3)
    np.testing.assert_allclose(pts[0], [0, 0, 0], atol=1e-6)


def test_normalize_hand_max_abs_one():
    hand = _random_hand(seed=42)
    vec = normalize_hand(hand)
    assert np.max(np.abs(vec)) == pytest.approx(1.0, abs=1e-5)


def test_normalize_hand_translation_invariant():
    """Shifting all landmarks by a constant should not change the output."""
    hand = _random_hand(seed=7)
    shifted = [(x + 0.3, y - 0.2, z + 0.1) for (x, y, z) in hand]
    vec1 = normalize_hand(hand)
    vec2 = normalize_hand(shifted)
    np.testing.assert_allclose(vec1, vec2, atol=1e-5)


def test_normalize_hand_all_zeros_no_nan():
    """Zero input should produce a zero vector, not NaN."""
    hand = [(0.0, 0.0, 0.0)] * 21
    vec = normalize_hand(hand)
    assert not np.any(np.isnan(vec))


# ---------------------------------------------------------------------- #
# build_frame_vector
# ---------------------------------------------------------------------- #

def test_build_frame_vector_shape():
    landmarks = {"hands": [_random_hand()], "blendshapes": [0.1] * 52}
    vec = build_frame_vector(landmarks)
    assert vec.shape == (config.PER_FRAME_FEATURE_DIM,)


def test_build_frame_vector_no_hands_zero_padded():
    landmarks = {"hands": [], "blendshapes": []}
    vec = build_frame_vector(landmarks)
    assert vec.shape == (config.PER_FRAME_FEATURE_DIM,)
    np.testing.assert_array_equal(vec[:126], 0)


def test_build_frame_vector_partial_blendshapes_padded():
    landmarks = {"hands": [], "blendshapes": [0.5] * 10}
    vec = build_frame_vector(landmarks)
    assert vec[126:136].sum() == pytest.approx(5.0, abs=1e-5)
    assert vec[136:].sum() == pytest.approx(0.0, abs=1e-5)


def test_build_frame_vector_dtype():
    landmarks = {"hands": [], "blendshapes": []}
    vec = build_frame_vector(landmarks)
    assert vec.dtype == np.float32


# ---------------------------------------------------------------------- #
# is_empty
# ---------------------------------------------------------------------- #

def test_is_empty_true_when_no_hands():
    assert is_empty({"hands": [], "blendshapes": []}) is True
    assert is_empty({}) is True


def test_is_empty_false_when_hand_present():
    assert is_empty({"hands": [_random_hand()]}) is False
