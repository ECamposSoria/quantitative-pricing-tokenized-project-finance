"""Stress testing engine (WP-06 T-040/T-041)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Mapping

import numpy as np

from .scenarios import StressScenario, StressShock


Runner = Callable[[Mapping[str, object]], Dict[str, float]]


@dataclass(frozen=True)
class StressRunResult:
    scenario: StressScenario
    stressed_inputs: Dict[str, object]
    stressed_metrics: Dict[str, float]
    deltas: Dict[str, float]


class StressTestEngine:
    """Apply deterministic shocks and compute delta vs baseline metrics."""

    def __init__(self, baseline_inputs: Mapping[str, object], baseline_metrics: Mapping[str, float]):
        self.baseline_inputs = dict(baseline_inputs)
        self.baseline_metrics = dict(baseline_metrics)

    def apply_stress_scenario(self, scenario: StressScenario) -> Dict[str, object]:
        stressed = dict(self.baseline_inputs)
        for shock in scenario.shocks:
            if shock.target not in stressed:
                continue
            stressed[shock.target] = self._apply_shock(stressed[shock.target], shock)
        return stressed

    def run_stressed_simulation(self, scenario: StressScenario, runner: Runner) -> StressRunResult:
        stressed_inputs = self.apply_stress_scenario(scenario)
        stressed_metrics = runner(stressed_inputs)
        deltas = self.calculate_stress_metrics(stressed_metrics)
        return StressRunResult(
            scenario=scenario,
            stressed_inputs=stressed_inputs,
            stressed_metrics=stressed_metrics,
            deltas=deltas,
        )

    def calculate_stress_metrics(self, stressed_metrics: Mapping[str, float]) -> Dict[str, float]:
        deltas: Dict[str, float] = {}
        for key, baseline_value in self.baseline_metrics.items():
            stressed_value = stressed_metrics.get(key, np.nan)
            deltas[key] = float(stressed_value - baseline_value)
        return deltas

    # ------------------------------------------------------------------ helpers
    def _apply_shock(self, value: object, shock: StressShock) -> object:
        if isinstance(value, (int, float)):
            return _apply_numeric(value, shock)
        if isinstance(value, np.ndarray):
            return _apply_numeric(value, shock)
        return value


def _apply_numeric(value, shock: StressShock):
    if shock.mode == "add":
        return value + shock.value
    if shock.mode == "mult":
        return value * (1 + shock.value)
    raise ValueError(f"Unsupported shock mode '{shock.mode}'")


__all__ = ["StressTestEngine", "StressRunResult"]
