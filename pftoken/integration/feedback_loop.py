"""
Feedback mechanisms to push market signals back into deterministic models.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np


def update_discount_rate(base_curve: Iterable[float], market_spread: Iterable[float]) -> np.ndarray:
    """
    Adjust a discount curve using observed market spreads.

    This keeps the deterministic valuation framework responsive to AMM
    price discovery during stress testing.
    """
    base = np.asarray(list(base_curve), dtype=float)
    spread = np.asarray(list(market_spread), dtype=float)
    if base.size != spread.size:
        raise ValueError("base_curve and market_spread must share shape.")
    return base + spread


def feedback_score(deviations: Iterable[float], decay: float = 0.9) -> float:
    """
    Compute an exponentially weighted score capturing persistent deviations.
    """
    if not 0 < decay <= 1:
        raise ValueError("decay must be in (0, 1].")
    score = 0.0
    for deviation in deviations:
        score = decay * score + deviation
    return score
