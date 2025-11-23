"""Efficient frontier analysis for tranche weights."""

from __future__ import annotations

from typing import Dict, Iterable, Mapping, Sequence, TYPE_CHECKING

import numpy as np

from pftoken.risk.utils import FrontierPoint, ensure_2d_losses

if TYPE_CHECKING:
    from pftoken.pricing.wacd import WACDCalculator


class EfficientFrontierAnalysis:
    """Generate and evaluate tranche weight portfolios."""

    def __init__(self, tranche_names: Sequence[str]):
        if not tranche_names:
            raise ValueError("At least one tranche is required.")
        self.tranche_names = list(tranche_names)

    def _normalize(self, weights: np.ndarray) -> np.ndarray:
        weights = np.maximum(weights, 0.0)
        total = np.sum(weights)
        if total <= 0:
            raise ValueError("Weight vector cannot be all zeros.")
        return weights / total

    def sample_weights(self, *, num: int, seed: int | None = None) -> np.ndarray:
        """Sample weight vectors on the simplex using a Dirichlet draw."""

        rng = np.random.default_rng(seed)
        weights = rng.dirichlet(np.ones(len(self.tranche_names)), size=num)
        return weights

    def evaluate(
        self,
        weights: np.ndarray | Iterable[Iterable[float]],
        tranche_returns: Mapping[str, float],
        tranche_loss_scenarios: np.ndarray | Iterable[Iterable[float]],
        *,
        wacd_calc: "WACDCalculator" | None = None,
        risk_metric: str = "cvar",
        alpha: float = 0.95,
    ) -> Sequence[FrontierPoint]:
        """Compute risk/return for each weight vector."""

        weight_matrix = np.asarray(weights, dtype=float)
        if weight_matrix.ndim == 1:
            weight_matrix = weight_matrix.reshape(1, -1)
        if weight_matrix.shape[1] != len(self.tranche_names):
            raise ValueError("Weight vector length mismatch.")
        loss_matrix = ensure_2d_losses(tranche_loss_scenarios, expected_cols=len(self.tranche_names))
        tranche_return_vec = np.array([tranche_returns[name] for name in self.tranche_names], dtype=float)

        points: list[FrontierPoint] = []
        for row in weight_matrix:
            w = self._normalize(row)
            portfolio_losses = loss_matrix @ w
            expected_return = float(np.dot(w, tranche_return_vec))
            if risk_metric == "cvar":
                threshold = np.quantile(portfolio_losses, alpha)
                tail = portfolio_losses[portfolio_losses >= threshold]
                risk_value = float(np.mean(tail)) if tail.size else 0.0
            elif risk_metric == "var":
                risk_value = float(np.quantile(portfolio_losses, alpha))
            else:
                risk_value = float(np.std(portfolio_losses))
            wacd_value = None
            if wacd_calc is not None:
                try:
                    wacd_result = wacd_calc.compute_with_weights(
                        {name: float(val) for name, val in zip(self.tranche_names, w)},
                        apply_tokenized_deltas=True,
                    )
                    wacd_value = wacd_result.get("wacd_after_tax")
                except Exception:
                    wacd_value = None
            points.append(
                FrontierPoint(
                    weights={name: float(val) for name, val in zip(self.tranche_names, w)},
                    expected_return=expected_return,
                    risk=risk_value,
                    is_efficient=False,
                    wacd_after_tax=wacd_value,
                )
            )
        return self._mark_efficient(points)

    def _mark_efficient(self, points: Sequence[FrontierPoint]) -> Sequence[FrontierPoint]:
        """Mark portfolios that are not dominated (lower risk, higher return)."""

        efficient_flags = []
        for i, pt in enumerate(points):
            dominated = False
            for j, other in enumerate(points):
                if i == j:
                    continue
                if other.risk <= pt.risk and other.expected_return >= pt.expected_return:
                    if other.risk < pt.risk or other.expected_return > pt.expected_return:
                        dominated = True
                        break
            efficient_flags.append(not dominated)

        updated = []
        for pt, flag in zip(points, efficient_flags):
            updated.append(FrontierPoint(pt.weights, pt.expected_return, pt.risk, flag, pt.wacd_after_tax))
        return updated

    def mark_efficient_3d(self, points: Sequence[FrontierPoint]) -> Sequence[FrontierPoint]:
        """Mark portfolios Pareto-optimal across (risk ↓, return ↑, wacd ↓)."""

        efficient_flags = []
        for i, pt in enumerate(points):
            dominated = False
            for j, other in enumerate(points):
                if i == j:
                    continue
                # If either lacks WACD, fall back to 2D dominance
                if pt.wacd_after_tax is None or other.wacd_after_tax is None:
                    if other.risk <= pt.risk and other.expected_return >= pt.expected_return:
                        if other.risk < pt.risk or other.expected_return > pt.expected_return:
                            dominated = True
                            break
                    continue
                better_risk = other.risk <= pt.risk
                better_return = other.expected_return >= pt.expected_return
                better_wacd = other.wacd_after_tax <= pt.wacd_after_tax
                strictly_better = (
                    other.risk < pt.risk
                    or other.expected_return > pt.expected_return
                    or other.wacd_after_tax < pt.wacd_after_tax
                )
                if better_risk and better_return and better_wacd and strictly_better:
                    dominated = True
                    break
            efficient_flags.append(not dominated)

        updated = []
        for pt, flag in zip(points, efficient_flags):
            updated.append(FrontierPoint(pt.weights, pt.expected_return, pt.risk, flag, pt.wacd_after_tax))
        return updated


__all__ = ["EfficientFrontierAnalysis"]
