"""Hedging simulation module for Monte Carlo analysis."""

from .hedge_simulator import (
    HedgeConfig,
    apply_hedge_to_cfads,
    cap_payout,
    collar_payout,
    floor_payout,
    run_hedging_comparison,
)

__all__ = [
    "HedgeConfig",
    "apply_hedge_to_cfads",
    "cap_payout",
    "collar_payout",
    "floor_payout",
    "run_hedging_comparison",
]
