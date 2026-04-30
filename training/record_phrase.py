"""CLI tool: record landmark sequences for a single ASL phrase.

Usage:
    python -m training.record_phrase \
        --phrase "I have a headache for a week now" \
        --samples 30

The phrase must be in config.INITIAL_PHRASES or be provided with --phrase.
Recorded sequences are saved to data/recordings/<label_id>/<sample_id>.npy.
label_map.json is created/updated in models/.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

import config

config.ensure_dirs()


def _get_or_create_label_id(phrase: str) -> int:
    label_map: dict[str, str] = {}
    if config.LABEL_MAP_JSON.exists():
        with open(config.LABEL_MAP_JSON) as f:
            label_map = json.load(f)

    for k, v in label_map.items():
        if v == phrase:
            return int(k)

    new_id = max((int(k) for k in label_map), default=-1) + 1
    label_map[str(new_id)] = phrase
    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.LABEL_MAP_JSON, "w") as f:
        json.dump(label_map, f, indent=2)
    print(f"[record] Assigned label ID {new_id} to: {phrase!r}")
    return new_id


def record(phrase: str, num_samples: int) -> None:
    try:
        from core.vision import VisionProcessor
        from core.features import build_frame_vector
    except ImportError as e:
        print(f"Import error: {e}. Run from the project root.")
        sys.exit(1)

    label_id = _get_or_create_label_id(phrase)
    out_dir = config.RECORDINGS_DIR / str(label_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    existing = sorted(out_dir.glob("*.npy"))
    start_idx = len(existing)

    vision = VisionProcessor(config.HAND_LANDMARKER_TASK, config.FACE_LANDMARKER_TASK)
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    if not cap.isOpened():
        print("[record] Cannot open camera.")
        sys.exit(1)

    print(f"\n[record] Phrase: {phrase!r}")
    print(f"[record] Collecting {num_samples} samples (labels saved to {out_dir})")
    print("[record] Press SPACE to start recording a sample. Press Q to quit.\n")

    collected = 0
    while collected < num_samples:
        ok, frame = cap.read()
        if not ok:
            continue

        landmarks = vision.process(frame)
        annotated = vision.draw_overlay(frame, landmarks)

        overlay = annotated.copy()
        cv2.putText(
            overlay,
            f"Sample {collected + 1}/{num_samples}  |  Press SPACE to record",
            (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 229, 255), 2,
        )
        cv2.putText(
            overlay, f"Phrase: {phrase}", (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1,
        )
        cv2.imshow("Sumpay — Record Phrase", overlay)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord(" "):
            # Record a 3-second clip
            print(f"  Recording sample {collected + 1}... ", end="", flush=True)
            frames: list[np.ndarray] = []
            start = time.monotonic()
            while time.monotonic() - start < 3.0:
                ok, fr = cap.read()
                if not ok:
                    continue
                lm = vision.process(fr)
                vec = build_frame_vector(lm)
                frames.append(vec)
                ann = vision.draw_overlay(fr, lm)
                cv2.putText(
                    ann,
                    f"RECORDING  {time.monotonic() - start:.1f}s / 3.0s",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2,
                )
                cv2.imshow("Sumpay — Record Phrase", ann)
                cv2.waitKey(1)

            if frames:
                seq = np.stack(frames, axis=0).astype(np.float32)
                npy_path = out_dir / f"{start_idx + collected:04d}.npy"
                np.save(str(npy_path), seq)
                print(f"saved ({len(frames)} frames) -> {npy_path}")
                collected += 1
            else:
                print("no frames captured, try again")

    cap.release()
    vision.close()
    cv2.destroyAllWindows()
    print(f"\n[record] Done. {collected} samples saved for label {label_id}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Record ASL phrase landmark sequences.")
    parser.add_argument("--phrase", required=True, help="The English phrase to sign.")
    parser.add_argument("--samples", type=int, default=30, help="Number of samples to record.")
    args = parser.parse_args()
    record(args.phrase, args.samples)


if __name__ == "__main__":
    main()
