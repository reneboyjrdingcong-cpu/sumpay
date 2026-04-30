"""TTSWorker — threaded offline text-to-speech engine.

Uses pyttsx3 (wraps SAPI5 on Windows / NSSpeech on macOS / eSpeak on Linux).
Runs in its own QThread with a producer/consumer queue so the GUI and camera
threads are never blocked while speech is in progress.

Signals:
  busy_changed(bool) — True when speaking, False when idle
"""
from __future__ import annotations

import queue
import threading
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal


class TTSWorker(QThread):
    busy_changed: pyqtSignal = pyqtSignal(bool)

    def __init__(self, rate: int = 165, volume: float = 1.0, parent=None) -> None:
        super().__init__(parent)
        self._queue: queue.Queue[Optional[str]] = queue.Queue()
        self._rate = rate
        self._volume = volume
        self._running = False

    def run(self) -> None:
        self._running = True
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", self._rate)
            engine.setProperty("volume", self._volume)
        except Exception as exc:
            print(f"[tts] pyttsx3 init failed: {exc}")
            return

        while self._running:
            try:
                text = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if text is None:  # sentinel — stop
                break

            self.busy_changed.emit(True)
            try:
                engine.say(text)
                engine.runAndWait()
            except Exception as exc:
                print(f"[tts] error speaking: {exc}")
            finally:
                self.busy_changed.emit(False)

    def speak(self, text: str) -> None:
        """Queue text for speaking. Non-blocking; called from any thread."""
        if text.strip():
            try:
                self._queue.put_nowait(text)
            except queue.Full:
                pass

    def stop(self) -> None:
        self._running = False
        self._queue.put(None)  # wake the consumer
