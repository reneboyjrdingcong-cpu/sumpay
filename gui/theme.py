"""High-contrast flat color palette and typography constants.

Referenced by both styles.qss (via string substitution at startup) and
Qt code that needs raw color values (e.g. landmark overlay painter).
"""
from __future__ import annotations

BG_PRIMARY = "#0A0E14"
BG_SECONDARY = "#131820"
BG_PANEL = "#1A2230"
BORDER = "#2A3445"

ACCENT = "#00E5FF"
ACCENT_DIM = "#4FC3F7"

TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#B0BEC5"
TEXT_MUTED = "#607D8B"

SUCCESS = "#00E676"
WARNING = "#FFAB00"
ERROR = "#FF5252"

LANDMARK_HAND = "#00E5FF"
LANDMARK_FACE = "#FFAB00"
LANDMARK_CONNECTION = "#4FC3F7"

FONT_FAMILY = '"Segoe UI", "Helvetica Neue", Arial, sans-serif'
FONT_SIZE_BASE = 14
FONT_SIZE_HEADER = 22
FONT_SIZE_TRANSCRIPT = 26
FONT_SIZE_CAPTION = 30

WINDOW_TITLE = "Project Sumpay  -  Offline Edge-AI Communication Dashboard"
WINDOW_MIN_WIDTH = 1400
WINDOW_MIN_HEIGHT = 820
