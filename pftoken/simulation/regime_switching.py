"""Regime-switching utilities for Monte Carlo asset paths and LGD/spread adjustments."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable

import numpy as np


@dataclass(frozen=True)
class RegimeParams:
    mu: float
    sigma: float
    recovery_adj: float = 0.0
    spread_lift_bps: float = 0.0


@dataclass(frozen=True)
class RegimeConfig:
    enable_regime_switching: bool = False
    enable_regime_lgd: bool = False
    enable_regime_spreads: bool = False
    n_regimes: int = 2
    transition_matrix: np.ndarray | None = None
    regime_params: Dict[int, RegimeParams] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict | None) -> "RegimeConfig":
        if not raw:
            return cls()

        n_regimes = int(raw.get("n_regimes", 2))
        matrix_raw = raw.get("transition_matrix")
        matrix = None
        if matrix_raw is not None:
            matrix = np.asarray(matrix_raw, dtype=float)

        regimes_raw = raw.get("regimes", {}) or raw.get("regime_params", {})
        regime_params: Dict[int, RegimeParams] = {}
        for key, val in regimes_raw.items():
            idx = int(key)
            regime_params[idx] = RegimeParams(
                mu=float(val.get("mu", 0.0)),
                sigma=float(val.get("sigma", 0.0)),
                recovery_adj=float(val.get("recovery_adj", 0.0)),
                spread_lift_bps=float(val.get("spread_lift_bps", 0.0)),
            )

        return cls(
            enable_regime_switching=bool(raw.get("enable_regime_switching", False)),
            enable_regime_lgd=bool(raw.get("enable_regime_lgd", False)),
            enable_regime_spreads=bool(raw.get("enable_regime_spreads", False)),
            n_regimes=n_regimes,
            transition_matrix=matrix,
            regime_params=regime_params,
        )

    def validate(self) -> None:
        if not self.enable_regime_switching:
            return
        if self.transition_matrix is None:
            raise ValueError("transition_matrix is required when regime switching is enabled.")
        if self.transition_matrix.shape != (self.n_regimes, self.n_regimes):
            raise ValueError("transition_matrix must have shape (n_regimes, n_regimes).")
        row_sums = np.sum(self.transition_matrix, axis=1)
        if not np.allclose(row_sums, 1.0, atol=1e-6):
            raise ValueError("Each row of transition_matrix must sum to 1.")
        for idx in range(self.n_regimes):
            if idx not in self.regime_params:
                raise ValueError(f"Missing regime parameters for regime index {idx}.")


class RegimeSwitchingProcess:
    """Simple Markov chain regime simulator with per-regime parameters."""

    def __init__(self, config: RegimeConfig, *, seed: int | None = None):
        self.config = config
        self.config.validate()
        self.rng = np.random.default_rng(seed)

    def simulate_regimes(self, n_sims: int, n_periods: int) -> np.ndarray:
        """
        Simulate regime indices over time.

        Returns
        -------
        np.ndarray
            Shape (n_sims, n_periods) with integer regime indices.
        """

        if not self.config.enable_regime_switching:
            return np.zeros((n_sims, n_periods), dtype=int)

        matrix = self.config.transition_matrix
        assert matrix is not None  # validated above
        regimes = np.zeros((n_sims, n_periods), dtype=int)
        if n_periods == 0:
            return regimes

        # Start in regime 0 by default (can be extended to use an initial distribution).
        regimes[:, 0] = 0
        for t in range(1, n_periods):
            prev = regimes[:, t - 1]
            next_states = np.empty_like(prev)
            for state in range(self.config.n_regimes):
                mask = prev == state
                if not np.any(mask):
                    continue
                probs = matrix[state]
                draws = self.rng.random(np.sum(mask))
                cumulative = np.cumsum(probs)
                next_states[mask] = np.searchsorted(cumulative, draws)
            regimes[:, t] = next_states
        return regimes

    def get_params_by_path(self, regime_paths: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Map regime indices to parameter arrays per path and period.

        Returns
        -------
        dict
            Keys: mu, sigma, recovery_adj, spread_lift_bps. Each shape (n_sims, n_periods).
        """

        params = {
            "mu": np.zeros_like(regime_paths, dtype=float),
            "sigma": np.zeros_like(regime_paths, dtype=float),
            "recovery_adj": np.zeros_like(regime_paths, dtype=float),
            "spread_lift_bps": np.zeros_like(regime_paths, dtype=float),
        }
        for idx, rp in self.config.regime_params.items():
            mask = regime_paths == idx
            params["mu"][mask] = rp.mu
            params["sigma"][mask] = rp.sigma
            params["recovery_adj"][mask] = rp.recovery_adj
            params["spread_lift_bps"][mask] = rp.spread_lift_bps
        return params


__all__ = ["RegimeConfig", "RegimeParams", "RegimeSwitchingProcess"]
