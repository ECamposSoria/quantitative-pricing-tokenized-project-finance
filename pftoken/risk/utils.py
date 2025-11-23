"""Shared dataclasses and helpers for risk analytics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Iterable, Mapping, Sequence

import numpy as np


def _as_array(values: Mapping[str, float] | Sequence[float], names: Sequence[str]) -> np.ndarray:
    """Align a mapping/sequence to tranche order."""

    if isinstance(values, Mapping):
        return np.array([float(values[name]) for name in names], dtype=float)
    arr = np.asarray(values, dtype=float)
    if arr.shape[0] != len(names):
        raise ValueError(f"Expected {len(names)} entries, got {arr.shape[0]}")
    return arr


def ensure_2d_losses(losses: np.ndarray | Iterable[Iterable[float]], *, expected_cols: int) -> np.ndarray:
    """Validate/reshape loss scenarios to (n, tranches)."""

    arr = np.asarray(losses, dtype=float)
    if arr.ndim == 1:
        arr = arr.reshape(-1, expected_cols)
    if arr.ndim != 2:
        raise ValueError("Loss scenarios must be 2D.")
    if arr.shape[1] != expected_cols:
        raise ValueError(f"Loss scenarios must have {expected_cols} columns, got {arr.shape[1]}")
    return arr


def quantile(values: np.ndarray, q: float, *, method: str = "linear") -> float:
    """Wrapper over np.quantile with validation."""

    if not 0 <= q <= 1:
        raise ValueError("Quantile must be within [0, 1].")
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        raise ValueError("Cannot compute quantile of empty array.")
    return float(np.quantile(arr, q, method=method))


def validate_spd_matrix(matrix: np.ndarray, *, epsilon: float = 1e-8) -> np.ndarray:
    """Ensure symmetric positive definite/semi-definite by bumping the diagonal if needed."""

    arr = np.asarray(matrix, dtype=float)
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
        raise ValueError("Correlation matrix must be square.")
    if not np.allclose(arr, arr.T, atol=1e-8):
        raise ValueError("Correlation matrix must be symmetric.")
    eigvals = np.linalg.eigvalsh(arr)
    min_eig = float(np.min(eigvals))
    if min_eig < epsilon:
        bump = (-min_eig + epsilon)
        arr = arr + bump * np.eye(arr.shape[0])
    return arr


@dataclass(frozen=True)
class TrancheRiskResult:
    tranche: str
    el: float
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    marginal_contribution: float

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class TailFitResult:
    distribution: str  # "gpd" | "gev" | "empirical"
    params: Dict[str, float]
    ks_pvalue: float | None
    qq_residuals: np.ndarray

    def to_dict(self) -> Dict[str, float | None]:
        data = asdict(self)
        # Avoid returning large arrays in summaries
        data["qq_residuals"] = self.qq_residuals.tolist()
        return data


@dataclass(frozen=True)
class FrontierPoint:
    weights: Dict[str, float]
    expected_return: float
    risk: float
    is_efficient: bool
    wacd_after_tax: float | None = None

    def to_dict(self) -> Dict[str, float | Dict[str, float] | bool]:
        return asdict(self)


@dataclass(frozen=True)
class AggregateRiskResult:
    portfolio_mean_loss: float
    portfolio_var_95: float
    portfolio_var_99: float
    portfolio_cvar_95: float
    portfolio_cvar_99: float
    tranche_mean_losses: Dict[str, float]

    def to_dict(self) -> Dict[str, float | Dict[str, float]]:
        return asdict(self)


__all__ = [
    "AggregateRiskResult",
    "FrontierPoint",
    "TailFitResult",
    "TrancheRiskResult",
    "ensure_2d_losses",
    "quantile",
    "validate_spd_matrix",
    "_as_array",
]
