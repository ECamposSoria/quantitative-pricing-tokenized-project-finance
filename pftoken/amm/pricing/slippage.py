"""Slippage analytics for AMM trades."""

from __future__ import annotations

from typing import Iterable, Sequence

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


def slippage_curve(prices_before: float, sizes: Sequence[float], price_after_fn) -> np.ndarray:
    """
    Build a slippage curve for a set of trade sizes given a pricing callback.

    price_after_fn(size) should return the post-trade price for the given size.
    """
    sizes_arr = np.asarray(list(sizes), dtype=float)
    if sizes_arr.size == 0:
        raise ValueError("sizes cannot be empty.")
    if np.any(sizes_arr <= 0):
        raise ValueError("sizes must be positive.")
    slippages = []
    for size in sizes_arr:
        after = price_after_fn(size)
        slippages.append(slippage_percent(prices_before, after))
    return np.column_stack((sizes_arr, np.asarray(slippages, dtype=float)))
