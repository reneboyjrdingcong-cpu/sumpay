"""PyTorch Dataset for recorded ASL landmark sequences."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional, Callable

import numpy as np
import torch
from torch.utils.data import Dataset

import config


class ASLDataset(Dataset):
    """Loads .npy files from data/recordings/<label_id>/<sample_id>.npy.

    Each .npy file is a float32 array of shape (T, PER_FRAME_FEATURE_DIM)
    where T may vary across samples.  __getitem__ pads or trims to WINDOW_LENGTH.
    """

    def __init__(
        self,
        recordings_dir: Path = config.RECORDINGS_DIR,
        label_map_path: Path = config.LABEL_MAP_JSON,
        augment: Optional[Callable] = None,
    ) -> None:
        self.augment = augment
        self.samples: list[tuple[Path, int]] = []

        if not label_map_path.exists():
            raise FileNotFoundError(f"label_map.json not found: {label_map_path}")
        with open(label_map_path) as f:
            self.label_map: dict[str, str] = json.load(f)  # {str_idx: phrase}
        self.idx_to_label = {int(k): v for k, v in self.label_map.items()}
        self.num_classes = len(self.label_map)

        for label_id_str in sorted(os.listdir(recordings_dir)):
            label_dir = recordings_dir / label_id_str
            if not label_dir.is_dir():
                continue
            try:
                label_id = int(label_id_str)
            except ValueError:
                continue
            for npy_file in sorted(label_dir.glob("*.npy")):
                self.samples.append((npy_file, label_id))

        if not self.samples:
            raise RuntimeError(
                f"No samples found in {recordings_dir}. "
                "Run training/record_phrase.py first."
            )

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
        path, label_id = self.samples[idx]
        seq = np.load(str(path)).astype(np.float32)  # (T, F)

        # Drop frames with no hands detected — matches recognizer.py which
        # never appends empty frames to its buffer. Without this, training
        # windows contain rest-pose zeros that never appear at inference.
        hand_present = np.any(seq[:, :126] != 0.0, axis=1)
        if hand_present.any():
            seq = seq[hand_present]

        if self.augment is not None:
            seq = self.augment(seq)

        T = seq.shape[0]
        W = config.WINDOW_LENGTH
        if T >= W:
            start = np.random.randint(0, T - W + 1) if T > W else 0
            seq = seq[start: start + W]
        else:
            pad = np.zeros((W - T, seq.shape[1]), dtype=np.float32)
            seq = np.concatenate([seq, pad], axis=0)

        return torch.from_numpy(seq), label_id
