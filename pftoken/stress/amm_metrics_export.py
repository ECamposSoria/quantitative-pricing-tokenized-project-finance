"""WP-09 export interface for AMM stress metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Sequence

import numpy as np

from pftoken.amm.core.pool_v2 import ConstantProductPool, PoolConfig, PoolState
from pftoken.amm.pricing.market_price import depth_curve
from .amm_stress_scenarios import AMMStressScenario
from .liquidity_stress import flash_crash_recovery, lp_withdrawal_cascade, panic_sell_ladder, ScenarioOutcome


@dataclass(frozen=True)
class AMMStressMetrics:
    depth_curve: np.ndarray
    slippage_curve: np.ndarray
    stressed_depths: Dict[str, np.ndarray]
    il_by_scenario: Dict[str, float]
    recovery_steps: Dict[str, int]


def _scenario_outcome(pool: ConstantProductPool, scenario: AMMStressScenario) -> ScenarioOutcome:
    if scenario.code == "PS":
        return panic_sell_ladder(pool, scenario.params["steps"])
    if scenario.code == "LP":
        return lp_withdrawal_cascade(pool, scenario.params["steps"])
    if scenario.code == "FC":
        return flash_crash_recovery(pool, scenario.params["drop_fraction"], scenario.params["recovery_fraction"])
    raise ValueError(f"Unknown scenario code {scenario.code}")


def get_stress_metrics(pool: ConstantProductPool, scenarios: Sequence[AMMStressScenario]) -> AMMStressMetrics:
    depth = depth_curve(pool, price_range=[pool.price() * x for x in (0.9, 1.0, 1.1)])
    stressed_depths: Dict[str, np.ndarray] = {}
    il_by_scenario: Dict[str, float] = {}
    recovery_steps: Dict[str, int] = {}
    slippage_curve = np.zeros((0, 2))

    for scenario in scenarios:
        # operate on a shallow copy to avoid mutating caller
        pool_copy = ConstantProductPool(pool.config, PoolState(pool.state.reserve0, pool.state.reserve1))
        outcome = _scenario_outcome(pool_copy, scenario)
        stressed_depths[scenario.code] = outcome.liquidity_path
        il_by_scenario[scenario.code] = outcome.il
        recovery_steps[scenario.code] = outcome.recovery_steps
        if slippage_curve.size == 0:
            slippage_curve = outcome.slippage_curve

    return AMMStressMetrics(
        depth_curve=depth,
        slippage_curve=slippage_curve,
        stressed_depths=stressed_depths,
        il_by_scenario=il_by_scenario,
        recovery_steps=recovery_steps,
    )


__all__ = ["AMMStressMetrics", "get_stress_metrics"]
