"""Evaluate the trained ASL model on a held-out split.

Usage:
    python -m training.eval
"""
from __future__ import annotations

import json
import sys

import numpy as np
import torch
from torch.utils.data import DataLoader, random_split

import config
from training.dataset import ASLDataset


def main() -> None:
    if not config.ASL_CLASSIFIER_PT.exists():
        print(f"[eval] No trained model at {config.ASL_CLASSIFIER_PT}. Run training/train.py first.")
        sys.exit(1)

    dataset = ASLDataset(augment=None)
    n_val = max(1, int(len(dataset) * 0.2))
    n_train = len(dataset) - n_val
    _, val_set = random_split(dataset, [n_train, n_val])
    loader = DataLoader(val_set, batch_size=32, shuffle=False, num_workers=0)

    model = torch.jit.load(str(config.ASL_CLASSIFIER_PT))
    model.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    num_classes = dataset.num_classes
    confusion = np.zeros((num_classes, num_classes), dtype=int)

    with torch.no_grad():
        for x, y in loader:
            preds = model(x.to(device)).argmax(dim=1).cpu().numpy()
            for pred, true in zip(preds, y.numpy()):
                confusion[true][pred] += 1

    acc = np.trace(confusion) / max(confusion.sum(), 1)
    print(f"\n[eval] Accuracy: {acc:.3f}  ({np.trace(confusion)}/{confusion.sum()} correct)\n")
    print("Per-class accuracy:")
    for i, phrase in dataset.idx_to_label.items():
        row = confusion[i]
        n = row.sum()
        correct = row[i]
        pct = correct / max(n, 1) * 100
        print(f"  [{i:2d}] {phrase[:55]:55s}  {correct:3d}/{n:3d}  ({pct:.0f}%)")


if __name__ == "__main__":
    main()
