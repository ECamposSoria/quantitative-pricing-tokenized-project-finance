"""Monte Carlo engine for WP-07 (T-021).

Uses correlated stochastic variables defined in the calibration payload to
produce vectorized simulation draws, with optional path-level processing via a
user-supplied callback.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterable, Mapping, MutableMapping, Sequence

import numpy as np
import pandas as pd

from pftoken.models.calibration import CalibrationSet
from .correlation import CorrelatedSampler
from .stochastic_vars import StochasticVariables


SimulationCallback = Callable[[Dict[str, np.ndarray]], Dict[str, np.ndarray]]


@dataclass(frozen=True)
class MonteCarloConfig:
    simulations: int
    seed: int | None = None
    antithetic: bool = False
    chunk_size: int | None = None
    variables: Sequence[str] | None = None


@dataclass
class MonteCarloResult:
    draws: Dict[str, np.ndarray]
    derived: Dict[str, np.ndarray] = field(default_factory=dict)
    seed: int | None = None
    metadata: Dict[str, object] = field(default_factory=dict)

    def summary(self, percentiles: Sequence[float] = (5, 50, 95)) -> Dict[str, Dict[str, object]]:
        """Return basic stats per variable."""

        summaries: Dict[str, Dict[str, object]] = {}
        for name, values in self.draws.items():
            summaries[name] = _summarize_array(values, percentiles)
        for name, values in self.derived.items():
            summaries[name] = _summarize_array(values, percentiles)
        return summaries

    def to_npz(self, path: Path | str) -> None:
        np.savez_compressed(path, **{**self.draws, **{f"derived_{k}": v for k, v in self.derived.items()}})

    def to_parquet(self, path: Path | str) -> None:
        flat: Dict[str, np.ndarray] = {}
        for k, v in self.draws.items():
            flat[k] = v.reshape(len(v), -1)[:, 0] if v.ndim > 1 else v
        for k, v in self.derived.items():
            flat[f"derived_{k}"] = v.reshape(len(v), -1)[:, 0] if v.ndim > 1 else v
        df = pd.DataFrame(flat)
        df.to_parquet(path, index=False)


class MonteCarloEngine:
    """Vectorized Monte Carlo engine with optional path callback."""

    def __init__(
        self,
        calibration: CalibrationSet,
        *,
        path_callback: SimulationCallback | None = None,
    ):
        self.calibration = calibration
        self.path_callback = path_callback
        self._has_correlation = calibration.correlation is not None
        self._sampler = (
            CorrelatedSampler(calibration)
            if self._has_correlation
            else StochasticVariables(calibration)
        )

    def run_simulation(self, config: MonteCarloConfig) -> MonteCarloResult:
        variables = list(config.variables) if config.variables else list(self._variable_names())
        chunk = config.chunk_size or config.simulations
        draws: Dict[str, np.ndarray] = {name: np.empty(config.simulations) for name in variables}
        derived: Dict[str, np.ndarray] = {}
        sampler = self._build_sampler(seed=config.seed)

        start = 0
        while start < config.simulations:
            end = min(start + chunk, config.simulations)
            size = end - start
            batch = self._sample_batch(variables, size, sampler, antithetic=config.antithetic)
            for name, values in batch.items():
                draws[name][start:end] = values

            if self.path_callback:
                derived_batch = self.path_callback(batch)
                for key, values in derived_batch.items():
                    if key not in derived:
                        derived[key] = np.empty((config.simulations, *values.shape[1:]))
                    derived[key][start:end] = values
            start = end

        metadata = {
            "simulations": config.simulations,
            "antithetic": config.antithetic,
            "variables": variables,
        }
        return MonteCarloResult(draws=draws, derived=derived, seed=config.seed, metadata=metadata)

    # ------------------------------------------------------------------ helpers
    def _build_sampler(self, *, seed: int | None):
        if self._has_correlation:
            return CorrelatedSampler(self.calibration, seed=seed)
        return StochasticVariables(self.calibration, seed=seed)

    def _sample_batch(self, variables: Sequence[str], size: int, sampler, *, antithetic: bool) -> Dict[str, np.ndarray]:
        if isinstance(sampler, CorrelatedSampler):
            results = sampler.sample(size, antithetic=antithetic)
            if missing := [v for v in variables if v not in results]:
                for name in missing:
                    results[name] = sampler.variables.sample(name, size, antithetic=antithetic)
            return {name: results[name] for name in variables}

        # Independent sampling path.
        return {name: sampler.sample(name, size, antithetic=antithetic) for name in variables}

    def _variable_names(self) -> Sequence[str]:
        if isinstance(self._sampler, CorrelatedSampler):
            return self._sampler.variables.names()
        return self._sampler.names()


def _summarize_array(values: np.ndarray, percentiles: Sequence[float]) -> Dict[str, object]:
    arr = np.asarray(values)
    axis = 0
    mean_val = np.mean(arr, axis=axis)
    std_val = np.std(arr, ddof=1, axis=axis)
    stats: Dict[str, object] = {
        "mean": float(mean_val) if np.isscalar(mean_val) else mean_val.tolist(),
        "std": float(std_val) if np.isscalar(std_val) else std_val.tolist(),
    }
    for p in percentiles:
        q = np.percentile(arr, p, axis=axis)
        stats[f"p{int(p)}"] = float(q) if np.isscalar(q) else q.tolist()
    min_val = np.min(arr, axis=axis)
    max_val = np.max(arr, axis=axis)
    stats["min"] = float(min_val) if np.isscalar(min_val) else min_val.tolist()
    stats["max"] = float(max_val) if np.isscalar(max_val) else max_val.tolist()
    return stats


__all__ = ["MonteCarloConfig", "MonteCarloEngine", "MonteCarloResult"]
