"""Stochastic variable generators (WP-07 T-022)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping

import numpy as np
from scipy.stats import beta as beta_dist
from scipy.stats import norm, poisson

from pftoken.models.calibration import CalibrationSet, RandomVariableConfig

DistributionName = str
def time_dependent_launch_risk(year: int, base_p: float = 0.07, decay_rate: float = 0.3, min_p: float = 0.01) -> float:
    """Launch failure probability decays with operational maturity."""
    return max(base_p * np.exp(-decay_rate * max(0, year - 1)), min_p)


@dataclass(frozen=True)
class SampleSummary:
    name: str
    mean: float
    std: float
    min: float
    max: float


class StochasticVariables:
    """Samples deterministic distributions defined in the calibration payload."""

    SUPPORTED = {"lognormal", "normal", "beta", "bernoulli", "poisson", "ou"}

    def __init__(self, calibration: CalibrationSet, *, seed: int | None = None):
        if not calibration.random_variables:
            raise ValueError("Calibration set does not contain random variables definitions.")
        self._rng = np.random.default_rng(seed)
        self._variables: Dict[str, RandomVariableConfig] = calibration.random_variables

    @property
    def rng(self) -> np.random.Generator:
        return self._rng

    def names(self) -> Iterable[str]:
        return self._variables.keys()

    def sample(self, name: str, size: int, *, antithetic: bool = False) -> np.ndarray:
        config = self._get_config(name)
        distribution = config.distribution
        if distribution not in self.SUPPORTED:
            raise ValueError(f"Unsupported distribution '{distribution}' for variable '{name}'.")
        sampler = getattr(self, f"_sample_{distribution}")
        return sampler(config, size, antithetic)

    def sample_many(self, names: Iterable[str], size: int, *, antithetic: bool = False) -> Dict[str, np.ndarray]:
        return {name: self.sample(name, size, antithetic=antithetic) for name in names}

    def describe(self, name: str, size: int = 5_000) -> SampleSummary:
        values = self.sample(name, size)
        return SampleSummary(
            name=name,
            mean=float(values.mean()),
            std=float(values.std(ddof=1)),
            min=float(values.min()),
            max=float(values.max()),
        )

    def transform_from_normal(self, name: str, standard_normals: np.ndarray) -> np.ndarray:
        """Map correlated standard-normal samples into the target distribution."""

        config = self._get_config(name)
        if config.distribution == "lognormal":
            mu = config.params.get("mu", 0.0)
            sigma = config.params.get("sigma", 0.1)
            return np.exp(mu + sigma * standard_normals)
        if config.distribution == "normal":
            mean = config.params.get("mean", 0.0)
            sigma = config.params.get("sigma", 1.0)
            return mean + sigma * standard_normals
        if config.distribution == "beta":
            alpha = config.params.get("alpha", 1.0)
            beta_param = config.params.get("beta", 1.0)
            uniforms = norm.cdf(standard_normals)
            uniforms = np.clip(uniforms, 1e-9, 1 - 1e-9)
            return beta_dist.ppf(uniforms, alpha, beta_param)
        if config.distribution == "bernoulli":
            probability = config.params.get("probability", 0.5)
            uniforms = norm.cdf(standard_normals)
            return (uniforms < probability).astype(int)
        raise ValueError(f"Variable '{name}' with distribution '{config.distribution}' does not support transform.")

    def sample_time_dependent(self, name: str, year: int, size: int) -> np.ndarray:
        """Sample variables with time-dependent parameters (e.g., launch risk decay)."""

        if name == "launch_failure":
            config = self._get_config(name)
            base_p = config.params.get("probability", 0.07)
            p = time_dependent_launch_risk(year, base_p=base_p)
            return self._rng.choice([0, 1], size=size, p=[1 - p, p])
        return self.sample(name, size)

    # --- Internal helpers -------------------------------------------------
    def _sample_lognormal(self, config: RandomVariableConfig, size: int, antithetic: bool) -> np.ndarray:
        z = self._standard_normals(size, antithetic)
        mu = config.params.get("mu", 0.0)
        sigma = config.params.get("sigma", 0.1)
        return np.exp(mu + sigma * z)

    def _sample_normal(self, config: RandomVariableConfig, size: int, antithetic: bool) -> np.ndarray:
        z = self._standard_normals(size, antithetic)
        mean = config.params.get("mean", 0.0)
        sigma = config.params.get("sigma", 1.0)
        return mean + sigma * z

    def _sample_beta(self, config: RandomVariableConfig, size: int, antithetic: bool) -> np.ndarray:
        alpha = config.params.get("alpha", 1.0)
        beta_param = config.params.get("beta", 1.0)
        uniforms = self._uniforms(size, antithetic)
        uniforms = np.clip(uniforms, 1e-9, 1 - 1e-9)
        return beta_dist.ppf(uniforms, alpha, beta_param)

    def _sample_bernoulli(self, config: RandomVariableConfig, size: int, antithetic: bool) -> np.ndarray:
        probability = config.params.get("probability", 0.5)
        trials = self._uniforms(size, antithetic)
        return (trials < probability).astype(int)

    def _sample_poisson(self, config: RandomVariableConfig, size: int, antithetic: bool) -> np.ndarray:
        lam = config.params.get("lambda", config.params.get("lam", 1.0))
        # antithetic not meaningful for Poisson; use direct sampling
        return self._rng.poisson(lam=lam, size=size)

    def _sample_ou(self, config: RandomVariableConfig, size: int, antithetic: bool) -> np.ndarray:
        theta = config.params.get("theta", 0.0)
        kappa = config.params.get("kappa", 0.5)
        sigma = config.params.get("sigma", 0.1)
        x0 = config.params.get("x0", theta)
        dt = config.params.get("dt", 1.0)
        horizon = int(config.params.get("horizon", 1))
        full_path = bool(int(config.params.get("return_path", 0)))

        if horizon <= 1:
            shocks = self._standard_normals(size, antithetic)
            variance = (sigma**2) * dt
            return x0 + theta * dt + np.sqrt(variance) * shocks

        values = np.empty((size, horizon), dtype=float)
        values[:, 0] = x0
        decay = np.exp(-kappa * dt)

        for step in range(1, horizon):
            shocks = self._standard_normals(size, antithetic)
            variance = (
                (sigma**2) / (2 * kappa) * (1 - np.exp(-2 * kappa * dt))
                if kappa != 0
                else (sigma**2) * dt
            )
            values[:, step] = (
                theta + (values[:, step - 1] - theta) * decay + np.sqrt(variance) * shocks
            )
        return values if full_path else values[:, -1]

    def _get_config(self, name: str) -> RandomVariableConfig:
        if name not in self._variables:
            raise KeyError(f"Unknown stochastic variable '{name}'.")
        return self._variables[name]

    def _standard_normals(self, size: int, antithetic: bool) -> np.ndarray:
        if not antithetic:
            return self._rng.standard_normal(size)
        half = (size + 1) // 2
        draws = self._rng.standard_normal(half)
        mirrored = np.concatenate([draws, -draws])[:size]
        return mirrored

    def _uniforms(self, size: int, antithetic: bool) -> np.ndarray:
        if not antithetic:
            return self._rng.random(size)
        half = (size + 1) // 2
        draws = self._rng.random(half)
        mirrored = np.concatenate([draws, 1.0 - draws])[:size]
        return mirrored


__all__ = ["SampleSummary", "StochasticVariables", "time_dependent_launch_risk"]
