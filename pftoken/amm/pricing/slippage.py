"""Slippage analytics for AMM trades."""

from __future__ import annotations

from typing import Iterable

import numpy as np


def slippage_percent(price_before: float, price_after: float) -> float:
    if price_before == 0:
        raise ZeroDivisionError("price_before cannot be zero.")
    return (price_after - price_before) / price_before


def aggregate_slippage(series: Iterable[float]) -> float:
    """Return average absolute slippage over a sequence."""
    arr = np.asarray(list(series), dtype=float)
    if arr.size == 0:
        raise ValueError("series cannot be empty.")
    return float(np.abs(arr).mean())
