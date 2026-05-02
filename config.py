"""Project Sumpay - global configuration.

All paths, hyperparameters, and clinician-curated tables live here so non-engineers
can edit the keyword map and phrase list without touching application code.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR: Path = Path(__file__).resolve().parent

ASSETS_DIR: Path = ROOT_DIR / "assets"
MODELS_DIR: Path = ROOT_DIR / "models"
DATA_DIR: Path = ROOT_DIR / "data"
RECORDINGS_DIR: Path = DATA_DIR / "recordings"

MEDIAPIPE_DIR: Path = ASSETS_DIR / "mediapipe"
HAND_LANDMARKER_TASK: Path = MEDIAPIPE_DIR / "hand_landmarker.task"
FACE_LANDMARKER_TASK: Path = MEDIAPIPE_DIR / "face_landmarker.task"

VOSK_MODEL_DIR: Path = ASSETS_DIR / "vosk" / "vosk-model-small-en-us-0.15"

ASL_VIDEOS_DIR: Path = ASSETS_DIR / "asl_videos"

ASL_CLASSIFIER_PT: Path = MODELS_DIR / "asl_classifier.pt"
LABEL_MAP_JSON: Path = MODELS_DIR / "label_map.json"

STYLES_QSS: Path = ASSETS_DIR / "styles.qss"

CAMERA_INDEX: int = 0
CAMERA_WIDTH: int = 1280
CAMERA_HEIGHT: int = 720
CAMERA_FPS: int = 30

WINDOW_LENGTH: int = 60
WINDOW_STRIDE: int = 10
NUM_HAND_LANDMARKS: int = 21
NUM_FACE_LANDMARKS: int = 478
HAND_FEATURE_DIM: int = NUM_HAND_LANDMARKS * 3 * 2
FACE_BLENDSHAPES_DIM: int = 52
PER_FRAME_FEATURE_DIM: int = HAND_FEATURE_DIM + FACE_BLENDSHAPES_DIM

CONFIDENCE_THRESHOLD: float = 0.60
DWELL_FRAMES: int = 3
COOLDOWN_FRAMES: int = 45

D_MODEL: int = 128
N_HEADS: int = 4
N_LAYERS: int = 3
DROPOUT: float = 0.2

TRAIN_BATCH_SIZE: int = 32
TRAIN_EPOCHS: int = 60
TRAIN_LR: float = 3e-4
TRAIN_VAL_SPLIT: float = 0.15

MIC_SAMPLE_RATE: int = 16000
MIC_BLOCK_SIZE: int = 4000

KEYWORD_MAP: dict[str, str] = {
    "take your medicine": "take_medicine.mp4",
    "take medicine": "take_medicine.mp4",
    "rest": "rest.mp4",
    "lie down": "rest.mp4",
    "breathe deeply": "breathe_deeply.mp4",
    "deep breath": "breathe_deeply.mp4",
    "drink water": "drink_water.mp4",
    "follow up": "follow_up.mp4",
    "everything is okay": "okay.mp4",
    "you are okay": "okay.mp4",
    "unusual odor": "unusual_odor_discharge.mp4",
    "odor or discharge": "unusual_odor_discharge.mp4",
    "noticed a discharge": "unusual_odor_discharge.mp4",
    "pain reliever": "pain_reliever_daily.mp4",
    "pain reliever once a day": "pain_reliever_daily.mp4",
    "take this pain reliever": "pain_reliever_daily.mp4",
}

INITIAL_PHRASES: list[str] = [
    "I have a headache",
    "for a week now",
    "Can you check",
    "my eye",
    "I feel dizzy",
    "I have chest pain",
    "I cannot sleep at night",
    "My stomach hurts",
    "I need water please",
    "Thank you doctor",
    "Yes",
    "No",
]


def ensure_dirs() -> None:
    for d in (ASSETS_DIR, MODELS_DIR, DATA_DIR, RECORDINGS_DIR,
              MEDIAPIPE_DIR, ASL_VIDEOS_DIR):
        os.makedirs(d, exist_ok=True)
