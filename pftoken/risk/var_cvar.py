"""Value-at-Risk and CVaR utilities (empirical + EVT-ready)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
from scipy import stats

from pftoken.risk.utils import TailFitResult, ensure_2d_losses, quantile


@dataclass(frozen=True)
class EmpiricalRisk:
    var_levels: dict
    cvar_levels: dict


class TailRiskAnalyzer:
    """Compute empirical VaR/CVaR and optional EVT-based tails."""

    def __init__(self, *, min_tail_samples: int = 50):
        self.min_tail_samples = min_tail_samples

    # ------------------------------------------------------------ empirical
    def empirical_var(
        self, losses: np.ndarray | Iterable[float], levels: Sequence[float] = (0.95, 0.99)
    ) -> dict[float, float]:
        arr = np.asarray(losses, dtype=float)
        return {level: quantile(arr, level) for level in levels}

    def empirical_cvar(
        self, losses: np.ndarray | Iterable[float], levels: Sequence[float] = (0.95, 0.99)
    ) -> dict[float, float]:
        arr = np.asarray(losses, dtype=float)
        cvars: dict[float, float] = {}
        for level in levels:
            threshold = quantile(arr, level)
            tail = arr[arr >= threshold]
            cvars[level] = float(np.mean(tail)) if tail.size else 0.0
        return cvars

    def analyze_empirical(
        self,
        losses: np.ndarray | Iterable[float] | np.ndarray,
        levels: Sequence[float] = (0.95, 0.99),
    ) -> EmpiricalRisk:
        arr = np.asarray(losses, dtype=float)
        return EmpiricalRisk(var_levels=self.empirical_var(arr, levels), cvar_levels=self.empirical_cvar(arr, levels))

    # ------------------------------------------------------------ EVT fits
    def fit_gpd(
        self,
        losses: np.ndarray | Iterable[float],
        *,
        threshold_quantile: float = 0.95,
        confidence_levels: Sequence[float] = (0.99,),
    ) -> TailFitResult:
        arr = np.asarray(losses, dtype=float)
        threshold = quantile(arr, threshold_quantile)
        tail = arr[arr > threshold]
        if tail.size < self.min_tail_samples:
            return TailFitResult("empirical", {"threshold": threshold}, ks_pvalue=None, qq_residuals=np.array([]))
        # Fit GPD on excesses
        excess = tail - threshold
        c, loc, scale = stats.genpareto.fit(excess, floc=0)  # fix loc at 0 for stability
        fitted = stats.genpareto(c, loc=loc, scale=scale)
        # KS test on excesses
        ks_stat, ks_pvalue = stats.kstest(excess, fitted.cdf)
        # QQ residuals for diagnostics
        probs = np.linspace(0.01, 0.99, min(50, excess.size))
        modeled = fitted.ppf(probs)
        empirical = np.quantile(excess, probs)
        qq_residuals = empirical - modeled
        params = {"shape": float(c), "loc": float(loc), "scale": float(scale), "threshold": float(threshold)}
        # Optional: estimate extreme quantiles
        for level in confidence_levels:
            params[f"var_{int(level*100)}"] = float(threshold + fitted.ppf(level))
        return TailFitResult("gpd", params, ks_pvalue=float(ks_pvalue), qq_residuals=qq_residuals)

    def fit_gev(
        self,
        losses: np.ndarray | Iterable[float],
        *,
        confidence_levels: Sequence[float] = (0.99,),
    ) -> TailFitResult:
        arr = np.asarray(losses, dtype=float)
        if arr.size < self.min_tail_samples:
            return TailFitResult("empirical", {"note": "insufficient sample"}, ks_pvalue=None, qq_residuals=np.array([]))
        shape, loc, scale = stats.genextreme.fit(arr)
        fitted = stats.genextreme(shape, loc=loc, scale=scale)
        ks_stat, ks_pvalue = stats.kstest(arr, fitted.cdf)
        probs = np.linspace(0.01, 0.99, min(50, arr.size))
        modeled = fitted.ppf(probs)
        empirical = np.quantile(arr, probs)
        qq_residuals = empirical - modeled
        params = {"shape": float(shape), "loc": float(loc), "scale": float(scale)}
        for level in confidence_levels:
            params[f"var_{int(level*100)}"] = float(fitted.ppf(level))
        return TailFitResult("gev", params, ks_pvalue=float(ks_pvalue), qq_residuals=qq_residuals)

    # ------------------------------------------------------------ matrix helpers
    def columnwise_empirical(
        self,
        losses: np.ndarray | Iterable[Iterable[float]],
        *,
        levels: Sequence[float] = (0.95, 0.99),
    ) -> dict[int, EmpiricalRisk]:
        arr = ensure_2d_losses(losses, expected_cols=len(losses[0]) if isinstance(losses, list) else losses.shape[1])
        results: dict[int, EmpiricalRisk] = {}
        for idx in range(arr.shape[1]):
            results[idx] = self.analyze_empirical(arr[:, idx], levels)
        return results


__all__ = ["TailRiskAnalyzer", "EmpiricalRisk"]
