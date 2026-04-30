"""Tests for KeywordRouter matching logic."""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import tempfile
import os
from pathlib import Path


def _make_router(keyword_map, tmp_dir):
    """Create a KeywordRouter with dummy video files for the listed keywords."""
    # Create placeholder video files so video_path.exists() passes
    for video_name in keyword_map.values():
        (Path(tmp_dir) / video_name).touch()

    import config
    # Minimal PyQt6 QApplication needed to instantiate QObject
    try:
        from PyQt6.QtWidgets import QApplication
        import sys
        if not QApplication.instance():
            _app = QApplication.instance() or QApplication(sys.argv)
    except Exception:
        pass

    from core.keyword_router import KeywordRouter
    return KeywordRouter(keyword_map, Path(tmp_dir))


def test_exact_keyword_triggers_video():
    kmap = {"take your medicine": "take_medicine.mp4", "rest": "rest.mp4"}
    with tempfile.TemporaryDirectory() as tmp:
        router = _make_router(kmap, tmp)
        emitted = []
        router.play_video.connect(lambda p: emitted.append(p))
        router.match("please take your medicine now")
        assert len(emitted) == 1
        assert "take_medicine.mp4" in emitted[0]


def test_partial_word_does_not_match():
    kmap = {"rest": "rest.mp4"}
    with tempfile.TemporaryDirectory() as tmp:
        router = _make_router(kmap, tmp)
        emitted = []
        router.play_video.connect(lambda p: emitted.append(p))
        router.match("the results are interesting")  # "rest" inside "results"
        assert emitted == []


def test_case_insensitive_match():
    kmap = {"breathe deeply": "breathe_deeply.mp4"}
    with tempfile.TemporaryDirectory() as tmp:
        router = _make_router(kmap, tmp)
        emitted = []
        router.play_video.connect(lambda p: emitted.append(p))
        router.match("BREATHE DEEPLY please")
        assert len(emitted) == 1


def test_longer_keyword_wins_over_shorter():
    """'take your medicine' should win over bare 'take medicine'."""
    kmap = {
        "take your medicine": "take_medicine.mp4",
        "take medicine": "take_alt.mp4",
    }
    with tempfile.TemporaryDirectory() as tmp:
        router = _make_router(kmap, tmp)
        emitted = []
        router.play_video.connect(lambda p: emitted.append(p))
        router.match("please take your medicine")
        assert len(emitted) == 1
        assert "take_medicine.mp4" in emitted[0]


def test_no_match_emits_nothing():
    kmap = {"rest": "rest.mp4"}
    with tempfile.TemporaryDirectory() as tmp:
        router = _make_router(kmap, tmp)
        emitted = []
        router.play_video.connect(lambda p: emitted.append(p))
        router.match("how are you feeling today")
        assert emitted == []
