"""Data augmentations for ASL landmark sequences.

All transforms operate on numpy arrays of shape (T, F) where T = number of
frames and F = feature dimension.  They are designed to be composed and
applied randomly during training.
"""
from __future__ import annotations

import numpy as np


def time_warp(seq: np.ndarray, sigma: float = 0.1) -> np.ndarray:
    """Randomly stretch/compress the time axis via piecewise linear interpolation."""
    T, F = seq.shape
    orig_steps = np.arange(T, dtype=np.float32)
    # Add random perturbations to interior knots
    knots = np.sort(
        np.concatenate([[0], np.random.uniform(0, T, 4), [T - 1]])
    )
    warped_knots = knots + np.random.uniform(-sigma * T, sigma * T, len(knots))
    warped_knots = np.clip(warped_knots, 0, T - 1)
    warped_knots[0] = 0
    warped_knots[-1] = T - 1
    new_steps = np.interp(orig_steps, np.linspace(0, T - 1, len(knots)), warped_knots)
    new_steps = np.clip(new_steps, 0, T - 1)
    warped = np.stack(
        [np.interp(new_steps, orig_steps, seq[:, f]) for f in range(F)], axis=1
    )
    return warped.astype(np.float32)


def jitter(seq: np.ndarray, sigma: float = 0.02) -> np.ndarray:
    """Add Gaussian noise to each frame."""
    return seq + np.random.normal(0, sigma, seq.shape).astype(np.float32)


def dropout_frames(seq: np.ndarray, p: float = 0.05) -> np.ndarray:
    """Zero out random frames to simulate missed detections."""
    mask = np.random.random(seq.shape[0]) > p
    out = seq.copy()
    out[~mask] = 0.0
    return out


def mirror_hands(seq: np.ndarray) -> np.ndarray:
    """Flip hand x-coordinates so a right-handed signer looks left-handed.

    Assumes layout: [hand0 (63), hand1 (63), blendshapes (52)].
    Mirrors x of each hand by negating every 3rd element starting at index 0.
    """
    out = seq.copy()
    for start in (0, 63):
        out[:, start::3] = -out[:, start::3]  # negate x components
    return out


def apply_train_augmentations(seq: np.ndarray) -> np.ndarray:
    if np.random.random() < 0.7:
        seq = time_warp(seq)
    if np.random.random() < 0.8:
        seq = jitter(seq)
    if np.random.random() < 0.5:
        seq = dropout_frames(seq)
    if np.random.random() < 0.5:
        seq = mirror_hands(seq)
    return seq
