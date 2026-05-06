"""TTSWorker — threaded offline text-to-speech engine.

On Windows, uses win32com.client SAPI5 directly. pyttsx3 (which also wraps
SAPI5) has a known issue where the second runAndWait() in the same engine
silently produces no audio, breaking the Replay button. Calling SAPI5
directly avoids that. Falls back to pyttsx3 on macOS/Linux.

Signals:
  busy_changed(bool) — True when speaking, False when idle
"""
from __future__ import annotations

import queue
import sys
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
        if sys.platform == "win32":
            self._run_sapi()
        else:
            self._run_pyttsx3()

    # ------------------------------------------------------------------ #
    # Windows path — direct SAPI5 via win32com (reliable for replay).
    # ------------------------------------------------------------------ #
    def _run_sapi(self) -> None:
        try:
            import pythoncom
            from win32com.client import Dispatch
        except Exception as exc:
            print(f"[tts] win32com unavailable, falling back to pyttsx3: {exc}")
            self._run_pyttsx3()
            return

        try:
            pythoncom.CoInitialize()
        except Exception as exc:
            print(f"[tts] CoInitialize failed: {exc}")
            return

        try:
            try:
                voice = Dispatch("SAPI.SpVoice")
                # SAPI rate is -10..10 (0 ≈ 200 wpm). Map our wpm-ish rate.
                voice.Rate = max(-10, min(10, (self._rate - 200) // 20))
                voice.Volume = max(0, min(100, int(self._volume * 100)))
            except Exception as exc:
                print(f"[tts] SAPI voice init failed: {exc}")
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
                    voice.Speak(text)  # blocks until done (default flags = 0)
                except Exception as exc:
                    print(f"[tts] error speaking: {exc}")
                finally:
                    self.busy_changed.emit(False)
        finally:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass

    # ------------------------------------------------------------------ #
    # macOS / Linux path — pyttsx3 wraps NSSpeech / eSpeak.
    # ------------------------------------------------------------------ #
    def _run_pyttsx3(self) -> None:
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

            if text is None:
                break

            self.busy_changed.emit(True)
            try:
                engine.say(text)
                engine.runAndWait()
            except Exception as exc:
                print(f"[tts] error speaking: {exc}")
            finally:
                self.busy_changed.emit(False)

    # ------------------------------------------------------------------ #

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
