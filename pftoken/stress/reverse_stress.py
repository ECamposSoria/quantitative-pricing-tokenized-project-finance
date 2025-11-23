"""Reverse stress testing utilities (WP-06 T-042)."""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Callable, Dict, Mapping, Sequence

import numpy as np


EvaluateFn = Callable[[Mapping[str, float]], float]


@dataclass(frozen=True)
class ReverseStressResult:
    shocks: Dict[str, float]
    metric: float
    target: float


class ReverseStressTester:
    """Find minimum shocks that push the system below a target metric."""

    def __init__(self, *, tolerance: float = 1e-4, max_iter: int = 25):
        self.tolerance = tolerance
        self.max_iter = max_iter

    def find_breaking_point(
        self,
        evaluate: Callable[[float], float],
        *,
        target: float,
        low: float = 0.0,
        high: float = 1.0,
    ) -> ReverseStressResult:
        """1D binary search for minimal shock that breaches the target."""

        for _ in range(self.max_iter):
            mid = 0.5 * (low + high)
            metric = evaluate(mid)
            if metric <= target:
                high = mid
            else:
                low = mid
            if abs(high - low) < self.tolerance:
                break
        return ReverseStressResult(shocks={"shock": high}, metric=metric, target=target)

    def identify_minimal_fatal_combo(
        self,
        evaluate: EvaluateFn,
        *,
        shock_levels: Mapping[str, Sequence[float]],
        target: float,
    ) -> ReverseStressResult:
        """Grid-search minimal combo that breaches the target."""

        best: ReverseStressResult | None = None
        keys = list(shock_levels.keys())
        grids = [shock_levels[k] for k in keys]
        for combo in itertools.product(*grids):
            candidate = dict(zip(keys, combo))
            metric = evaluate(candidate)
            if metric <= target:
                weight = sum(abs(v) for v in candidate.values())
                if best is None or weight < sum(abs(v) for v in best.shocks.values()):
                    best = ReverseStressResult(shocks=candidate, metric=metric, target=target)
        if best is None:
            return ReverseStressResult(shocks={}, metric=float("inf"), target=target)
        return best

    def map_failure_surface(
        self,
        evaluate: EvaluateFn,
        *,
        shock_levels: Mapping[str, Sequence[float]],
        target: float,
    ) -> Dict[str, np.ndarray]:
        """Evaluate metric grid to visualize safe/unsafe regions."""

        results: Dict[str, np.ndarray] = {}
        for key, levels in shock_levels.items():
            values = []
            for level in levels:
                metric = evaluate({key: level})
                values.append(metric)
            results[key] = np.array(values)
        results["target"] = target
        return results


__all__ = ["ReverseStressTester", "ReverseStressResult"]
