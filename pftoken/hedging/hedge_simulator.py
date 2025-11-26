"""Hedge payout simulation for Monte Carlo analysis (WP-11/WP-13).

Calculates cap and collar payouts across MC simulation paths and adjusts
CFADS to reflect hedge benefits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np


@dataclass(frozen=True)
class HedgeConfig:
    """Configuration for interest rate hedge simulation.

    Default hedge: CAP (based on 10K MC simulation analysis)

    Analysis (2025-11-26, 10K sims):
    - Unhedged: 2.71% breach probability
    - Cap: 2.09% breach (-23%, $595K cost)
    - Collar: 2.38% breach (-12%, $326K cost)

    Cap provides 23% breach reduction vs 12% for collar.
    Cost per breach avoided: Cap $9,604 vs Collar $9,883.
    Decision: Cap is recommended as default hedge.
    """

    notional: float = 50_000_000.0  # USD
    cap_strike: float = 0.04  # 4%
    floor_strike: float = 0.03  # 3%
    base_rate: float = 0.045  # 4.5% base interest rate
    cap_premium: float = 595_433.0  # Upfront cap premium (USD)
    collar_net_premium: float = 326_139.0  # Net collar premium (USD)
    default_hedge: str = "cap"  # Recommended hedge based on MC analysis


def cap_payout(
    effective_rate: float | np.ndarray,
    strike: float,
    notional: float,
    accrual: float = 1.0,
) -> float | np.ndarray:
    """
    Calculate cap payout for a single period.

    Cap pays max(0, effective_rate - strike) * notional * accrual

    Args:
        effective_rate: The effective interest rate (base + shock)
        strike: Cap strike rate
        notional: Notional amount
        accrual: Year fraction (default 1.0 for annual)

    Returns:
        Cap payout amount
    """
    return np.maximum(0.0, effective_rate - strike) * notional * accrual


def floor_payout(
    effective_rate: float | np.ndarray,
    strike: float,
    notional: float,
    accrual: float = 1.0,
) -> float | np.ndarray:
    """
    Calculate floor payout for a single period.

    Floor pays max(0, strike - effective_rate) * notional * accrual

    Args:
        effective_rate: The effective interest rate (base + shock)
        strike: Floor strike rate
        notional: Notional amount
        accrual: Year fraction (default 1.0 for annual)

    Returns:
        Floor payout amount
    """
    return np.maximum(0.0, strike - effective_rate) * notional * accrual


def collar_payout(
    effective_rate: float | np.ndarray,
    cap_strike: float,
    floor_strike: float,
    notional: float,
    accrual: float = 1.0,
) -> float | np.ndarray:
    """
    Calculate collar net payout (long cap, short floor).

    Collar payout = cap_payout - floor_payout

    When rate > cap_strike: positive payout (cap pays)
    When rate < floor_strike: negative payout (floor costs)
    When floor_strike <= rate <= cap_strike: zero payout

    Args:
        effective_rate: The effective interest rate (base + shock)
        cap_strike: Cap strike rate (upper bound)
        floor_strike: Floor strike rate (lower bound)
        notional: Notional amount
        accrual: Year fraction (default 1.0 for annual)

    Returns:
        Net collar payout amount
    """
    cap_pay = cap_payout(effective_rate, cap_strike, notional, accrual)
    floor_pay = floor_payout(effective_rate, floor_strike, notional, accrual)
    return cap_pay - floor_pay


def apply_hedge_to_cfads(
    cfads_paths: np.ndarray,
    rate_shocks: np.ndarray,
    hedge_type: Literal["none", "cap", "collar"],
    config: HedgeConfig,
) -> np.ndarray:
    """
    Apply hedge payouts to CFADS paths.

    Hedge payouts are added to CFADS as they represent cash inflows that
    offset higher debt service costs when rates rise.

    Args:
        cfads_paths: CFADS paths array, shape (n_sims, n_periods), in USD
        rate_shocks: Rate shock draws from MC, shape (n_sims,)
        hedge_type: "none", "cap", or "collar"
        config: Hedge configuration

    Returns:
        Adjusted CFADS paths with hedge payouts added, same shape as input
    """
    if hedge_type == "none":
        return cfads_paths.copy()

    n_sims, n_periods = cfads_paths.shape

    # Calculate effective rate for each simulation path
    effective_rates = config.base_rate + rate_shocks  # shape (n_sims,)

    # Calculate annual hedge payout per simulation
    if hedge_type == "cap":
        annual_payout = cap_payout(
            effective_rates, config.cap_strike, config.notional
        )
    elif hedge_type == "collar":
        annual_payout = collar_payout(
            effective_rates,
            config.cap_strike,
            config.floor_strike,
            config.notional,
        )
    else:
        raise ValueError(f"Unknown hedge type: {hedge_type}")

    # Broadcast payout to all periods (same payout each year while hedge is active)
    # Shape: (n_sims, 1) -> broadcast to (n_sims, n_periods)
    payout_matrix = np.broadcast_to(annual_payout[:, None], (n_sims, n_periods))

    # Add hedge payouts to CFADS (positive payout = cash inflow = higher CFADS)
    adjusted_cfads = cfads_paths + payout_matrix

    return adjusted_cfads


def run_hedging_comparison(
    cfads_paths: np.ndarray,
    rate_shocks: np.ndarray,
    dual_comparator,
    covenant: float,
    config: HedgeConfig,
) -> dict:
    """
    Run Monte Carlo comparison across hedging scenarios.

    Args:
        cfads_paths: CFADS paths array, shape (n_sims, n_periods), in USD
        rate_shocks: Rate shock draws from MC, shape (n_sims,)
        dual_comparator: DualStructureComparator instance
        covenant: DSCR covenant threshold
        config: Hedge configuration

    Returns:
        Dictionary with hedging comparison results
    """
    scenarios = {}

    for hedge_type in ["none", "cap", "collar"]:
        adjusted_cfads = apply_hedge_to_cfads(
            cfads_paths, rate_shocks, hedge_type, config
        )

        # Run dual structure comparison with adjusted CFADS
        result = dual_comparator.run_monte_carlo_comparison(adjusted_cfads, covenant)

        # Extract key metrics
        tokenized = result.get("tokenized", {})
        cost = 0.0
        if hedge_type == "cap":
            cost = config.cap_premium
        elif hedge_type == "collar":
            cost = config.collar_net_premium

        scenarios[hedge_type] = {
            "breach_probability": tokenized.get("breach_probability", 0.0),
            "breach_count": tokenized.get("breach_count", 0),
            "min_dscr_p5": tokenized.get("min_dscr_p5", 0.0),
            "min_dscr_p25": tokenized.get("min_dscr_p25", 0.0),
            "min_dscr_p50": tokenized.get("min_dscr_p50", 0.0),
            "cost": cost,
        }

    # Determine recommendation
    recommendation, rationale = _determine_recommendation(scenarios, config)

    return {
        "hedge_config": {
            "notional": config.notional,
            "cap_strike": config.cap_strike,
            "floor_strike": config.floor_strike,
            "base_rate": config.base_rate,
            "cap_premium": config.cap_premium,
            "collar_net_premium": config.collar_net_premium,
        },
        "scenarios": scenarios,
        "recommendation": recommendation,
        "rationale": rationale,
    }


def _determine_recommendation(scenarios: dict, config: HedgeConfig) -> tuple[str, str]:
    """Determine the best hedging strategy based on breach reduction per dollar."""
    none_breach = scenarios["none"]["breach_probability"]
    cap_breach = scenarios["cap"]["breach_probability"]
    collar_breach = scenarios["collar"]["breach_probability"]

    cap_reduction = none_breach - cap_breach
    collar_reduction = none_breach - collar_breach

    # If no meaningful reduction, recommend no hedge
    if cap_reduction <= 0.001 and collar_reduction <= 0.001:
        return "none", "Hedges provide minimal breach probability reduction"

    # Calculate cost per basis point of breach reduction
    cap_cost_per_bp = (
        config.cap_premium / (cap_reduction * 10000) if cap_reduction > 0 else float("inf")
    )
    collar_cost_per_bp = (
        config.collar_net_premium / (collar_reduction * 10000)
        if collar_reduction > 0
        else float("inf")
    )

    if collar_cost_per_bp < cap_cost_per_bp:
        cost_savings = (1 - config.collar_net_premium / config.cap_premium) * 100
        return (
            "collar",
            f"Collar provides similar breach reduction at {cost_savings:.0f}% lower cost",
        )
    elif cap_reduction > collar_reduction * 1.2:  # Cap significantly better
        return "cap", "Cap provides materially better breach probability reduction"
    else:
        return "collar", "Collar offers best value (breach reduction per dollar)"


__all__ = [
    "HedgeConfig",
    "cap_payout",
    "floor_payout",
    "collar_payout",
    "apply_hedge_to_cfads",
    "run_hedging_comparison",
]
