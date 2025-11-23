"""Credit risk metrics for tranche-level EL/VaR/CVaR."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Sequence

import numpy as np

from pftoken.risk.utils import (
    TrancheRiskResult,
    _as_array,
    ensure_2d_losses,
    quantile,
)


@dataclass(frozen=True)
class RiskInputs:
    """Container for PD/LGD/EAD inputs."""

    pd: Mapping[str, float]
    lgd: Mapping[str, float]
    ead: Mapping[str, float]
    loss_scenarios: np.ndarray | None = None
    simulations: int = 5000
    seed: int | None = None


class RiskMetricsCalculator:
    """Compute per-tranche expected loss and tail metrics."""

    def __init__(self, tranche_names: Sequence[str]):
        if not tranche_names:
            raise ValueError("At least one tranche is required.")
        self.tranche_names = list(tranche_names)

    # ------------------------------------------------------------------ helpers
    def _build_losses_from_pd_lgd(
        self,
        pd: Mapping[str, float] | Sequence[float],
        lgd: Mapping[str, float] | Sequence[float],
        ead: Mapping[str, float] | Sequence[float] | None,
        *,
        size: int,
        seed: int | None = None,
    ) -> np.ndarray:
        """Generate synthetic independent losses using Bernoulli defaults."""

        rng = np.random.default_rng(seed)
        pd_arr = _as_array(pd, self.tranche_names)
        lgd_arr = _as_array(lgd, self.tranche_names)
        ead_arr = _as_array(ead if ead is not None else [1.0] * len(self.tranche_names), self.tranche_names)
        defaults = rng.random((size, len(self.tranche_names))) < pd_arr
        return defaults * ead_arr * lgd_arr

    def _per_tranche_var(self, losses: np.ndarray, alpha: float) -> Dict[str, float]:
        arr = ensure_2d_losses(losses, expected_cols=len(self.tranche_names))
        return {
            name: quantile(arr[:, idx], alpha)
            for idx, name in enumerate(self.tranche_names)
        }

    def _per_tranche_cvar(self, losses: np.ndarray, alpha: float) -> Dict[str, float]:
        arr = ensure_2d_losses(losses, expected_cols=len(self.tranche_names))
        results: Dict[str, float] = {}
        for idx, name in enumerate(self.tranche_names):
            threshold = quantile(arr[:, idx], alpha)
            tail = arr[:, idx][arr[:, idx] >= threshold]
            results[name] = float(np.mean(tail)) if tail.size else 0.0
        return results

    # ------------------------------------------------------------------ public
    def calculate_expected_loss(
        self,
        pd: Mapping[str, float] | Sequence[float],
        lgd: Mapping[str, float] | Sequence[float],
        ead: Mapping[str, float] | Sequence[float] | None = None,
    ) -> Dict[str, float]:
        """Return EL = PD × LGD × EAD per tranche."""

        pd_arr = _as_array(pd, self.tranche_names)
        lgd_arr = _as_array(lgd, self.tranche_names)
        ead_arr = _as_array(ead if ead is not None else [1.0] * len(self.tranche_names), self.tranche_names)
        values = pd_arr * lgd_arr * ead_arr
        return {name: float(val) for name, val in zip(self.tranche_names, values)}

    def calculate_var(
        self,
        loss_scenarios: np.ndarray | Iterable[Iterable[float]],
        *,
        alpha: float = 0.95,
    ) -> Dict[str, float]:
        """Empirical per-tranche VaR."""

        return self._per_tranche_var(loss_scenarios, alpha)

    def calculate_cvar(
        self,
        loss_scenarios: np.ndarray | Iterable[Iterable[float]],
        *,
        alpha: float = 0.95,
    ) -> Dict[str, float]:
        """Empirical per-tranche CVaR (mean of tail)."""

        return self._per_tranche_cvar(loss_scenarios, alpha)

    def calculate_marginal_risk(
        self,
        loss_scenarios: np.ndarray | Iterable[Iterable[float]],
        *,
        alpha: float = 0.95,
    ) -> Dict[str, float]:
        """Approximate marginal contribution via tail expectation."""

        arr = ensure_2d_losses(loss_scenarios, expected_cols=len(self.tranche_names))
        portfolio = np.sum(arr, axis=1)
        threshold = quantile(portfolio, alpha)
        tail_mask = portfolio >= threshold
        if not np.any(tail_mask):
            return {name: 0.0 for name in self.tranche_names}
        tail_losses = arr[tail_mask]
        contributions = tail_losses.mean(axis=0)
        return {name: float(val) for name, val in zip(self.tranche_names, contributions)}

    def tranche_results(
        self,
        inputs: RiskInputs,
        *,
        alpha_levels: Sequence[float] = (0.95, 0.99),
    ) -> Sequence[TrancheRiskResult]:
        """Build structured risk metrics for each tranche."""

        loss_scenarios = inputs.loss_scenarios
        if loss_scenarios is None:
            loss_scenarios = self._build_losses_from_pd_lgd(
                inputs.pd, inputs.lgd, inputs.ead, size=inputs.simulations, seed=inputs.seed
            )

        var_results = {alpha: self._per_tranche_var(loss_scenarios, alpha) for alpha in alpha_levels}
        cvar_results = {alpha: self._per_tranche_cvar(loss_scenarios, alpha) for alpha in alpha_levels}
        marginal = self.calculate_marginal_risk(loss_scenarios, alpha=min(alpha_levels) if alpha_levels else 0.95)
        el = self.calculate_expected_loss(inputs.pd, inputs.lgd, inputs.ead)

        results: list[TrancheRiskResult] = []
        for name in self.tranche_names:
            results.append(
                TrancheRiskResult(
                    tranche=name,
                    el=el[name],
                    var_95=var_results.get(0.95, {}).get(name, 0.0),
                    var_99=var_results.get(0.99, {}).get(name, 0.0),
                    cvar_95=cvar_results.get(0.95, {}).get(name, 0.0),
                    cvar_99=cvar_results.get(0.99, {}).get(name, 0.0),
                    marginal_contribution=marginal.get(name, 0.0),
                )
            )
        return results


__all__ = ["RiskMetricsCalculator", "RiskInputs"]
