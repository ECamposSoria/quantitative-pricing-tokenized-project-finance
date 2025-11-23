"""Default flag generation for Monte Carlo paths (WP-07 T-025)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class DefaultFlags:
    technical: np.ndarray
    payment: np.ndarray
    insolvency: np.ndarray
    first_breach_period: np.ndarray

    def any_default(self) -> np.ndarray:
        return self.technical | self.payment | self.insolvency


class DefaultDetector:
    """Classify defaults based on ratio breaches and asset coverage."""

    def __init__(
        self,
        *,
        dscr_threshold: float = 1.0,
        llcr_threshold: float | None = None,
        asset_coverage_threshold: float = 1.0,
    ):
        self.dscr_threshold = dscr_threshold
        self.llcr_threshold = llcr_threshold
        self.asset_coverage_threshold = asset_coverage_threshold

    def classify(
        self,
        dscr_paths: np.ndarray,
        *,
        llcr_paths: np.ndarray | None = None,
        asset_values: np.ndarray | None = None,
        debt_outstanding: float | None = None,
    ) -> DefaultFlags:
        """Return boolean flags per simulation."""

        dscr_arr = np.asarray(dscr_paths, dtype=float)
        if dscr_arr.ndim != 2:
            raise ValueError("dscr_paths must be 2D (n_sims, n_periods).")
        technical = dscr_arr < self.dscr_threshold
        payment = dscr_arr < 1.0

        if llcr_paths is not None and self.llcr_threshold is not None:
            llcr_arr = np.asarray(llcr_paths, dtype=float)
            if llcr_arr.shape != dscr_arr.shape:
                raise ValueError("llcr_paths must match dscr_paths shape.")
            technical |= llcr_arr < self.llcr_threshold
            payment |= llcr_arr < 1.0

        insolvency = np.zeros(dscr_arr.shape[0], dtype=bool)
        if asset_values is not None and debt_outstanding is not None:
            asset_arr = np.asarray(asset_values, dtype=float)
            insolvency = asset_arr < (self.asset_coverage_threshold * debt_outstanding)

        first_breach_period = _first_true_index(payment | technical)
        return DefaultFlags(
            technical=technical.any(axis=1),
            payment=payment.any(axis=1),
            insolvency=insolvency,
            first_breach_period=first_breach_period,
        )


def _first_true_index(flags: np.ndarray) -> np.ndarray:
    """Return index of first True per row, -1 if none."""
    if flags.ndim == 1:
        return np.where(flags, 0, -1)
    idx = np.argmax(flags, axis=1)
    no_breach = ~flags.any(axis=1)
    idx[no_breach] = -1
    return idx


__all__ = ["DefaultDetector", "DefaultFlags"]
