"""
Liquidity stress testing scaffolding for AMM pools.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class LiquidityStressResult:
    depleted_liquidity: float
    max_drawdown: float


def stress_liquidity(liquidity_series: Iterable[float], shock_fraction: float) -> LiquidityStressResult:
    """
    Apply a proportional liquidity shock and compute stress metrics.
    """
    if not 0 <= shock_fraction <= 1:
        raise ValueError("shock_fraction must lie in [0, 1].")
    series = np.asarray(list(liquidity_series), dtype=float)
    if series.size == 0:
        raise ValueError("liquidity_series cannot be empty.")
    shocked = series * (1 - shock_fraction)
    drawdown = (series - shocked) / series
    return LiquidityStressResult(
        depleted_liquidity=float(series.sum() - shocked.sum()),
        max_drawdown=float(drawdown.max()),
    )
