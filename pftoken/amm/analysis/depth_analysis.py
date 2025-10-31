"""Liquidity depth helpers for AMM pools."""

from __future__ import annotations

from typing import Iterable, Tuple

import numpy as np


def cumulative_depth(levels: Iterable[Tuple[float, float]]) -> np.ndarray:
    """
    Aggregate cumulative depth from price/quantity levels.

    Parameters
    ----------
    levels:
        Iterable of (price, quantity) tuples sorted by price away from mid.
    """
    qty = np.asarray([lvl[1] for lvl in levels], dtype=float)
    if qty.size == 0:
        raise ValueError("levels cannot be empty.")
    return np.cumsum(qty)


def depth_ratio(depth_near: float, depth_far: float) -> float:
    if depth_far == 0:
        raise ZeroDivisionError("depth_far cannot be zero.")
    return depth_near / depth_far
