"""Helpers for Q64.96 sqrt price math (Uniswap v3 style)."""

from __future__ import annotations

import math

Q96 = 2**96
MIN_TICK = -887272
MAX_TICK = 887272
MIN_SQRT_PRICE_X96 = int(math.pow(1.0001, MIN_TICK / 2) * Q96)
MAX_SQRT_PRICE_X96 = int(math.pow(1.0001, MAX_TICK / 2) * Q96)


def tick_to_sqrt_price_x96(tick: int) -> int:
    tick = max(MIN_TICK, min(MAX_TICK, tick))
    return int(math.pow(1.0001, tick / 2) * Q96)


def sqrt_price_x96_to_tick(sqrt_price_x96: int) -> int:
    sqrt_price = sqrt_price_x96 / Q96
    tick_est = int(round(2 * math.log(sqrt_price, 1.0001)))
    return max(MIN_TICK, min(MAX_TICK, tick_est))


def get_amount0_delta(sqrt_price_ax96: int, sqrt_price_bx96: int, liquidity: float) -> float:
    """Token0 amount for moving between sqrt prices."""
    sqrt_a = sqrt_price_ax96 / Q96
    sqrt_b = sqrt_price_bx96 / Q96
    if sqrt_a == sqrt_b:
        return 0.0
    upper = max(sqrt_a, sqrt_b)
    lower = min(sqrt_a, sqrt_b)
    return liquidity * (1.0 / lower - 1.0 / upper)


def get_amount1_delta(sqrt_price_ax96: int, sqrt_price_bx96: int, liquidity: float) -> float:
    """Token1 amount for moving between sqrt prices."""
    sqrt_a = sqrt_price_ax96 / Q96
    sqrt_b = sqrt_price_bx96 / Q96
    if sqrt_a == sqrt_b:
        return 0.0
    upper = max(sqrt_a, sqrt_b)
    lower = min(sqrt_a, sqrt_b)
    return liquidity * (upper - lower)


__all__ = [
    "Q96",
    "MIN_TICK",
    "MAX_TICK",
    "MIN_SQRT_PRICE_X96",
    "MAX_SQRT_PRICE_X96",
    "tick_to_sqrt_price_x96",
    "sqrt_price_x96_to_tick",
    "get_amount0_delta",
    "get_amount1_delta",
]
