"""
LP PnL analytics comparing providing liquidity vs. simply holding the assets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

import numpy as np

from .impermanent_loss import il_v2, il_v3_range


@dataclass(frozen=True)
class LPPnLBreakdown:
    fees_earned: float
    impermanent_loss: float
    net_pnl: float


@dataclass(frozen=True)
class LPPnLDecomposition:
    fees_earned: float
    impermanent_loss: float
    price_appreciation: float
    net_pnl: float


def pnl_vs_hold(
    fees_collected: float,
    initial_value: float,
    final_pool_value: float,
    final_hold_value: float,
) -> LPPnLBreakdown:
    """Compare LP payoff vs. hodling the underlying assets."""
    if initial_value <= 0:
        raise ValueError("initial_value must be positive.")
    impermanent_loss = final_pool_value - final_hold_value
    net_pnl = fees_collected + final_pool_value - initial_value
    return LPPnLBreakdown(
        fees_earned=fees_collected,
        impermanent_loss=impermanent_loss,
        net_pnl=net_pnl,
    )


def cumulative_fees(fee_series: Iterable[float]) -> float:
    values = np.asarray(list(fee_series), dtype=float)
    if values.size == 0:
        return 0.0
    return float(values.sum())


def pnl_decomposition(
    amount0_start: float,
    amount1_start: float,
    price_start: float,
    price_end: float,
    fees_earned: float,
    tick_lower: Optional[int] = None,
    tick_upper: Optional[int] = None,
) -> LPPnLDecomposition:
    """Decompose LP PnL into fees, impermanent loss and price appreciation."""
    if price_start <= 0 or price_end <= 0:
        raise ValueError("Prices must be positive.")
    initial_value = amount0_start * price_start + amount1_start
    hold_end_value = amount0_start * price_end + amount1_start

    if tick_lower is not None and tick_upper is not None:
        il_fraction = il_v3_range(price_start, price_end, tick_lower, tick_upper)
    else:
        il_fraction = il_v2(price_end / price_start)

    lp_end_value = hold_end_value * (1 + il_fraction)
    price_appreciation = hold_end_value - initial_value
    net_pnl = lp_end_value + fees_earned - initial_value
    return LPPnLDecomposition(
        fees_earned=fees_earned,
        impermanent_loss=lp_end_value - hold_end_value,
        price_appreciation=price_appreciation,
        net_pnl=net_pnl,
    )


__all__ = [
    "LPPnLBreakdown",
    "LPPnLDecomposition",
    "pnl_vs_hold",
    "cumulative_fees",
    "pnl_decomposition",
]
