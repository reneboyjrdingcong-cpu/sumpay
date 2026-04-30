"""Tests for TTSWorker queue semantics (no actual audio synthesis)."""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import queue
import threading
import time


def test_speak_puts_text_in_queue():
    """speak() is non-blocking and enqueues the string."""
    q: queue.Queue = queue.Queue()

    def fake_speak(text):
        q.put(text)

    import types
    from core import tts as tts_mod
    worker = tts_mod.TTSWorker.__new__(tts_mod.TTSWorker)
    worker._queue = queue.Queue()
    worker._running = True
    worker.speak("hello world")
    assert not worker._queue.empty()
    item = worker._queue.get_nowait()
    assert item == "hello world"


def test_speak_ignores_whitespace_only():
    from core import tts as tts_mod
    worker = tts_mod.TTSWorker.__new__(tts_mod.TTSWorker)
    worker._queue = queue.Queue()
    worker._running = True
    worker.speak("   ")
    assert worker._queue.empty()


def test_stop_puts_sentinel():
    from core import tts as tts_mod
    worker = tts_mod.TTSWorker.__new__(tts_mod.TTSWorker)
    worker._queue = queue.Queue()
    worker._running = True
    worker.stop()
    item = worker._queue.get_nowait()
    assert item is None  # sentinel value
