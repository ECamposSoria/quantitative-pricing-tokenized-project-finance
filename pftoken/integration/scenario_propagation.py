"""
Propagate Monte Carlo / stress scenarios into AMM parameters.
"""

from __future__ import annotations

from typing import Iterable, Mapping

import numpy as np


def propagate_shocks(base_prices: Iterable[float], shocks: Iterable[float]) -> np.ndarray:
    """
    Apply multiplicative shocks to a base price series.

    Parameters
    ----------
    base_prices:
        Deterministic valuation path (e.g., DCF output)
    shocks:
        Scenario multipliers sampled from Monte Carlo or stress engines
    """
    base = np.asarray(list(base_prices), dtype=float)
    shock_arr = np.asarray(list(shocks), dtype=float)
    if base.size != shock_arr.size:
        raise ValueError("base_prices and shocks must share shape.")
    return base * shock_arr


def map_to_pool_params(shock_series: Iterable[float], base_fee_bps: int) -> list[Mapping[str, float]]:
    """
    Translate scenario shocks into pool parameter adjustments.

    The placeholder returns a fee bump proportional to the shock magnitude.
    """
    params = []
    for idx, shock in enumerate(shock_series):
        params.append(
            {
                "step": idx,
                "fee_bps": max(base_fee_bps * (1 + shock), 0),
            }
        )
    return params
