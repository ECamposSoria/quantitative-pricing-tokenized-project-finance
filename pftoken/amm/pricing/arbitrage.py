"""
Arbitrage detection helpers for AMM pools vs. reference curves.

These utilities are intentionally simple—suitable for unit testing and
scenario generation—while leaving room for more sophisticated search
algorithms (multi-pool, routing, etc.) later on.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class ArbitrageSignal:
    price_delta: float
    relative_delta: float
    direction: str


def detect_simple_arbitrage(pool_price: float, reference_price: float, threshold: float = 0.01) -> ArbitrageSignal | None:
    """
    Trigger an arbitrage signal if the relative delta exceeds the threshold.

    `threshold` is expressed as a decimal (1% = 0.01).
    """
    if reference_price == 0:
        raise ZeroDivisionError("reference_price cannot be zero.")
    relative_delta = (pool_price - reference_price) / reference_price
    if abs(relative_delta) < threshold:
        return None

    direction = "buy_pool_sell_reference" if relative_delta < 0 else "sell_pool_buy_reference"
    return ArbitrageSignal(price_delta=pool_price - reference_price, relative_delta=relative_delta, direction=direction)


def mean_reversion_score(deviations: Iterable[float]) -> float:
    """
    Compute a z-score style metric to gauge deviation significance.

    This is a placeholder for more advanced statistical tooling that will
    likely leverage rolling-window volatility estimates.
    """
    deviations_arr = np.asarray(list(deviations), dtype=float)
    if deviations_arr.size == 0:
        raise ValueError("deviations cannot be empty.")
    std = deviations_arr.std(ddof=1)
    if std == 0:
        return 0.0
    return float(deviations_arr[-1] / std)
