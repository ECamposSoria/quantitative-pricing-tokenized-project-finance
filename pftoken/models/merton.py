"""Deterministic Merton-style credit metrics with placeholder calibration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping

import numpy as np
from scipy.stats import norm

from .calibration import CalibrationSet, load_placeholder_calibration
from .params import DebtTrancheParams


def implied_asset_value(cfads_path: np.ndarray, discount_rate: float) -> float:
    """Approximate enterprise value as PV of future CFADS."""

    periods = np.arange(1, len(cfads_path) + 1)
    disc = 1.0 / (1.0 + discount_rate) ** periods
    return float(np.sum(cfads_path * disc))


def distance_to_default(
    asset_value: float,
    debt_outstanding: float,
    discount_rate: float,
    asset_volatility: float,
    horizon_years: float,
) -> float:
    """Classical KMV distance-to-default metric."""

    if asset_value <= 0 or debt_outstanding <= 0 or asset_volatility <= 0:
        return float("-inf")
    numerator = np.log(asset_value / debt_outstanding) + (
        (discount_rate - 0.5 * asset_volatility**2) * horizon_years
    )
    denominator = asset_volatility * np.sqrt(horizon_years)
    return numerator / denominator


@dataclass(frozen=True)
class MertonResult:
    tranche: str
    pd: float
    lgd: float
    expected_loss: float
    distance_to_default: float
    asset_volatility: float
    recovery_rate: float


class MertonModel:
    """Vectorized PD/LGD/EL calculator using placeholder calibration."""

    def __init__(
        self,
        cfads_vector: Mapping[int, float],
        tranches: Iterable[DebtTrancheParams],
        *,
        discount_rate: float,
        calibration: CalibrationSet | None = None,
    ):
        self.cfads_vector = dict(sorted(cfads_vector.items()))
        self.tranches = list(tranches)
        self.discount_rate = discount_rate
        self.calibration = calibration or load_placeholder_calibration()
        self._cfads_array = np.array([self.cfads_vector[year] for year in self.cfads_vector], dtype=float)

    def run(self) -> Dict[str, MertonResult]:
        asset_value = implied_asset_value(self._cfads_array, self.discount_rate)
        horizon = len(self._cfads_array)
        results: Dict[str, MertonResult] = {}

        ordered_tranches = sorted(self.tranches, key=lambda t: t.priority_level)
        prev_pd = 0.0
        for tranche in ordered_tranches:
            cal = self._calibration_for_tranche(tranche.name)
            debt = tranche.initial_principal / 1_000_000.0
            dd = distance_to_default(asset_value, debt, self.discount_rate, cal.asset_volatility, horizon)
            pd = max(norm.cdf(-dd), cal.pd_floor)
            if pd < prev_pd:
                pd = min(0.999, prev_pd + 1e-4)
            prev_pd = pd
            lgd = 1.0 - cal.recovery_rate
            el = pd * lgd
            results[tranche.name] = MertonResult(
                tranche=tranche.name,
                pd=pd,
                lgd=lgd,
                expected_loss=el,
                distance_to_default=dd,
                asset_volatility=cal.asset_volatility,
                recovery_rate=cal.recovery_rate,
            )
        return results

    def _calibration_for_tranche(self, tranche_name: str):
        key = tranche_name.lower()
        if key not in self.calibration.params:
            raise KeyError(f"Missing calibration for tranche '{tranche_name}'")
        return self.calibration.params[key]


__all__ = [
    "MertonModel",
    "MertonResult",
    "distance_to_default",
    "implied_asset_value",
]
