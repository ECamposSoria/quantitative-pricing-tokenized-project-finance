"""Herfindahl-Hirschman index helpers for concentration analysis."""

from __future__ import annotations

from typing import Dict, Iterable, Mapping, Sequence

import numpy as np


class RiskConcentrationAnalysis:
    """Compute HHI and equivalent number of homogeneous tranches."""

    def __init__(self, tranche_names: Sequence[str]):
        if not tranche_names:
            raise ValueError("At least one tranche is required.")
        self.tranche_names = list(tranche_names)

    @staticmethod
    def _hhi_from_shares(shares: np.ndarray) -> float:
        shares = np.asarray(shares, dtype=float)
        total = shares.sum()
        if total == 0:
            return 0.0
        normalized = shares / total
        return float(np.sum(normalized**2))

    def exposures_hhi(self, exposures: Mapping[str, float]) -> Dict[str, float]:
        """HHI based on current exposures."""

        shares = np.array([exposures.get(name, 0.0) for name in self.tranche_names], dtype=float)
        hhi = self._hhi_from_shares(shares)
        equivalent_n = 1.0 / hhi if hhi > 0 else float("inf")
        return {"hhi": hhi, "equivalent_n": equivalent_n}

    def losses_hhi(self, loss_scenarios: Iterable[Iterable[float]]) -> Dict[str, float]:
        """HHI based on average loss contributions."""

        arr = np.asarray(list(loss_scenarios), dtype=float)
        if arr.ndim != 2 or arr.shape[1] != len(self.tranche_names):
            raise ValueError("Loss scenarios must match tranche dimensionality.")
        mean_losses = arr.mean(axis=0)
        hhi = self._hhi_from_shares(mean_losses)
        equivalent_n = 1.0 / hhi if hhi > 0 else float("inf")
        return {"hhi": hhi, "equivalent_n": equivalent_n}


__all__ = ["RiskConcentrationAnalysis"]
