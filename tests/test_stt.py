"""Tests for STTWorker queue and mic-level logic (no actual Vosk or mic)."""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import queue
import numpy as np


def test_audio_callback_enqueues_mono_chunk():
    """_audio_callback should enqueue a 1-D array (mono channel)."""
    from core import stt as stt_mod
    worker = stt_mod.STTWorker.__new__(stt_mod.STTWorker)
    worker._audio_queue = queue.Queue()
    emitted_levels = []
    worker.mic_level = type("S", (), {"emit": lambda self, v: emitted_levels.append(v)})()

    # Simulate 2-channel indata (sounddevice gives (N, channels))
    indata = np.ones((1024, 2), dtype=np.float32) * 0.05
    worker._audio_callback(indata, 1024, None, None)

    assert not worker._audio_queue.empty()
    chunk = worker._audio_queue.get_nowait()
    assert chunk.ndim == 1
    assert chunk.shape[0] == 1024


def test_audio_callback_emits_level_in_range():
    from core import stt as stt_mod
    worker = stt_mod.STTWorker.__new__(stt_mod.STTWorker)
    worker._audio_queue = queue.Queue()
    levels = []
    worker.mic_level = type("S", (), {"emit": lambda self, v: levels.append(v)})()

    # Full-scale sine — level should be capped at 1.0
    indata = np.sin(np.linspace(0, 2 * np.pi, 1024)).reshape(-1, 1).astype(np.float32)
    worker._audio_callback(indata, 1024, None, None)
    assert 0.0 <= levels[0] <= 1.0


def test_stop_enqueues_sentinel():
    from core import stt as stt_mod
    worker = stt_mod.STTWorker.__new__(stt_mod.STTWorker)
    worker._audio_queue = queue.Queue()
    worker._running = True
    worker.stop()
    assert not worker._audio_queue.empty()
    sentinel = worker._audio_queue.get_nowait()
    assert sentinel is None


def test_silence_threshold_classifies_correctly():
    """Silent chunks must fall below threshold; loud chunks must exceed it."""
    import config
    silent = np.zeros(4000, dtype=np.float32)
    loud = np.ones(4000, dtype=np.float32) * 0.5
    assert float(np.sqrt(np.mean(silent ** 2))) < config.MIC_SILENCE_THRESHOLD
    assert float(np.sqrt(np.mean(loud ** 2))) >= config.MIC_SILENCE_THRESHOLD


def test_constructor_accepts_model_size():
    """STTWorker should store model_size from constructor."""
    from core import stt as stt_mod
    worker = stt_mod.STTWorker.__new__(stt_mod.STTWorker)
    worker._model_size = "base.en"
    worker._sample_rate = 16000
    worker._block_size = 4000
    worker._running = False
    worker._audio_queue = queue.Queue()
    assert worker._model_size == "base.en"
