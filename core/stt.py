"""STTWorker — offline speech-to-text via faster-whisper (Whisper base.en).

Captures mic audio at the device's native rate (MIC_CAPTURE_RATE), resamples
to 16 kHz for Whisper, then buffers until silence is detected before transcribing.
Runs in its own QThread; never blocks the GUI.

Signals:
  partial_transcript(str)  — "..." indicator while doctor is speaking
  final_transcript(str)    — complete utterance after silence detected
  mic_level(float)         — RMS level in [0, 1] for the mic bar in status bar
"""
from __future__ import annotations

import queue
from typing import Optional

import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

import config


def _resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    if orig_sr == target_sr:
        return audio
    target_len = int(len(audio) * target_sr / orig_sr)
    return np.interp(
        np.linspace(0, len(audio) - 1, target_len),
        np.arange(len(audio)),
        audio,
    ).astype(np.float32)


class STTWorker(QThread):
    partial_transcript: pyqtSignal = pyqtSignal(str)
    final_transcript: pyqtSignal = pyqtSignal(str)
    mic_level: pyqtSignal = pyqtSignal(float)

    def __init__(
        self,
        model_size: str = config.WHISPER_MODEL_SIZE,
        sample_rate: int = config.MIC_SAMPLE_RATE,
        block_size: int = config.MIC_BLOCK_SIZE,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._model_size = model_size
        self._sample_rate = sample_rate
        self._block_size = block_size
        self._running = False
        self._audio_queue: queue.Queue[Optional[np.ndarray]] = queue.Queue()

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        """Called by sounddevice from its own thread — enqueue mono chunk."""
        chunk = indata[:, 0].copy() if indata.ndim > 1 else indata.copy()
        rms = float(np.sqrt(np.mean(chunk ** 2)))
        level = min(rms * 20.0, 1.0)
        self.mic_level.emit(level)
        self._audio_queue.put_nowait(chunk)

    def run(self) -> None:
        self._running = True

        try:
            from faster_whisper import WhisperModel
        except ImportError:
            print("[stt] faster-whisper not installed — STT disabled")
            return

        try:
            import sounddevice as sd
        except ImportError:
            print("[stt] sounddevice not installed — STT disabled")
            return

        print(f"[stt] Loading Whisper '{self._model_size}' on CPU (int8)...")
        try:
            model = WhisperModel(self._model_size, device="cpu", compute_type="int8")
        except Exception as exc:
            print(f"[stt] Whisper model load failed: {exc}")
            return
        print("[stt] Whisper ready.")

        capture_rate = config.MIC_CAPTURE_RATE
        dev = sd.query_devices(config.MIC_DEVICE_INDEX) if config.MIC_DEVICE_INDEX is not None else sd.query_devices(kind="input")
        n_channels = min(dev["max_input_channels"], 2)

        try:
            stream = sd.InputStream(
                device=config.MIC_DEVICE_INDEX,
                samplerate=capture_rate,
                blocksize=self._block_size,
                dtype="float32",
                channels=n_channels,
                callback=self._audio_callback,
            )
        except Exception as exc:
            print(f"[stt] microphone open failed: {exc}")
            return

        audio_buffer: list[np.ndarray] = []
        silence_count: int = 0

        def _transcribe(buf: list[np.ndarray]) -> None:
            if len(buf) < config.MIC_MIN_SPEECH_FRAMES:
                return
            raw = np.concatenate(buf)
            audio = _resample(raw, capture_rate, self._sample_rate)
            try:
                segments, _ = model.transcribe(audio, language="en", beam_size=1)
                text = " ".join(seg.text for seg in segments).strip()
                if text:
                    print(f"[stt] transcript: {text!r}")
                    self.final_transcript.emit(text)
            except Exception as exc:
                print(f"[stt] transcription error: {exc}")

        with stream:
            while self._running:
                try:
                    chunk = self._audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                if chunk is None:
                    _transcribe(audio_buffer)
                    break

                audio_buffer.append(chunk)
                rms = float(np.sqrt(np.mean(chunk ** 2)))

                if rms < config.MIC_SILENCE_THRESHOLD:
                    silence_count += 1
                else:
                    silence_count = 0
                    self.partial_transcript.emit("...")

                if silence_count >= config.MIC_SILENCE_FRAMES:
                    _transcribe(audio_buffer)
                    audio_buffer.clear()
                    silence_count = 0

    def stop(self) -> None:
        self._running = False
        self._audio_queue.put(None)
