"""KeywordRouter — maps STT transcript text to ASL response video paths.

Matching uses whole-word regex so "rest" inside "the rest of the results"
does not trigger the "rest" keyword.

Emits:
  play_video(str) — absolute path to the matching MP4 file
"""
from __future__ import annotations

import re
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot


class KeywordRouter(QObject):
    play_video: pyqtSignal = pyqtSignal(str)

    def __init__(
        self,
        keyword_map: dict[str, str],
        videos_dir: Path,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._videos_dir = videos_dir
        # Pre-compile whole-word patterns, longest keyword first so more
        # specific phrases win over shorter substrings (e.g. "take your medicine"
        # before "take medicine").
        self._patterns: list[tuple[re.Pattern, Path]] = []
        for keyword in sorted(keyword_map, key=len, reverse=True):
            video_name = keyword_map[keyword]
            video_path = videos_dir / video_name
            pattern = re.compile(
                r"\b" + re.escape(keyword.lower()) + r"\b",
                re.IGNORECASE,
            )
            self._patterns.append((pattern, video_path))

    @pyqtSlot(str)
    def match(self, text: str) -> None:
        """Called from the STT final_transcript signal."""
        normalized = text.strip().lower()
        for pattern, video_path in self._patterns:
            if pattern.search(normalized):
                if video_path.exists():
                    self.play_video.emit(str(video_path.resolve()))
                else:
                    print(f"[router] keyword matched but video missing: {video_path}")
                return  # first match wins
