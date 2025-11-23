"""Aggregate loss calculator with correlation-aware simulation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Mapping, Sequence

import numpy as np
from scipy.stats import norm

from pftoken.risk.utils import (
    AggregateRiskResult,
    TrancheRiskResult,
    _as_array,
    ensure_2d_losses,
    quantile,
    validate_spd_matrix,
)

LGDProvider = Callable[[str], float]


@dataclass(frozen=True)
class AggregateInputs:
    pd: Mapping[str, float]
    lgd: Mapping[str, float] | None
    ead: Mapping[str, float]
    correlation: np.ndarray
    simulations: int = 5000
    seed: int | None = None
    lgd_provider: LGDProvider | None = None


class AggregateRiskCalculator:
    """Simulate correlated tranche losses and summarize portfolio tails."""

    def __init__(self, tranche_names: Sequence[str]):
        if not tranche_names:
            raise ValueError("At least one tranche is required.")
        self.tranche_names = list(tranche_names)

    def _lgd_vector(self, lgd: Mapping[str, float] | Sequence[float] | None, lgd_provider: LGDProvider | None) -> np.ndarray:
        if lgd_provider is None and lgd is None:
            raise ValueError("LGD inputs or a provider must be supplied.")
        if lgd_provider is not None:
            provided = [lgd_provider(name) for name in self.tranche_names]
            return _as_array(provided, self.tranche_names)
        return _as_array(lgd or [], self.tranche_names)

    def simulate_losses(self, inputs: AggregateInputs) -> np.ndarray:
        """Generate correlated loss scenarios using a Gaussian copula."""

        pd_vec = _as_array(inputs.pd, self.tranche_names)
        ead_vec = _as_array(inputs.ead, self.tranche_names)
        lgd_vec = self._lgd_vector(inputs.lgd, inputs.lgd_provider)

        corr = validate_spd_matrix(inputs.correlation)
        rng = np.random.default_rng(inputs.seed)
        z = rng.standard_normal((inputs.simulations, len(self.tranche_names)))
        L = np.linalg.cholesky(corr)
        correlated = z @ L.T
        uniforms = norm.cdf(correlated)
        defaults = uniforms < pd_vec
        losses = defaults * ead_vec * lgd_vec
        return losses

    def summarize_portfolio(
        self,
        loss_scenarios: np.ndarray | Iterable[Iterable[float]],
        *,
        alpha_levels: Sequence[float] = (0.95, 0.99),
    ) -> AggregateRiskResult:
        """Aggregate portfolio loss metrics and per-tranche averages."""

        arr = ensure_2d_losses(loss_scenarios, expected_cols=len(self.tranche_names))
        portfolio_losses = arr.sum(axis=1)
        var_95 = quantile(portfolio_losses, alpha_levels[0]) if alpha_levels else 0.0
        var_99 = quantile(portfolio_losses, alpha_levels[-1]) if len(alpha_levels) > 1 else var_95
        tail_95 = portfolio_losses[portfolio_losses >= var_95]
        tail_99 = portfolio_losses[portfolio_losses >= var_99]
        cvar_95 = float(np.mean(tail_95)) if tail_95.size else 0.0
        cvar_99 = float(np.mean(tail_99)) if tail_99.size else 0.0
        mean_losses = {name: float(arr[:, idx].mean()) for idx, name in enumerate(self.tranche_names)}
        return AggregateRiskResult(
            portfolio_mean_loss=float(np.mean(portfolio_losses)),
            portfolio_var_95=var_95,
            portfolio_var_99=var_99,
            portfolio_cvar_95=cvar_95,
            portfolio_cvar_99=cvar_99,
            tranche_mean_losses=mean_losses,
        )

    def contribution_table(
        self,
        loss_scenarios: np.ndarray | Iterable[Iterable[float]],
    ) -> Dict[str, float]:
        """Share of total expected loss contributed by each tranche."""

        arr = ensure_2d_losses(loss_scenarios, expected_cols=len(self.tranche_names))
        total = float(np.sum(arr))
        if total == 0:
            return {name: 0.0 for name in self.tranche_names}
        contributions = np.sum(arr, axis=0) / total
        return {name: float(val) for name, val in zip(self.tranche_names, contributions)}


__all__ = ["AggregateRiskCalculator", "AggregateInputs"]
