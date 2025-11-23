"""Hybrid stress testing combining MC draws with deterministic shocks (T-043)."""

from __future__ import annotations

from copy import deepcopy
from typing import Dict, Iterable

import numpy as np

from pftoken.simulation.monte_carlo import MonteCarloResult
from .scenarios import StressScenario, StressShock


class HybridStressTester:
    """Apply stress scenarios directly to Monte Carlo draws."""

    def stress_conditional_mc(self, result: MonteCarloResult, scenario: StressScenario) -> MonteCarloResult:
        stressed = deepcopy(result)
        for shock in scenario.shocks:
            if shock.target in stressed.draws:
                stressed.draws[shock.target] = _apply_shock_array(stressed.draws[shock.target], shock)
            if shock.target in stressed.derived:
                stressed.derived[shock.target] = _apply_shock_array(stressed.derived[shock.target], shock)
        stressed.metadata = {**stressed.metadata, "stressed_scenario": scenario.code}
        return stressed

    def progressive_stress_mc(self, result: MonteCarloResult, scenarios: Iterable[StressScenario]) -> MonteCarloResult:
        stressed = result
        for scenario in scenarios:
            stressed = self.stress_conditional_mc(stressed, scenario)
        return stressed

    def variance_decomposition(self, base: MonteCarloResult, stressed: MonteCarloResult) -> Dict[str, float]:
        """Compare variance of draws before/after stress."""

        deltas: Dict[str, float] = {}
        for key, arr in base.draws.items():
            if key in stressed.draws:
                deltas[key] = float(np.var(stressed.draws[key]) - np.var(arr))
        return deltas


def _apply_shock_array(values: np.ndarray, shock: StressShock) -> np.ndarray:
    if shock.mode == "add":
        return values + shock.value
    if shock.mode == "mult":
        return values * (1 + shock.value)
    return values


__all__ = ["HybridStressTester"]
