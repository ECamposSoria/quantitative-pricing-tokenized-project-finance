"""Loader for deterministic placeholder calibration parameters (T-047)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Mapping, Optional

import yaml

DEFAULT_CALIBRATION_PATH = Path("data/derived/leo_iot/stochastic_params.yaml")


@dataclass(frozen=True)
class TrancheCalibration:
    asset_volatility: float
    spread_bps: float
    recovery_rate: float
    pd_floor: float

    def __post_init__(self) -> None:
        if not 0 < self.asset_volatility < 1:
            raise ValueError("asset_volatility must be within (0, 1)")
        if not 0 <= self.recovery_rate <= 1:
            raise ValueError("recovery_rate must be within [0, 1]")
        if self.spread_bps <= 0:
            raise ValueError("spread_bps must be positive")
        if not 0 <= self.pd_floor < 1:
            raise ValueError("pd_floor must be within [0, 1)")


@dataclass(frozen=True)
class CalibrationSet:
    version: str
    as_of: str
    params: Dict[str, TrancheCalibration]
    path: Path
    random_variables: Dict[str, "RandomVariableConfig"] = field(default_factory=dict)
    correlation: Optional["CorrelationConfig"] = None
    path_dependent: Optional[Dict[str, float]] = None
    regime_switching: Optional[Dict[str, object]] = None


@dataclass(frozen=True)
class RandomVariableConfig:
    name: str
    distribution: str
    params: Dict[str, float]


@dataclass(frozen=True)
class CorrelationConfig:
    variables: list[str]
    matrix: list[list[float]]


def load_placeholder_calibration(path: str | Path | None = None) -> CalibrationSet:
    """Load deterministic calibration params, deferring real T-047 scope."""

    calibration_path = Path(path) if path else DEFAULT_CALIBRATION_PATH
    if not calibration_path.exists():
        raise FileNotFoundError(
            f"Calibration file {calibration_path} not found. "
            "Generate it via scripts/export_excel_validation.py once placeholders are refreshed."
        )

    with calibration_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)

    tranche_params: Dict[str, TrancheCalibration] = {}
    for tranche_name, raw in payload.get("params", {}).items():
        tranche_params[tranche_name.lower()] = TrancheCalibration(
            asset_volatility=float(raw["asset_volatility"]),
            spread_bps=float(raw["spread_bps"]),
            recovery_rate=float(raw["recovery_rate"]),
            pd_floor=float(raw["pd_floor"]),
        )

    random_variables = _parse_random_variables(payload.get("random_variables", {}))
    correlation = _parse_correlation(payload.get("correlation"))
    path_dependent = _parse_path_dependent(payload.get("path_dependent"))
    regime_switching = _parse_regime_switching(payload.get("regime_switching"))

    return CalibrationSet(
        version=str(payload.get("version", "0.0.0")),
        as_of=str(payload.get("as_of", "unknown")),
        params=tranche_params,
        path=calibration_path,
        random_variables=random_variables,
        correlation=correlation,
        path_dependent=path_dependent,
        regime_switching=regime_switching,
    )


def _parse_random_variables(raw: Mapping[str, Mapping[str, float]]) -> Dict[str, RandomVariableConfig]:
    configs: Dict[str, RandomVariableConfig] = {}
    for name, config in raw.items():
        distribution = str(config.get("distribution", "")).lower()
        params: Dict[str, float] = {}
        for key, value in config.items():
            if key == "distribution":
                continue
            try:
                params[key] = float(value)
            except (TypeError, ValueError):
                continue
        configs[name] = RandomVariableConfig(name=name, distribution=distribution, params=params)
    return configs


def _parse_correlation(raw: Mapping[str, object] | None) -> Optional[CorrelationConfig]:
    if not raw:
        return None
    variables = [str(var) for var in raw.get("variables", [])]
    matrix = [
        [float(value) for value in row]
        for row in raw.get("matrix", [])
    ]
    return CorrelationConfig(variables=variables, matrix=matrix)


def _parse_path_dependent(raw: Mapping[str, object] | None) -> Optional[Dict[str, float]]:
    if not raw:
        return None
    return {
        "enable_path_default": bool(raw.get("enable_path_default", False)),
        "barrier_calibration_mode": str(raw.get("barrier_calibration_mode", "match_terminal_pd")),
        "barrier_ratio": float(raw.get("barrier_ratio", 1.0)),
    }


def _parse_regime_switching(raw: Mapping[str, object] | None) -> Optional[Dict[str, object]]:
    if not raw:
        return None
    parsed: Dict[str, object] = {
        "enable_regime_switching": bool(raw.get("enable_regime_switching", False)),
        "enable_regime_lgd": bool(raw.get("enable_regime_lgd", False)),
        "enable_regime_spreads": bool(raw.get("enable_regime_spreads", False)),
        "n_regimes": int(raw.get("n_regimes", 2)),
    }
    transition = raw.get("transition_matrix")
    if transition is not None:
        parsed["transition_matrix"] = [[float(v) for v in row] for row in transition]
    regimes = raw.get("regimes") or raw.get("regime_params") or {}
    parsed_regimes: Dict[int, Dict[str, float]] = {}
    for key, val in regimes.items():
        idx = int(key)
        parsed_regimes[idx] = {
            "mu": float(val.get("mu", 0.0)),
            "sigma": float(val.get("sigma", 0.0)),
            "recovery_adj": float(val.get("recovery_adj", 0.0)),
            "spread_lift_bps": float(val.get("spread_lift_bps", 0.0)),
        }
    parsed["regimes"] = parsed_regimes
    return parsed


__all__ = [
    "CalibrationSet",
    "CorrelationConfig",
    "RandomVariableConfig",
    "TrancheCalibration",
    "load_placeholder_calibration",
]
