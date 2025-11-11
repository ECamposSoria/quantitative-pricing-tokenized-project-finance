"""Correlation utilities for stochastic variables (WP-07 T-023)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Sequence

import numpy as np

from pftoken.models.calibration import CalibrationSet, CorrelationConfig
from .stochastic_vars import StochasticVariables


@dataclass(frozen=True)
class CorrelationMetadata:
    variables: Sequence[str]
    matrix: np.ndarray


class CorrelationMatrix:
    """Validate and apply correlation structures."""

    def __init__(self, config: CorrelationConfig, *, tolerance: float = 1e-9):
        self.variables = list(config.variables)
        self.matrix = np.array(config.matrix, dtype=float)
        self.tolerance = tolerance
        self._validate()
        self._cholesky = np.linalg.cholesky(self.matrix + tolerance * np.eye(self.matrix.shape[0]))

    def generate_correlated_normals(self, rng: np.random.Generator, size: int) -> np.ndarray:
        base = rng.standard_normal((size, len(self.variables)))
        return base @ self._cholesky.T

    def _validate(self) -> None:
        if self.matrix.shape[0] != self.matrix.shape[1]:
            raise ValueError("Correlation matrix must be square.")
        if len(self.variables) != self.matrix.shape[0]:
            raise ValueError("Number of variables must match matrix dimensions.")
        if not np.allclose(self.matrix, self.matrix.T, atol=1e-8):
            raise ValueError("Correlation matrix must be symmetric.")
        eigvals = np.linalg.eigvals(self.matrix)
        if np.any(eigvals < -self.tolerance):
            raise ValueError("Correlation matrix must be positive semi-definite.")

    def metadata(self) -> CorrelationMetadata:
        return CorrelationMetadata(variables=self.variables, matrix=self.matrix)


class CorrelatedSampler:
    """Combine StochasticVariables with a CorrelationMatrix to produce joint samples."""

    def __init__(
        self,
        calibration: CalibrationSet,
        *,
        seed: int | None = None,
    ):
        if calibration.correlation is None:
            raise ValueError("Calibration set does not include correlation data.")
        self.variables = StochasticVariables(calibration, seed=seed)
        self.correlation = CorrelationMatrix(calibration.correlation)
        self._ensure_variables_present()

    def sample(self, size: int) -> Dict[str, np.ndarray]:
        normals = self.correlation.generate_correlated_normals(self.variables.rng, size)
        results: Dict[str, np.ndarray] = {}
        for idx, name in enumerate(self.correlation.variables):
            results[name] = self.variables.transform_from_normal(name, normals[:, idx])
        return results

    def _ensure_variables_present(self) -> None:
        available = set(self.variables.names())
        missing = [name for name in self.correlation.variables if name not in available]
        if missing:
            raise KeyError(f"Correlation matrix references unknown variables: {missing}")


__all__ = ["CorrelationMatrix", "CorrelatedSampler", "CorrelationMetadata"]
