"""Almgren-Chriss style convergence and sizing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class ConvergenceResult:
    trajectory: np.ndarray
    execution_cost: float
    spreads: np.ndarray
    realized_spread_reduction: float


class AlmgrenChrissEngine:
    def __init__(self, eta: float, gamma: float, sigma: float, lambda_risk: float):
        """
        eta: temporary impact coefficient
        gamma: permanent impact coefficient
        sigma: volatility
        lambda_risk: risk aversion parameter
        """
        if eta < 0 or gamma < 0 or sigma < 0 or lambda_risk < 0:
            raise ValueError("Parameters must be non-negative.")
        self.eta = eta
        self.gamma = gamma
        self.sigma = sigma
        self.lambda_risk = lambda_risk

    def optimal_trajectory(self, total_size: float, time_horizon: float, n_steps: int) -> np.ndarray:
        """Compute an even-split schedule scaled by risk aversion (simplified AC)."""
        if total_size <= 0:
            raise ValueError("total_size must be positive.")
        if n_steps <= 0:
            raise ValueError("n_steps must be positive.")
        base = total_size / n_steps
        decay = np.exp(-self.lambda_risk * np.linspace(0, time_horizon, n_steps))
        weights = decay / decay.sum()
        return weights * total_size

    def execution_cost(self, trajectory: np.ndarray, prices: np.ndarray) -> float:
        """Realized cost including impact; simplified AC linear/quadratic terms."""
        if trajectory.shape != prices.shape:
            raise ValueError("trajectory and prices must align.")
        temp = self.eta * np.sum(np.square(trajectory))
        perm = 0.5 * self.gamma * np.square(trajectory.sum())
        price_term = float(np.dot(trajectory, prices))
        return float(price_term + temp + perm)

    def simulate_convergence(
        self,
        pool,
        reference_prices: np.ndarray,
        capital_limit: float,
        alpha: float = 0.1,
    ) -> ConvergenceResult:
        """
        Multi-step arb simulation with impact-aware sizing (simplified).
        """
        if reference_prices.size == 0:
            raise ValueError("reference_prices cannot be empty.")
        pool_price_fn = getattr(pool, "price", None)
        pool_price = pool_price_fn() if callable(pool_price_fn) else reference_prices[0]
        spreads = reference_prices - pool_price

        liquidity = getattr(pool, "active_liquidity", lambda: None)()
        liquidity = liquidity if liquidity is not None and liquidity > 0 else 1.0
        size = min(capital_limit, alpha * liquidity * max(abs(spreads[0]), 1e-6))

        trajectory = self.optimal_trajectory(size, time_horizon=1.0, n_steps=reference_prices.size)
        cost = self.execution_cost(trajectory, reference_prices)
        realized_reduction = spreads[0] - spreads[-1]
        return ConvergenceResult(
            trajectory=trajectory,
            execution_cost=cost,
            spreads=spreads,
            realized_spread_reduction=realized_reduction,
        )

    def convergence_half_life(self, spread_history: Iterable[float]) -> float:
        """Time to 50% spread reduction assuming exponential decay."""
        spreads = np.asarray(list(spread_history), dtype=float)
        if spreads.size == 0:
            raise ValueError("spread_history cannot be empty.")
        start = spreads[0]
        target = 0.5 * start
        diffs = np.abs(spreads - target)
        return float(np.argmin(diffs))


__all__ = ["AlmgrenChrissEngine", "ConvergenceResult"]
