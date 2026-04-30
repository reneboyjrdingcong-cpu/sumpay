"""STTWorker — offline streaming speech-to-text via Vosk.

Uses sounddevice to capture mic audio and feeds 16-kHz PCM chunks to the
Vosk recognizer.  Runs in its own QThread; never blocks the GUI.

Signals:
  partial_transcript(str)  — live in-progress words (updates as doctor speaks)
  final_transcript(str)    — complete utterance (end-of-speech detected)
  mic_level(float)         — RMS level in [0, 1] for the mic bar in status bar
"""
from __future__ import annotations

import json
import queue
from pathlib import Path
from typing import Optional

import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

import config


class STTWorker(QThread):
    partial_transcript: pyqtSignal = pyqtSignal(str)
    final_transcript: pyqtSignal = pyqtSignal(str)
    mic_level: pyqtSignal = pyqtSignal(float)

    def __init__(
        self,
        model_dir: str,
        sample_rate: int = config.MIC_SAMPLE_RATE,
        block_size: int = config.MIC_BLOCK_SIZE,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._model_dir = model_dir
        self._sample_rate = sample_rate
        self._block_size = block_size
        self._running = False
        self._audio_queue: queue.Queue[Optional[np.ndarray]] = queue.Queue()

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        """Called by sounddevice from its own thread — just enqueue the chunk."""
        chunk = indata[:, 0].copy()  # mono
        rms = float(np.sqrt(np.mean(chunk ** 2)))
        level = min(rms * 20.0, 1.0)  # rough normalisation
        self.mic_level.emit(level)
        self._audio_queue.put_nowait(chunk)

    def run(self) -> None:
        self._running = True

        try:
            from vosk import Model, KaldiRecognizer
        except ImportError:
            print("[stt] vosk not installed — STT disabled")
            return

        if not Path(self._model_dir).exists():
            print(f"[stt] Vosk model not found at {self._model_dir} — STT disabled")
            return

        try:
            import sounddevice as sd
        except ImportError:
            print("[stt] sounddevice not installed — STT disabled")
            return

        try:
            model = Model(self._model_dir)
            rec = KaldiRecognizer(model, self._sample_rate)
            rec.SetWords(True)
        except Exception as exc:
            print(f"[stt] Vosk init error: {exc}")
            return

        try:
            stream = sd.InputStream(
                samplerate=self._sample_rate,
                blocksize=self._block_size,
                dtype="float32",
                channels=1,
                callback=self._audio_callback,
            )
        except Exception as exc:
            print(f"[stt] microphone open failed: {exc}")
            return

        with stream:
            while self._running:
                try:
                    chunk = self._audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                if chunk is None:
                    break

                # Vosk expects 16-bit PCM bytes
                pcm = (chunk * 32767).astype(np.int16).tobytes()
                if rec.AcceptWaveform(pcm):
                    result = json.loads(rec.Result())
                    text = result.get("text", "").strip()
                    if text:
                        self.final_transcript.emit(text)
                else:
                    partial = json.loads(rec.PartialResult())
                    ptext = partial.get("partial", "").strip()
                    if ptext:
                        self.partial_transcript.emit(ptext)

    def stop(self) -> None:
        self._running = False
        self._audio_queue.put(None)
