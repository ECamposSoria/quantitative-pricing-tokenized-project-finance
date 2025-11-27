"""
Glue code to reconcile deterministic DCF valuations with market-driven AMM
signals.  The helpers are intentionally lightweight so they can be extended
once full scenario propagation is in place.
"""

from __future__ import annotations

from typing import Iterable, Tuple

import numpy as np
from .arbitrage_engine import ConvergenceResult


def blend_price(dcf_price: float, market_price: float, weight_market: float = 0.5) -> float:
    """Blend DCF and observed market prices with a convex combination."""
    if not 0 <= weight_market <= 1:
        raise ValueError("weight_market must lie in [0, 1].")
    return (1 - weight_market) * dcf_price + weight_market * market_price


def discrepancy_series(dcf_series: Iterable[float], market_series: Iterable[float]) -> np.ndarray:
    """Return vector of percentage deviations between two value series."""
    dcf = np.asarray(list(dcf_series), dtype=float)
    market = np.asarray(list(market_series), dtype=float)
    if dcf.shape != market.shape:
        raise ValueError("Series must share the same shape.")
    if np.any(dcf == 0):
        raise ZeroDivisionError("DCF series contains zero values.")
    return (market - dcf) / dcf


def adjustment_factor(deviations: Iterable[float]) -> float:
    """Map a set of deviations into a single adjustment factor."""
    deviations_arr = np.asarray(list(deviations), dtype=float)
    if deviations_arr.size == 0:
        raise ValueError("deviations cannot be empty.")
    return float(1 + deviations_arr.mean())


def blend_with_arbitrage(
    dcf_price: float,
    market_price: float,
    arb_result: ConvergenceResult | None,
    weight_market: float = 0.5,
) -> float:
    """
    Adjust blend by penalizing large spreads after convergence simulation.
    """
    blended = blend_price(dcf_price, market_price, weight_market)
    if arb_result is None:
        return blended
    penalty = min(0.05, abs(arb_result.realized_spread_reduction))  # cap at 5%
    return blended * (1 - penalty)
