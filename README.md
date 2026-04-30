# Project Sumpay

Standalone, **fully offline** edge-AI two-way communication dashboard for
hospital environments.

- **Patient -> Doctor:** webcam captures continuous ASL; on-device sequence
  model translates the sentence; offline TTS speaks it.
- **Doctor -> Patient:** mic captures speech; offline streaming STT (Vosk)
  transcribes it; medical keywords trigger pre-recorded ASL response clips.

Zero cloud APIs. Zero network calls at runtime.

## Quick start

```bash
pip install -r requirements.txt
python main.py
```

## One-time asset setup (offline)

These artifacts are large and are NOT vendored in the repo. Download them
once on a connected machine and copy the folders into the indicated paths.

1. **MediaPipe Tasks models** -> `assets/mediapipe/`
   - `hand_landmarker.task`
   - `face_landmarker.task`
   (from https://developers.google.com/mediapipe/solutions/vision)

2. **Vosk small English STT model** -> `assets/vosk/vosk-model-small-en-us-0.15/`
   (from https://alphacephei.com/vosk/models)

3. **ASL response clips** -> `assets/asl_videos/*.mp4`
   Filenames must match `KEYWORD_MAP` in `config.py`.

After copying, the app runs entirely without a network connection.

## Train the ASL classifier

```bash
# 1. Record samples for a phrase (do this for each phrase in INITIAL_PHRASES)
python -m training.record_phrase --phrase "I have a headache for a week now" --samples 30

# 2. Train and export TorchScript
python -m training.train

# 3. Evaluate
python -m training.eval
```

## Tests

```bash
pytest tests/
```

## Architecture

See `CLAUDE.md` for the threading model, recognition pipeline, and feature vector layout.
