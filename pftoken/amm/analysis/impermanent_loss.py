"""Impermanent loss calculators."""

from __future__ import annotations

from typing import Iterable

import numpy as np


def impermanent_loss(price_ratio: float) -> float:
    """
    Compute impermanent loss for a Uniswap v2 LP given price movement.

    price_ratio = P_new / P_old.
    """
    if price_ratio <= 0:
        raise ValueError("price_ratio must be positive.")
    sqrt_ratio = np.sqrt(price_ratio)
    return float(2 * sqrt_ratio / (1 + price_ratio) - 1)


def impermanent_loss_series(price_ratios: Iterable[float]) -> np.ndarray:
    """Vectorized helper turning a sequence of price ratios into IL values."""
    ratios = np.asarray(list(price_ratios), dtype=float)
    if ratios.size == 0:
        raise ValueError("price_ratios cannot be empty.")
    return np.vectorize(impermanent_loss)(ratios)
