"""White Mode design tokens — Apple-style monochromatic palette.

Referenced by styles.qss (via @TOKEN@ substitution) and Python code that
needs raw values (landmark overlay painter, shadow effects).
"""
from __future__ import annotations

BG_PRIMARY        = "#FFFFFF"
BG_GLASS          = "rgba(255, 255, 255, 140)"   # ~55% opacity
BG_GLASS_DEEP     = "rgba(245, 245, 247, 217)"   # ~85% opacity
BORDER_HAIRLINE   = "rgba(0, 0, 0, 10)"

TEXT_PRIMARY      = "#1D1D1F"
TEXT_SECONDARY    = "#6E6E73"
TEXT_HINT         = "#A1A1A6"

SHADOW_SOFT       = "rgba(0, 0, 0, 20)"
SHADOW_MEDIUM     = "rgba(0, 0, 0, 31)"

RADIUS_CARD   = 24
RADIUS_LARGE  = 32
RADIUS_CIRCLE = 28

FONT_FAMILY        = '"SF Pro Display", "Segoe UI", "Helvetica Neue", Arial, sans-serif'
FONT_SIZE_BODY     = 16
FONT_SIZE_HINT     = 14
FONT_SIZE_HEADER   = 28
FONT_SIZE_GREETING = 56

# Landmark overlay — kept visible against white background
LANDMARK_HAND       = "#1D1D1F"
LANDMARK_FACE       = "#8A8A8E"
LANDMARK_CONNECTION = "#3A3A3C"

WINDOW_TITLE     = "Project Sumpay"
WINDOW_MIN_WIDTH  = 1280
WINDOW_MIN_HEIGHT = 800
