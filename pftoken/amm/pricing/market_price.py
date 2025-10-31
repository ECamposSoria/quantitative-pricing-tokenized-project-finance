"""Helpers to extract observable prices from AMM pool state."""

from __future__ import annotations

from datetime import timedelta
from typing import Iterable, Sequence

import numpy as np

from ..core.pool_v2 import ConstantProductPool


def spot_price(pool: ConstantProductPool) -> float:
    """Return instantaneous price of token0 denominated in token1."""
    return pool.price()


def geometric_twap(prices: Sequence[float], window: timedelta) -> float:
    """
    Compute a geometric mean TWAP for the provided price sequence.

    The implementation assumes prices are sampled at uniform intervals,
    which matches the simplifications used in stress scenarios.
    """
    if not prices:
        raise ValueError("prices cannot be empty.")
    if window <= timedelta(0):
        raise ValueError("window must be positive.")

    log_prices = np.log(np.asarray(prices, dtype=float))
    return float(np.exp(log_prices.mean()))


def price_deviation(observed: float, reference: float) -> float:
    """Express deviation as percentage relative to reference."""
    if reference == 0:
        raise ZeroDivisionError("reference price cannot be zero.")
    return (observed - reference) / reference
