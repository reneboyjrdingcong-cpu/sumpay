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
RADIUS_PILL   = 999

# 8 px spacing scale — every margin / gap / padding lands on this grid.
SPACE_XS  = 8
SPACE_SM  = 16
SPACE_MD  = 24
SPACE_LG  = 32
SPACE_XL  = 48
SPACE_2XL = 64

# Unified screen layout (patient-side flow uses these everywhere)
SCREEN_PADDING_H      = 48
SCREEN_PADDING_TOP    = 24
SCREEN_PADDING_BOTTOM = 40
CONTENT_MAX_WIDTH     = 1100

FONT_FAMILY        = '"SF Pro Display", "Segoe UI", "Helvetica Neue", Arial, sans-serif'
FONT_SIZE_BODY     = 16
FONT_SIZE_HINT     = 14
FONT_SIZE_HEADER   = 28
FONT_SIZE_GREETING = 56

# Type scale (additive aliases + new sizes filling the gaps)
FONT_SIZE_DISPLAY  = FONT_SIZE_GREETING   # 56 — splash hello
FONT_SIZE_TITLE    = FONT_SIZE_HEADER     # 28 — large screen titles
FONT_SIZE_HEADING  = 24                   # body content on confirm / audio
FONT_SIZE_BODY_LG  = 20                   # subtitles, screen titles inline
FONT_SIZE_CAPTION  = FONT_SIZE_BODY_LG    # 20 — playback transcript caption

# Weight tokens — name what is already in use
WEIGHT_LIGHT   = 300
WEIGHT_REGULAR = 400
WEIGHT_MEDIUM  = 500
WEIGHT_SEMI    = 600

# Phase 2 — semantic tokens replacing previously-hardcoded values
WAVE_BAR         = "#1D1D1F"               # waveform fill (== TEXT_PRIMARY)
STATUS_LIVE_DOT  = "#FF3B30"               # systemRed for the live recording dot
TEXT_SELECTION   = "rgba(0, 122, 255, 60)" # systemBlue 24% — text-edit selection
ACCENT_EDIT_TINT = "rgba(255, 159, 10, 36)" # editing pill background

# Centralized animation magic numbers (Phase 1 already uses these values)
PULSE_DURATION_MS = 900
HOVER_BLUR_REST   = 40
HOVER_BLUR_ACTIVE = 60

# Landmark overlay — kept visible against white background
LANDMARK_HAND       = "#1D1D1F"
LANDMARK_FACE       = "#8A8A8E"
LANDMARK_CONNECTION = "#3A3A3C"

WINDOW_TITLE     = "Project Sumpay"
WINDOW_MIN_WIDTH  = 1280
WINDOW_MIN_HEIGHT = 800
