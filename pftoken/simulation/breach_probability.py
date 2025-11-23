"""Breach probability estimators (WP-07 T-030)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class BreachCurves:
    breach_probability: np.ndarray
    survival: np.ndarray
    hazard: np.ndarray


class BreachProbabilityAnalyzer:
    """Compute breach probabilities, survival, and hazard rates."""

    def compute(self, breach_flags: np.ndarray) -> BreachCurves:
        flags = np.asarray(breach_flags, dtype=bool)
        if flags.ndim != 2:
            raise ValueError("breach_flags must be 2D (n_sims, n_periods).")

        n_sims, n_periods = flags.shape
        breach_probability = flags.mean(axis=0)

        survival = np.ones(n_periods, dtype=float)
        hazard = np.zeros(n_periods, dtype=float)
        alive = np.ones(n_sims, dtype=bool)
        for t in range(n_periods):
            new_breaches = flags[:, t] & alive
            alive &= ~flags[:, t]
            survivors = max(alive.sum(), 1)
            hazard[t] = new_breaches.sum() / survivors
            survival[t] = alive.mean()

        return BreachCurves(breach_probability=breach_probability, survival=survival, hazard=hazard)


__all__ = ["BreachProbabilityAnalyzer", "BreachCurves"]
