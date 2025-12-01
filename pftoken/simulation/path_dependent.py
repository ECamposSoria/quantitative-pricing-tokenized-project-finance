"""First-passage default detection for path-dependent Merton-style models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class PathDependentConfig:
    enable_path_default: bool = False
    barrier_calibration_mode: str = "match_terminal_pd"
    barrier_ratio: float = 1.0

    @classmethod
    def from_dict(cls, raw: dict | None) -> "PathDependentConfig":
        if not raw:
            return cls()
        return cls(
            enable_path_default=bool(raw.get("enable_path_default", False)),
            barrier_calibration_mode=str(raw.get("barrier_calibration_mode", "match_terminal_pd")),
            barrier_ratio=float(raw.get("barrier_ratio", 1.0)),
        )


def evaluate_first_passage(
    asset_paths: np.ndarray,
    debt_schedule: Iterable[float],
    config: PathDependentConfig,
) -> np.ndarray:
    """
    Evaluate first-passage defaults: mark a path as defaulted if V_t < barrier_t at any t.

    Parameters
    ----------
    asset_paths : np.ndarray
        Shape (n_sims, n_periods) asset values (e.g., present value of remaining CFADS).
    debt_schedule : iterable of float
        Debt barriers per period (same units as asset_paths).
    config : PathDependentConfig
        Toggles and barrier calibration settings. If enable_path_default is False, returns zeros.

    Returns
    -------
    np.ndarray
        Boolean array (n_sims,) indicating whether a first-passage default occurred.
    """

    if not config.enable_path_default:
        return np.zeros(asset_paths.shape[0], dtype=bool)

    asset_arr = np.asarray(asset_paths, dtype=float)
    if asset_arr.ndim != 2:
        raise ValueError("asset_paths must have shape (n_sims, n_periods).")

    debt_arr = np.asarray(list(debt_schedule), dtype=float)
    if debt_arr.ndim != 1:
        raise ValueError("debt_schedule must be 1D over periods.")

    if asset_arr.shape[1] != debt_arr.shape[0]:
        raise ValueError(
            f"asset_paths periods ({asset_arr.shape[1]}) must match debt_schedule length ({debt_arr.shape[0]})."
        )

    barrier = config.barrier_ratio * debt_arr[None, :]
    crossed = asset_arr < barrier
    return np.any(crossed, axis=1)


__all__ = ["PathDependentConfig", "evaluate_first_passage"]
