"""Numerical helpers."""

from __future__ import annotations

import math
from typing import Dict

from .config import LIKERT_ORDER


def largest_remainder_round(values: Dict[str, float]) -> Dict[str, float]:
    """Round percentages to 2dp while keeping the total exactly 100."""
    floors = {}
    fracs = {}
    for label in LIKERT_ORDER:
        val = float(values.get(label, 0.0))
        floors[label] = math.floor(val * 100.0) / 100.0
        fracs[label] = val - floors[label]
    remainder = round(100.0 - sum(floors.values()), 2)
    step = 0.01 if remainder >= 0 else -0.01
    steps = int(round(abs(remainder) * 100))
    order = sorted(fracs, key=lambda k: fracs[k], reverse=(remainder >= 0))
    idx = 0
    while steps > 0 and order:
        key = order[idx % len(order)]
        floors[key] = round(floors[key] + step, 2)
        steps -= 1
        idx += 1
    total = round(sum(floors.values()), 2)
    if total != 100.0:
        adjust = round(100.0 - total, 2)
        key = max(floors, key=floors.get)
        floors[key] = round(floors[key] + adjust, 2)
    return floors


def normalise_distribution(dist: Dict[str, float]) -> Dict[str, float]:
    """Normalise raw scores to a 100% distribution."""
    filtered = {k: max(0.0, float(dist.get(k, 0.0))) for k in LIKERT_ORDER}
    total = sum(filtered.values())
    if total <= 0:
        equal = 100.0 / len(LIKERT_ORDER)
        return {k: round(equal, 2) for k in LIKERT_ORDER}
    percentages = {k: (filtered[k] / total) * 100.0 for k in LIKERT_ORDER}
    return largest_remainder_round(percentages)
