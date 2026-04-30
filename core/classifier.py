"""ASL classifier inference wrapper.

Loads the TorchScript model and exposes a predict() method for the recognizer.
Falls back gracefully when the model file is absent (returns None predictions).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np
import torch

import config


class ASLClassifier:
    def __init__(
        self,
        model_path: Path = config.ASL_CLASSIFIER_PT,
        label_map_path: Path = config.LABEL_MAP_JSON,
    ) -> None:
        self._model: Optional[torch.jit.ScriptModule] = None
        self._label_map: dict[int, str] = {}
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        if label_map_path.exists():
            with open(label_map_path) as f:
                raw = json.load(f)
            self._label_map = {int(k): v for k, v in raw.items()}

        if model_path.exists():
            try:
                self._model = torch.jit.load(str(model_path), map_location=self._device)
                self._model.eval()
            except Exception as exc:
                print(f"[classifier] failed to load model: {exc}")

    @property
    def ready(self) -> bool:
        return self._model is not None and bool(self._label_map)

    def predict(self, window: np.ndarray) -> tuple[str, float]:
        """Classify a landmark feature window.

        Args:
            window: float32 array of shape (WINDOW_LENGTH, PER_FRAME_FEATURE_DIM)

        Returns:
            (label_text, confidence) or ("", 0.0) if the model is not loaded.
        """
        if not self.ready:
            return "", 0.0

        x = torch.from_numpy(window).unsqueeze(0).to(self._device)  # (1, T, F)
        with torch.no_grad():
            logits = self._model(x)  # (1, num_classes)
            probs = torch.softmax(logits, dim=1)[0]
            idx = int(probs.argmax().item())
            conf = float(probs[idx].item())

        label = self._label_map.get(idx, "")
        return label, conf
