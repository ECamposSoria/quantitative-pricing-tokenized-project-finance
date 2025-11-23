"""Ratio distribution helpers for Monte Carlo fan charts (WP-07 T-029)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class RatioSummary:
    percentiles: Dict[int, np.ndarray]
    breach_rate: np.ndarray
    headroom: np.ndarray


class RatioDistributions:
    """Compute DSCR/LLCR fan chart data and breach rates."""

    def __init__(self, percentiles: Iterable[int] = (5, 25, 50, 75, 95)):
        self.percentiles = tuple(percentiles)

    def summarize(
        self,
        ratio_paths: np.ndarray,
        *,
        threshold: float | Sequence[float] | np.ndarray,
    ) -> RatioSummary:
        arr = np.asarray(ratio_paths, dtype=float)
        if arr.ndim != 2:
            raise ValueError("ratio_paths must be 2D (n_sims, n_periods).")
        threshold_arr = self._threshold_array(threshold, arr.shape[1])

        percentiles: Dict[int, np.ndarray] = {}
        for p in self.percentiles:
            percentiles[p] = np.percentile(arr, p, axis=0)

        breach_rate = (arr < threshold_arr).mean(axis=0)
        headroom = np.mean(arr - threshold_arr, axis=0)
        return RatioSummary(percentiles=percentiles, breach_rate=breach_rate, headroom=headroom)

    def _threshold_array(self, threshold: float | Sequence[float] | np.ndarray, periods: int) -> np.ndarray:
        threshold_arr = np.asarray(threshold, dtype=float)
        if threshold_arr.ndim == 0:
            threshold_arr = np.full(periods, float(threshold_arr))
        if threshold_arr.shape[0] != periods:
            raise ValueError("threshold length must equal number of periods.")
        return threshold_arr


__all__ = ["RatioDistributions", "RatioSummary"]
