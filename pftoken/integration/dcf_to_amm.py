"""
Pipeline helpers that map DCF cashflows into AMM liquidity actions.

The goal is to keep deterministic valuation outputs and AMM mechanics in
sync, enabling stress backtests that span both domains.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import numpy as np


@dataclass(frozen=True)
class LiquidityInstruction:
    """Represents a liquidity adjustment derived from DCF outputs."""

    timestamp: int
    amount_token0: float
    amount_token1: float


def allocate_liquidity(cfads: Iterable[float], price_series: Iterable[float]) -> List[LiquidityInstruction]:
    """
    Map CFADS projections to proportional liquidity contributions.

    This simplistic placeholder converts cashflows into token amounts
    using the provided price series so that scenario propagation can reuse
    the deterministic forecast.
    """
    cfads_arr = np.asarray(list(cfads), dtype=float)
    prices_arr = np.asarray(list(price_series), dtype=float)
    if cfads_arr.size != prices_arr.size:
        raise ValueError("CFADS and price series must share shape.")
    instructions: List[LiquidityInstruction] = []
    for idx, (cashflow, price) in enumerate(zip(cfads_arr, prices_arr)):
        amount_token0 = cashflow / price if price else 0.0
        instructions.append(
            LiquidityInstruction(
                timestamp=idx,
                amount_token0=amount_token0,
                amount_token1=cashflow,
            )
        )
    return instructions
