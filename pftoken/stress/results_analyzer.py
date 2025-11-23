"""Stress results analyzer (WP-06 T-041)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

import numpy as np

from .stress_engine import StressRunResult


@dataclass(frozen=True)
class RankedScenario:
    code: str
    name: str
    metric: float
    delta: float


class StressResultsAnalyzer:
    """Aggregate and rank stress runs."""

    def rank_by_metric(
        self,
        results: Iterable[StressRunResult],
        *,
        metric: str,
        descending: bool = False,
    ) -> List[RankedScenario]:
        ranked: List[RankedScenario] = []
        for res in results:
            value = float(res.stressed_metrics.get(metric, np.nan))
            delta = float(res.deltas.get(metric, np.nan))
            ranked.append(RankedScenario(code=res.scenario.code, name=res.scenario.name, metric=value, delta=delta))
        ranked.sort(key=lambda r: r.metric, reverse=descending)
        return ranked

    def near_misses(
        self,
        results: Iterable[StressRunResult],
        *,
        metric: str,
        threshold: float,
        tolerance: float = 0.05,
    ) -> List[RankedScenario]:
        """Return scenarios within tolerance * threshold of breaching."""

        ranked = []
        upper = threshold * (1 + tolerance)
        lower = threshold * (1 - tolerance)
        for res in results:
            value = float(res.stressed_metrics.get(metric, np.nan))
            if lower <= value <= upper:
                ranked.append(
                    RankedScenario(
                        code=res.scenario.code,
                        name=res.scenario.name,
                        metric=value,
                        delta=float(res.deltas.get(metric, np.nan)),
                    )
                )
        ranked.sort(key=lambda r: abs(r.metric - threshold))
        return ranked


__all__ = ["StressResultsAnalyzer", "RankedScenario"]
