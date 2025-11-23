"""Pathwise Merton PD/LGD integration for Monte Carlo (WP-07 T-024)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, Sequence

import numpy as np
from scipy.stats import norm
import warnings

from pftoken.models.calibration import CalibrationSet


@dataclass(frozen=True)
class TranchePathMetrics:
    tranche: str
    pd: np.ndarray
    lgd: np.ndarray
    distance_to_default: np.ndarray


def compute_pathwise_pd_lgd(
    asset_values: np.ndarray,
    debt_by_tranche: Mapping[str, float],
    *,
    discount_rate: float,
    horizon_years: float,
    calibration: CalibrationSet,
) -> Dict[str, TranchePathMetrics]:
    """
    Vectorized Merton-style PD/LGD per tranche for each simulated asset value.

    Parameters
    ----------
    asset_values : np.ndarray
        Simulated enterprise values (shape: n_sims,).
    debt_by_tranche : mapping
        Outstanding debt per tranche (same units as asset_values).
    discount_rate : float
        Annual discount rate for drift term.
    horizon_years : float
        Time to maturity of the tranche (years).
    calibration : CalibrationSet
        Contains asset vol/recovery/pd_floor per tranche.
    """

    asset_values = np.asarray(asset_values, dtype=float)
    if asset_values.ndim != 1:
        raise ValueError("asset_values must be a 1D array of simulated enterprise values.")
    results: Dict[str, TranchePathMetrics] = {}

    # Sort tranches by seniority and compute cumulative debt barriers
    seniority_order = {"senior": 1, "mezzanine": 2, "subordinated": 3}
    sorted_tranches = sorted(
        debt_by_tranche.items(),
        key=lambda x: seniority_order.get(x[0].lower(), 99)
    )

    cumulative_debt = 0.0
    for tranche, tranche_debt in sorted_tranches:
        cumulative_debt += tranche_debt
        debt_barrier = cumulative_debt  # Use cumulative debt as barrier

        cal = calibration.params.get(tranche.lower())
        if cal is None:
            raise KeyError(f"Missing calibration for tranche '{tranche}'.")

        # Distance-to-default vectorized.
        drift = discount_rate - 0.5 * cal.asset_volatility**2
        numerator = np.log(np.maximum(asset_values, 1e-9) / debt_barrier) + (drift * horizon_years)
        denominator = cal.asset_volatility * np.sqrt(horizon_years)
        dd = numerator / np.where(denominator == 0, 1e-9, denominator)

        pd_path = np.maximum(norm.cdf(-dd), cal.pd_floor)
        lgd_path = np.full_like(pd_path, 1.0 - cal.recovery_rate)

        dd_min, dd_max = float(dd.min()), float(dd.max())
        if dd_max < 0:
            warnings.warn(f"All distance-to-default values < 0 for tranche '{tranche}'; assets below debt.")
        elif dd_min < 0 and dd_max > 3:
            warnings.warn(f"Wide DD dispersion for tranche '{tranche}' (min={dd_min:.2f}, max={dd_max:.2f}).")

        results[tranche] = TranchePathMetrics(
            tranche=tranche,
            pd=pd_path,
            lgd=lgd_path,
            distance_to_default=dd,
        )

    return results


def loss_paths_from_pd_lgd(
    pd_paths: Mapping[str, np.ndarray],
    lgd: Mapping[str, float] | Mapping[str, np.ndarray],
    ead: Mapping[str, float] | None = None,
    *,
    seed: int | None = None,
) -> tuple[Sequence[str], np.ndarray]:
    """Generate Monte Carlo loss scenarios using Bernoulli defaults."""

    tranche_names = list(pd_paths.keys())
    rng = np.random.default_rng(seed)
    n_sims = len(next(iter(pd_paths.values())))
    losses = np.zeros((n_sims, len(tranche_names)), dtype=float)
    for idx, name in enumerate(tranche_names):
        pd_arr = np.asarray(pd_paths[name], dtype=float)
        lgd_val = lgd[name]
        lgd_arr = np.asarray(lgd_val, dtype=float)
        if lgd_arr.ndim == 0:
            lgd_arr = np.full_like(pd_arr, lgd_arr)
        ead_val = 1.0 if ead is None else float(ead[name])
        defaults = rng.random(n_sims) < pd_arr
        losses[:, idx] = defaults * lgd_arr * ead_val
    return tranche_names, losses


__all__ = ["TranchePathMetrics", "compute_pathwise_pd_lgd", "loss_paths_from_pd_lgd"]
