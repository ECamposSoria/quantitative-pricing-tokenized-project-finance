"""Helpers to extract observable prices from AMM pool state."""

from __future__ import annotations

from datetime import timedelta
import math
from typing import Iterable, Sequence

import numpy as np

from ..core.pool_v2 import ConstantProductPool
from ..core.pool_v3 import ConcentratedLiquidityPool
from ..core.swap_engine import SwapIntent, execute_swap


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


# --------------------------------------------------------------------------- #
# Execution and depth helpers
# --------------------------------------------------------------------------- #

def execution_price(pool: ConstantProductPool | ConcentratedLiquidityPool, amount_in: float, side: str) -> float:
    """
    Simulate execution with slippage and return effective price paid (token1 per token0).
    """
    if amount_in <= 0:
        raise ValueError("amount_in must be positive.")
    # Prefer pure simulation when available to avoid mutating state.
    if hasattr(pool, "simulate_swap"):
        quote = pool.simulate_swap(amount_in, side)
    else:
        quote = execute_swap(pool, SwapIntent(amount_in=amount_in, side_in=side))
    if quote.amount_out == 0:
        raise ZeroDivisionError("Swap produced zero output.")
    if side == "token0":
        return quote.amount_out / quote.amount_in
    return quote.amount_in / quote.amount_out


def depth_curve(pool: ConstantProductPool, price_range: Iterable[float]) -> np.ndarray:
    """
    Compute cumulative token0 depth required to move the pool to target prices.

    Uses the constant-product invariant: for target price p = y/x, with k fixed,
    x_new = sqrt(k / p). Depth = x_new - x_current (token0 in).
    """
    prices = np.asarray(list(price_range), dtype=float)
    if prices.size == 0:
        raise ValueError("price_range cannot be empty.")
    if np.any(prices <= 0):
        raise ValueError("price_range must be positive.")

    k = pool.state.invariant()
    x0 = pool.state.reserve0
    current_price = pool.price()
    depths = []
    for p in prices:
        if p <= current_price:
            depths.append(0.0)
            continue
        x_new = math.sqrt(k / p)
        depths.append(max(0.0, x_new - x0))
    return np.column_stack((prices, np.asarray(depths, dtype=float)))


def twap_sampling(pool: ConstantProductPool, intervals: int) -> np.ndarray:
    """
    Generate a simple TWAP sample assuming stationary price for a fixed number of intervals.
    """
    if intervals <= 0:
        raise ValueError("intervals must be positive.")
    price = pool.price()
    return np.full(shape=intervals, fill_value=price, dtype=float)


def arbitrage_signal(pool_price: float, reference_price: float, threshold: float = 0.01) -> dict | None:
    """
    Enhanced signal helper for downstream consumers.
    """
    if reference_price == 0:
        raise ZeroDivisionError("reference_price cannot be zero.")
    rel = (pool_price - reference_price) / reference_price
    if abs(rel) < threshold:
        return None
    direction = "buy_pool_sell_reference" if rel < 0 else "sell_pool_buy_reference"
    return {"relative_delta": rel, "direction": direction, "price_delta": pool_price - reference_price}
