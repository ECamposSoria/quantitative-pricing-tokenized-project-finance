"""
LP PnL analytics comparing providing liquidity vs. simply holding the assets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class LPPnLBreakdown:
    fees_earned: float
    impermanent_loss: float
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
