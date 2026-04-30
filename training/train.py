"""Train the ASL Transformer classifier and export as TorchScript.

Usage:
    python -m training.train [--epochs 60] [--lr 3e-4] [--batch 32]

Outputs:
    models/asl_classifier.pt  — TorchScript model
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split

import config
from training.dataset import ASLDataset
from training.augment import apply_train_augmentations


# ---------------------------------------------------------------------- #
# Model definition
# ---------------------------------------------------------------------- #

class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 512) -> None:
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        pos = torch.arange(0, max_len).unsqueeze(1).float()
        div = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(pos * div)
        pe[:, 1::2] = torch.cos(pos * div)
        self.register_buffer("pe", pe.unsqueeze(0))  # (1, max_len, d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, : x.size(1)]


class ASLTransformer(nn.Module):
    """Small Transformer encoder + mean-pool classifier."""

    def __init__(
        self,
        input_dim: int,
        num_classes: int,
        d_model: int = config.D_MODEL,
        n_heads: int = config.N_HEADS,
        n_layers: int = config.N_LAYERS,
        dropout: float = config.DROPOUT,
    ) -> None:
        super().__init__()
        self.input_proj = nn.Linear(input_dim, d_model)
        self.pos_enc = PositionalEncoding(d_model)
        enc_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            batch_first=True,
        )
        self.encoder = nn.TransformerEncoder(enc_layer, num_layers=n_layers)
        self.dropout = nn.Dropout(dropout)
        self.head = nn.Linear(d_model, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, T, F)
        x = self.input_proj(x)
        x = self.pos_enc(x)
        x = self.encoder(x)
        x = x.mean(dim=1)  # mean pool over time
        x = self.dropout(x)
        return self.head(x)  # (B, num_classes)


# ---------------------------------------------------------------------- #
# Training loop
# ---------------------------------------------------------------------- #

def train(epochs: int, lr: float, batch_size: int) -> None:
    config.ensure_dirs()

    dataset = ASLDataset(augment=apply_train_augmentations)
    n_val = max(1, int(len(dataset) * config.TRAIN_VAL_SPLIT))
    n_train = len(dataset) - n_val
    train_set, val_set = random_split(dataset, [n_train, n_val])
    # Val set should not be augmented — re-wrap without augment
    val_set.dataset.augment = None  # type: ignore[attr-defined]

    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_set, batch_size=batch_size, shuffle=False, num_workers=0)

    num_classes = dataset.num_classes
    model = ASLTransformer(
        input_dim=config.PER_FRAME_FEATURE_DIM,
        num_classes=num_classes,
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    print(f"[train] Device: {device}  |  Classes: {num_classes}  |  Train: {n_train}  |  Val: {n_val}")

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    criterion = nn.CrossEntropyLoss()

    best_val_acc = 0.0
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.clone().detach().to(device)
            optimizer.zero_grad()
            loss = criterion(model(x), y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += loss.item() * len(x)
        scheduler.step()
        avg_loss = total_loss / n_train

        model.eval()
        correct = total = 0
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.clone().detach().to(device)
                preds = model(x).argmax(dim=1)
                correct += (preds == y).sum().item()
                total += len(y)
        val_acc = correct / max(total, 1)

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            _export(model, num_classes, device)

        if epoch % 5 == 0 or epoch == epochs:
            print(f"  Epoch {epoch:3d}/{epochs}  loss={avg_loss:.4f}  val_acc={val_acc:.3f}  best={best_val_acc:.3f}")

    print(f"[train] Done. Best val accuracy: {best_val_acc:.3f}")
    print(f"[train] Exported to: {config.ASL_CLASSIFIER_PT}")


def _export(model: nn.Module, num_classes: int, device: torch.device) -> None:
    model.eval()
    dummy = torch.zeros(1, config.WINDOW_LENGTH, config.PER_FRAME_FEATURE_DIM, device=device)
    scripted = torch.jit.trace(model, dummy, check_trace=False)
    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    torch.jit.save(scripted, str(config.ASL_CLASSIFIER_PT))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=config.TRAIN_EPOCHS)
    parser.add_argument("--lr", type=float, default=config.TRAIN_LR)
    parser.add_argument("--batch", type=int, default=config.TRAIN_BATCH_SIZE)
    args = parser.parse_args()
    train(args.epochs, args.lr, args.batch)


if __name__ == "__main__":
    main()
