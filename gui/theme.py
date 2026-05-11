"""Clinical Light design tokens — calm paper-feel palette for kiosk use.

Drop-in replacement for the previous Apple-style monochromatic tokens.
All structural QSS rules are unchanged; only the values that flow through
@TOKEN@ substitution and the inline-styled widgets pick up the new palette.

Why these values: bright clinical rooms with overhead fluorescents tended to
wash out the white-on-white glass surfaces. We've moved to warm off-white
backgrounds with solid paper cards, real 1px hairlines, and a single
trustworthy teal accent (replacing the iOS traffic-light quad).

Referenced by styles.qss (via @TOKEN@ substitution) and Python code that
needs raw values (landmark overlay painter, shadow effects).
"""
from __future__ import annotations

# ── Surfaces ───────────────────────────────────────────────────────────
BG_PRIMARY        = "#FAFAF7"     # warm off-white (was #FFFFFF)
BG_GLASS          = "#FFFFFF"     # solid paper card (was rgba glass)
BG_GLASS_DEEP     = "#F4F3EE"     # emphasized card body (was rgba 85%)
BORDER_HAIRLINE   = "#E6E4DD"     # solid 1px edge (was rgba 4%)

# ── Text ───────────────────────────────────────────────────────────────
TEXT_PRIMARY      = "#1A1A1A"
TEXT_SECONDARY    = "#5C5B57"
TEXT_HINT         = "#8E8C85"

# ── Accents — calm clinical palette ────────────────────────────────────
# Single trustworthy teal for confirm/proceed; muted brick for retry/stop;
# amber for edit/caution. Each variant gets hover (lighter) + pressed
# (darker) shades so the QSS variant rules can stay token-driven.
ACCENT_PRIMARY          = "#1F8A7E"   # teal — confirm
ACCENT_PRIMARY_HOVER    = "#2BA295"
ACCENT_PRIMARY_PRESSED  = "#176B62"
ACCENT_PRIMARY_TINT     = "rgba(31, 138, 126, 36)"

ACCENT_DANGER           = "#C04A3A"   # muted brick — retry / stop
ACCENT_DANGER_HOVER     = "#D55B4A"
ACCENT_DANGER_PRESSED   = "#9C3B2F"

ACCENT_EDIT             = "#B97C1A"   # amber — edit / caution
ACCENT_EDIT_HOVER       = "#D08E20"
ACCENT_EDIT_PRESSED     = "#966315"
ACCENT_EDIT_TINT        = "rgba(185, 124, 26, 36)"

# ── Shadows — slightly lighter for paper feel ──────────────────────────
SHADOW_SOFT       = "rgba(0, 0, 0, 14)"
SHADOW_MEDIUM     = "rgba(0, 0, 0, 22)"

# ── Radii ──────────────────────────────────────────────────────────────
RADIUS_CARD   = 24
RADIUS_LARGE  = 32
RADIUS_CIRCLE = 32        # was 28 → 64×64 button (gloved-hand target)
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

# ── Type ───────────────────────────────────────────────────────────────
# Bumped across the board for fluorescent-light readability.
FONT_FAMILY        = '"Inter", "SF Pro Display", "Segoe UI", "Helvetica Neue", Arial, sans-serif'
FONT_SIZE_BODY     = 18    # was 16
FONT_SIZE_HINT     = 15    # was 14
FONT_SIZE_HEADER   = 32    # was 28
FONT_SIZE_GREETING = 96    # was 56  (splash 'Hello.')

# Type scale (additive aliases + new sizes filling the gaps)
FONT_SIZE_DISPLAY  = FONT_SIZE_GREETING   # 96 — splash hello
FONT_SIZE_TITLE    = FONT_SIZE_HEADER     # 32 — large screen titles
FONT_SIZE_HEADING  = 30                   # was 24 — body content on confirm / audio
FONT_SIZE_BODY_LG  = 22                   # was 20 — subtitles, screen titles inline
FONT_SIZE_CAPTION  = FONT_SIZE_BODY_LG    # 22 — playback transcript caption

# Weight tokens — name what is already in use
WEIGHT_LIGHT   = 300
WEIGHT_REGULAR = 400
WEIGHT_MEDIUM  = 500
WEIGHT_SEMI    = 600

# ── Semantic tokens (originally Phase 2) ───────────────────────────────
WAVE_BAR         = TEXT_PRIMARY              # waveform fill
STATUS_LIVE_DOT  = ACCENT_DANGER             # live recording dot, now muted brick
TEXT_SELECTION   = ACCENT_PRIMARY_TINT       # text-edit selection — teal tint

# Centralized animation magic numbers (Phase 1 already uses these values)
PULSE_DURATION_MS = 900
HOVER_BLUR_REST   = 40
HOVER_BLUR_ACTIVE = 60

# Landmark overlay — kept visible against warm-paper background
LANDMARK_HAND       = TEXT_PRIMARY
LANDMARK_FACE       = TEXT_HINT
LANDMARK_CONNECTION = "#3A3A3C"

WINDOW_TITLE     = "Project Sumpay"
WINDOW_MIN_WIDTH  = 1280
WINDOW_MIN_HEIGHT = 800
