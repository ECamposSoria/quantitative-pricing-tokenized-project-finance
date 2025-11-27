"""Impermanent loss calculators (v2 and range-aware v3 approximations)."""

from __future__ import annotations

import math
from typing import Iterable, Sequence, Tuple

import numpy as np


def il_v2(price_ratio: float) -> float:
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
    return np.vectorize(il_v2)(ratios)


def il_v3_range(price_start: float, price_end: float, tick_lower: int, tick_upper: int) -> float:
    """
    Approximate impermanent loss for a concentrated position over a price move.

    Uses Uniswap v3 liquidity formulas with unit liquidity to compute holdings
    at start/end, then compares LP value vs holding the initial amounts.
    """
    if price_start <= 0 or price_end <= 0:
        raise ValueError("Prices must be positive.")
    if tick_lower >= tick_upper:
        raise ValueError("tick_lower must be below tick_upper.")

    sqrt_lower = math.sqrt(math.pow(1.0001, tick_lower))
    sqrt_upper = math.sqrt(math.pow(1.0001, tick_upper))
    sqrt_start = math.sqrt(price_start)
    sqrt_end = math.sqrt(price_end)

    def amounts_at_price(sqrt_price: float) -> Tuple[float, float]:
        if sqrt_price <= sqrt_lower:
            # Entirely token0
            amount0 = 1.0 * (1 / sqrt_lower - 1 / sqrt_upper)
            return amount0, 0.0
        if sqrt_price >= sqrt_upper:
            # Entirely token1
            amount1 = 1.0 * (sqrt_upper - sqrt_lower)
            return 0.0, amount1
        amount0 = 1.0 * (1 / sqrt_price - 1 / sqrt_upper)
        amount1 = 1.0 * (sqrt_price - sqrt_lower)
        return amount0, amount1

    amt0_start, amt1_start = amounts_at_price(sqrt_start)
    amt0_end, amt1_end = amounts_at_price(sqrt_end)

    hold_end_value = amt0_start * price_end + amt1_start
    lp_end_value = amt0_end * price_end + amt1_end
    if hold_end_value == 0:
        return 0.0
    return lp_end_value / hold_end_value - 1.0


def il_surface(price_ratios: Sequence[float], tick_ranges: Sequence[Tuple[int, int]]) -> np.ndarray:
    """
    Build a grid of IL values for price ratios across multiple tick ranges.
    """
    ratios = np.asarray(list(price_ratios), dtype=float)
    if ratios.size == 0:
        raise ValueError("price_ratios cannot be empty.")
    surface = []
    for lower, upper in tick_ranges:
        row = [il_v3_range(1.0, ratio, lower, upper) for ratio in ratios]
        surface.append(row)
    return np.asarray(surface, dtype=float)


def fee_breakeven(il_abs: float, daily_fees: float, holding_period_days: int) -> float:
    """
    Return the minimum days required for cumulative fees to offset IL.
    """
    if daily_fees <= 0:
        return math.inf
    if holding_period_days <= 0:
        raise ValueError("holding_period_days must be positive.")
    days_needed = abs(il_abs) / daily_fees
    if days_needed > holding_period_days:
        return math.inf
    return days_needed


# Backwards compatibility alias
impermanent_loss = il_v2

__all__ = [
    "il_v2",
    "impermanent_loss",
    "impermanent_loss_series",
    "il_v3_range",
    "il_surface",
    "fee_breakeven",
]
