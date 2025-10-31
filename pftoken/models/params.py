"""
Typed parameter models for the project finance / AMM simulator.

The module uses Pydantic v2 models to provide strict validation, convenient
serialization helpers, and CSV loading utilities tailored to the LEO IoT
dataset provided in `data/input/leo_iot/`.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Iterable, Mapping, Sequence, Tuple

import numpy as np
import pandas as pd
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PositiveFloat,
    PositiveInt,
    field_validator,
    model_validator,
)
from pydantic.types import NonNegativeFloat


class FinancialBasics(BaseModel):
    """Core financial configuration for the deterministic base case."""

    model_config = ConfigDict(validate_assignment=True)

    initial_capex: PositiveFloat
    rcapex_per_cycle: PositiveFloat
    rcapex_cycle_years: PositiveInt
    opex_ratio: float = Field(..., ge=0.0, le=1.0)
    opex_growth_rate: float = Field(..., ge=-1.0)
    tax_rate: float = Field(..., ge=0.0, le=1.0)
    horizon_years: PositiveInt
    periods_per_year: PositiveInt
    working_capital_pct: float = Field(..., ge=0.0, le=1.0)


class DebtTranche(BaseModel):
    """Single debt tranche specification."""

    model_config = ConfigDict(validate_assignment=True)

    name: str
    notional: PositiveFloat
    interest_rate: PositiveFloat
    rate_spread: NonNegativeFloat
    tenor_years: PositiveFloat = Field(..., gt=0.0)
    grace_period_years: NonNegativeFloat
    priority: PositiveInt


class DebtStructure(BaseModel):
    """Complete debt structure with validation on relative weights."""

    model_config = ConfigDict(validate_assignment=True)

    tranches: Sequence[DebtTranche]

    @field_validator("tranches")
    @classmethod
    def ensure_tranches(cls, value: Sequence[DebtTranche]) -> Sequence[DebtTranche]:
        if not value:
            raise ValueError("At least one debt tranche must be provided.")
        return value

    @model_validator(mode="after")
    def check_weights(self) -> "DebtStructure":
        notions = [tranche.notional for tranche in self.tranches]
        total = sum(notions)
        if total <= 0:
            raise ValueError("Total debt notional must be positive.")
        weights = [notional / total for notional in notions]
        if not math.isclose(sum(weights), 1.0, rel_tol=1e-6):
            raise ValueError("Debt tranche weights must sum to 1.0.")
        return self

    def weights(self) -> Tuple[float, ...]:
        """Return debt weights by notional share (guaranteed to sum to one)."""
        total = sum(tranche.notional for tranche in self.tranches)
        return tuple(tranche.notional / total for tranche in self.tranches)


class OperationalParams(BaseModel):
    """Operational drivers for the LEO constellation."""

    model_config = ConfigDict(validate_assignment=True)

    satellites: PositiveInt
    satellite_life_years: PositiveInt
    base_arpu: PositiveFloat
    arpu_growth_rate: float = Field(..., ge=-1.0)
    iot_device_growth_rate: float = Field(..., ge=0.0)
    initial_devices: PositiveInt


class RateCurveConfig(BaseModel):
    """Reference rate curve configuration."""

    model_config = ConfigDict(validate_assignment=True)

    base_rate: float = Field(..., ge=0.0)
    spreads: Dict[str, float]
    volatility: float = Field(..., ge=0.0)

    @field_validator("spreads")
    @classmethod
    def spreads_non_negative(cls, value: Dict[str, float]) -> Dict[str, float]:
        for name, spread in value.items():
            if spread < 0:
                raise ValueError(f"Spread for {name} must be non-negative.")
        return value


class MonteCarloConfig(BaseModel):
    """Specifies stochastic simulation settings."""

    model_config = ConfigDict(validate_assignment=True)

    simulations: PositiveInt
    volatilities: Dict[str, PositiveFloat]
    correlation_matrix: Tuple[Tuple[float, ...], ...]
    seeds: Dict[str, int]

    @field_validator("correlation_matrix")
    @classmethod
    def validate_correlation_matrix(
        cls,
        value: Iterable[Iterable[float]],
    ) -> Tuple[Tuple[float, ...], ...]:
        arr = np.asarray(value, dtype=float)
        if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
            raise ValueError("Correlation matrix must be square.")
        if not np.allclose(arr, arr.T, atol=1e-8):
            raise ValueError("Correlation matrix must be symmetric.")
        if not np.allclose(np.diag(arr), 1.0, atol=1e-6):
            raise ValueError("Correlation matrix diagonal entries must be 1.")
        return tuple(tuple(float(x) for x in row) for row in arr)

    @model_validator(mode="after")
    def dimension_checks(self) -> "MonteCarloConfig":
        matrix = np.asarray(self.correlation_matrix, dtype=float)
        vol_size = len(self.volatilities)
        if matrix.shape[0] != vol_size:
            raise ValueError(
                "Correlation matrix dimension must match number of volatility factors."
            )
        eigenvalues = np.linalg.eigvalsh(matrix)
        if np.any(eigenvalues < -1e-8):
            raise ValueError("Correlation matrix must be positive semi-definite.")
        return self


class ReserveAccounts(BaseModel):
    """Targets for the DSRA and MRA reserve accounts."""

    model_config = ConfigDict(validate_assignment=True)

    dsra_months: PositiveInt
    mra_target_pct: float = Field(..., ge=0.0, le=1.0)


class CovenantThresholds(BaseModel):
    """Financial covenant thresholds required by the structure."""

    model_config = ConfigDict(validate_assignment=True)

    min_dscr: float = Field(..., gt=0.0)
    min_llcr: float = Field(..., gt=0.0)


class ProjectParameters(BaseModel):
    """
    Aggregates all validated data required by the deterministic model.

    Use `from_directory` to hydrate the model from the provided CSV inputs.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

    financials: FinancialBasics
    debt: DebtStructure
    operational: OperationalParams
    rate_curve: RateCurveConfig
    monte_carlo: MonteCarloConfig
    reserves: ReserveAccounts
    covenants: CovenantThresholds
    timeline_years: Tuple[int, ...]
    debt_service_schedule: pd.DataFrame
    rcapex_schedule: pd.DataFrame

    @field_validator("debt_service_schedule", "rcapex_schedule")
    @classmethod
    def ensure_dataframe(cls, value: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(value, pd.DataFrame):
            raise TypeError("Expected pandas DataFrame.")
        return value.copy()

    def to_dict(self) -> Dict[str, object]:
        """Serialize the parameters to a Python dictionary."""
        return self.model_dump(mode="python")

    def manual_validate(self) -> None:
        """Run additional ad-hoc validations."""
        schedule_years = set(self.debt_service_schedule["year"].unique())
        if not schedule_years.issubset(set(self.timeline_years)):
            raise ValueError("Debt service schedule extends beyond defined timeline.")

    @model_validator(mode="after")
    def _run_manual_checks(self) -> "ProjectParameters":
        self.manual_validate()
        return self

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "ProjectParameters":
        """Hydrate the model from a nested dictionary (will be validated)."""
        return cls.model_validate(payload)

    @classmethod
    def from_directory(cls, base_path: str | Path) -> "ProjectParameters":
        """Load parameters from the canonical CSV inputs."""
        base = Path(base_path)
        params_csv = base / "project_params.csv"
        tranches_csv = base / "tranches.csv"
        rcapex_csv = base / "rcapex_schedule.csv"
        debt_sched_csv = base / "debt_schedule.csv"

        if not params_csv.exists():
            raise FileNotFoundError(params_csv)
        if not tranches_csv.exists():
            raise FileNotFoundError(tranches_csv)
        if not rcapex_csv.exists():
            raise FileNotFoundError(rcapex_csv)
        if not debt_sched_csv.exists():
            raise FileNotFoundError(debt_sched_csv)

        param_map = cls._load_param_map(params_csv)

        financials = FinancialBasics(
            initial_capex=float(param_map["initial_capex_total"]),
            rcapex_per_cycle=float(param_map["rcapex_amount"]) * 1_000_000.0,
            rcapex_cycle_years=int(float(param_map["rcapex_cycle_years"])),
            opex_ratio=float(param_map["opex_ratio_revenue"]),
            opex_growth_rate=float(param_map["opex_growth_rate"]),
            tax_rate=float(param_map["tax_rate_corporate"]),
            horizon_years=int(float(param_map["analysis_horizon_years"])),
            periods_per_year=int(float(param_map["periods_per_year"])),
            working_capital_pct=float(param_map["working_capital_pct_revenue"]),
        )

        tranches_df = pd.read_csv(tranches_csv)
        debt_tranches = cls._build_debt_tranches(tranches_df, financials, param_map)
        debt_structure = DebtStructure(tranches=debt_tranches)

        operational = OperationalParams(
            satellites=int(float(param_map["num_satellites_initial"])),
            satellite_life_years=int(float(param_map["satellite_life_years"])),
            base_arpu=float(param_map["base_arpu_per_year"]),
            arpu_growth_rate=float(param_map["arpu_growth_rate"]),
            iot_device_growth_rate=float(param_map["iot_device_growth_rate"]),
            initial_devices=int(float(param_map["initial_iot_devices"])),
        )

        spreads = {
            "senior": float(param_map["spread_senior"]),
            "mezzanine": float(param_map["spread_mezz"]),
            "subordinated": float(param_map["spread_sub"]),
        }
        rate_curve = RateCurveConfig(
            base_rate=float(param_map["base_discount_rate"]),
            spreads=spreads,
            volatility=float(param_map["rate_volatility"]),
        )

        volatilities = {
            "revenue": float(param_map["vol_revenue"]),
            "opex": float(param_map["vol_opex"]),
            "devices": float(param_map["vol_devices"]),
            "rates": float(param_map["vol_rates"]),
        }
        corr_level = float(param_map["correlation_reduction_governance"])
        corr_matrix = cls._build_correlation_matrix(len(volatilities), corr_level)
        monte_carlo = MonteCarloConfig(
            simulations=int(float(param_map["monte_carlo_simulations"])),
            volatilities=volatilities,
            correlation_matrix=corr_matrix,
            seeds={
                "core": int(float(param_map["mc_seed_core"])),
                "rates": int(float(param_map["mc_seed_rates"])),
            },
        )

        reserves = ReserveAccounts(
            dsra_months=int(float(param_map["dsra_months_cover"])),
            mra_target_pct=float(param_map["mra_target_pct_next_rcapex"]),
        )

        covenants = CovenantThresholds(
            min_dscr=float(param_map["min_dscr_covenant"]),
            min_llcr=float(param_map["min_llcr_covenant"]),
        )

        timeline = tuple(
            range(1, financials.horizon_years + 1)
        )
        debt_schedule = pd.read_csv(debt_sched_csv)
        rcapex_schedule = pd.read_csv(rcapex_csv)

        model = cls(
            financials=financials,
            debt=debt_structure,
            operational=operational,
            rate_curve=rate_curve,
            monte_carlo=monte_carlo,
            reserves=reserves,
            covenants=covenants,
            timeline_years=timeline,
            debt_service_schedule=debt_schedule,
            rcapex_schedule=rcapex_schedule,
        )
        return model

    @staticmethod
    def _load_param_map(csv_path: Path) -> Dict[str, str]:
        df = pd.read_csv(csv_path)
        if "param" not in df.columns or "value" not in df.columns:
            raise ValueError(f"Unexpected schema in {csv_path}")
        return {row.param: str(row.value) for row in df.itertuples(index=False)}

    @staticmethod
    def _build_debt_tranches(
        df: pd.DataFrame,
        financials: FinancialBasics,
        param_map: Mapping[str, str],
    ) -> Tuple[DebtTranche, ...]:
        base_rate = float(param_map["base_discount_rate"])
        records = []
        for row in df.itertuples(index=False):
            if getattr(row, "tranche_name") == "equity":
                continue
            notional = float(getattr(row, "initial_principal"))
            spread_bps = float(getattr(row, "spread_bps"))
            spread = spread_bps / 10_000.0
            tenor_years = float(getattr(row, "maturity_period")) / financials.periods_per_year
            grace_years = float(getattr(row, "grace_period_periods")) / financials.periods_per_year
            tranche = DebtTranche(
                name=getattr(row, "tranche_name"),
                notional=notional,
                interest_rate=base_rate + spread,
                rate_spread=spread,
                tenor_years=tenor_years,
                grace_period_years=grace_years,
                priority=int(getattr(row, "priority_level")),
            )
            records.append(tranche)
        if not records:
            raise ValueError("No debt tranches found in tranches.csv")
        return tuple(records)

    @staticmethod
    def _build_correlation_matrix(size: int, off_diag: float) -> Tuple[Tuple[float, ...], ...]:
        matrix = []
        for i in range(size):
            row = []
            for j in range(size):
                row.append(1.0 if i == j else off_diag)
            matrix.append(tuple(row))
        return tuple(matrix)


__all__ = [
    "ProjectParameters",
    "FinancialBasics",
    "DebtStructure",
    "DebtTranche",
    "OperationalParams",
    "RateCurveConfig",
    "MonteCarloConfig",
    "ReserveAccounts",
    "CovenantThresholds",
]
