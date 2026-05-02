"""PrimaryButton — the single 'advance the flow' action used across screens.

Wraps `CircleButton` so every screen's primary action looks identical: the
56 px traffic-light circle the user already trusts on ConfirmScreen.

Variants:
    confirm — green, advance forward (Continue / Done / Confirm)
    retry   — red,   restart / replay
    edit    — yellow, modify
"""
from __future__ import annotations

from gui.widgets.circle_button import CircleButton


class PrimaryButton(CircleButton):
    def __init__(self, label: str, variant: str = "confirm", parent=None):
        super().__init__(label, variant=variant, parent=parent)
