"""Structured parameter loading for the LEO IoT dataset (WP-02)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence

import pandas as pd

REQUIRED_PROJECT_PARAMS = {
    "analysis_horizon_years",
    "tenor_years",
    "grace_period_years",
    "ramping_period_months",
    "periods_per_year",
    "tax_rate_corporate",
    "min_dscr_covenant",
    "min_llcr_covenant",
    "dscr_default_trigger",
    "dscr_grace_threshold",
    "base_rate_reference",
    "spread_senior",
    "spread_mezz",
    "spread_sub",
    "target_dscr_years_5_10",
    "dsra_months_cover",
    "mra_target_pct_next_rcapex",
}


@dataclass(frozen=True)
class ProjectParams:
    """Immutable project-level parameters required by WP-02."""

    analysis_horizon_years: int
    tenor_years: int
    grace_period_years: int
    ramping_period_months: int
    periods_per_year: int
    tax_rate_corporate: float
    min_dscr_covenant: float
    min_llcr_covenant: float
    dscr_default_trigger: float
    dscr_grace_threshold: float
    base_rate_reference: float
    spread_senior: float
    spread_mezz: float
    spread_sub: float
    target_dscr_years_5_10: float
    dsra_months_cover: int
    mra_target_pct_next_rcapex: float

    def __post_init__(self) -> None:
        if self.analysis_horizon_years <= 0:
            raise ValueError("analysis_horizon_years must be positive")
        if self.tenor_years <= 0:
            raise ValueError("tenor_years must be positive")
        if self.grace_period_years < 0:
            raise ValueError("grace_period_years cannot be negative")
        if self.ramping_period_months < 0:
            raise ValueError("ramping_period_months cannot be negative")
        if self.periods_per_year <= 0:
            raise ValueError("periods_per_year must be positive")
        for label, value in (
            ("tax_rate_corporate", self.tax_rate_corporate),
            ("min_dscr_covenant", self.min_dscr_covenant),
            ("min_llcr_covenant", self.min_llcr_covenant),
            ("dscr_default_trigger", self.dscr_default_trigger),
            ("dscr_grace_threshold", self.dscr_grace_threshold),
            ("base_rate_reference", self.base_rate_reference),
            ("target_dscr_years_5_10", self.target_dscr_years_5_10),
            ("mra_target_pct_next_rcapex", self.mra_target_pct_next_rcapex),
        ):
            if value < 0:
                raise ValueError(f"{label} must be non-negative")
        if not (0 <= self.spread_senior <= 1):
            raise ValueError("spread_senior must be within [0, 1]")
        if not (0 <= self.spread_mezz <= 1):
            raise ValueError("spread_mezz must be within [0, 1]")
        if not (0 <= self.spread_sub <= 1):
            raise ValueError("spread_sub must be within [0, 1]")

    @property
    def grace_period_months(self) -> int:
        return self.grace_period_years * 12

    @property
    def ramping_period_years(self) -> float:
        return self.ramping_period_months / 12.0


@dataclass(frozen=True)
class DebtTrancheParams:
    """Debt tranche configuration extracted from `tranches.csv`."""

    name: str
    priority_level: int
    initial_principal: float
    rate_base_type: str
    base_rate: float
    spread_bps: int
    grace_period_years: int
    tenor_years: int
    amortization_style: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Tranche name cannot be empty")
        if self.priority_level < 1:
            raise ValueError("priority_level must be >= 1")
        if self.initial_principal <= 0:
            raise ValueError("initial_principal must be positive")
        if self.base_rate < 0:
            raise ValueError("base_rate must be non-negative")
        if self.spread_bps < 0:
            raise ValueError("spread_bps must be non-negative")
        if self.grace_period_years < 0:
            raise ValueError("grace_period_years cannot be negative")
        if self.tenor_years <= 0:
            raise ValueError("tenor_years must be positive")

    @property
    def coupon_rate(self) -> float:
        return self.base_rate + self.spread_bps / 10_000.0


@dataclass(frozen=True)
class CFADSProjectionParams:
    """Row-wise CFADS projection sourced from revenue_projection.csv."""

    rows: List[Dict[str, float]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.rows:
            raise ValueError("CFADS projection cannot be empty")
        required = {
            "year",
            "revenue_gross",
            "opex",
            "maintenance_opex",
            "working_cap_change",
            "tax_paid",
            "capex",
            "rcapex",
            "cfads",
        }
        for row in self.rows:
            missing = required - row.keys()
            if missing:
                raise ValueError(f"Missing columns in CFADS row: {missing}")

    @property
    def years(self) -> List[int]:
        return [int(row["year"]) for row in self.rows]

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows)

    def cfads_by_year(self) -> Dict[int, float]:
        return {int(row["year"]): float(row["cfads"]) for row in self.rows}


class ProjectParameters:
    """Lightweight loader that binds CSV inputs into typed dataclasses."""

    def __init__(self, data_dir: str | Path):
        self.base_path = Path(data_dir)
        self._ensure_exists()
        self.project = self._load_project_params()
        self.tranches = self._load_tranches()
        self.cfads_projection = self._load_cfads_projection()
        self.debt_schedule = self._load_debt_schedule()
        self.rcapex_schedule = self._load_rcapex_schedule()

    @classmethod
    def from_directory(cls, data_dir: str | Path) -> "ProjectParameters":
        return cls(data_dir)

    def _ensure_exists(self) -> None:
        if not self.base_path.exists():
            raise FileNotFoundError(self.base_path)

    def _require_file(self, filename: str) -> Path:
        path = self.base_path / filename
        if not path.exists():
            raise FileNotFoundError(path)
        return path

    def _load_project_params(self) -> ProjectParams:
        csv_path = self._require_file("project_params.csv")
        df = pd.read_csv(csv_path)
        if not {"param", "value"}.issubset(df.columns):
            raise ValueError("project_params.csv must contain param and value columns")
        param_map = {str(row.param): row.value for row in df.itertuples(index=False)}
        missing = REQUIRED_PROJECT_PARAMS - param_map.keys()
        if missing:
            raise ValueError(f"Missing parameters in project_params.csv: {sorted(missing)}")

        def _val(name: str, cast=float) -> float:
            raw = param_map[name]
            return cast(raw)

        return ProjectParams(
            analysis_horizon_years=int(_val("analysis_horizon_years")),
            tenor_years=int(_val("tenor_years")),
            grace_period_years=int(_val("grace_period_years")),
            ramping_period_months=int(_val("ramping_period_months")),
            periods_per_year=int(_val("periods_per_year")),
            tax_rate_corporate=float(_val("tax_rate_corporate")),
            min_dscr_covenant=float(_val("min_dscr_covenant")),
            min_llcr_covenant=float(_val("min_llcr_covenant")),
            dscr_default_trigger=float(_val("dscr_default_trigger")),
            dscr_grace_threshold=float(_val("dscr_grace_threshold")),
            base_rate_reference=float(_val("base_rate_reference")),
            spread_senior=float(_val("spread_senior")),
            spread_mezz=float(_val("spread_mezz")),
            spread_sub=float(_val("spread_sub")),
            target_dscr_years_5_10=float(_val("target_dscr_years_5_10")),
            dsra_months_cover=int(_val("dsra_months_cover")),
            mra_target_pct_next_rcapex=float(_val("mra_target_pct_next_rcapex")),
        )

    def _load_tranches(self) -> List[DebtTrancheParams]:
        csv_path = self._require_file("tranches.csv")
        df = pd.read_csv(csv_path)
        required = {
            "tranche_name",
            "priority_level",
            "initial_principal",
            "rate_base_type",
            "base_rate",
            "spread_bps",
            "grace_period_years",
            "tenor_years",
            "amortization_style",
        }
        if not required.issubset(df.columns):
            raise ValueError("tranches.csv schema mismatch")
        tranches: List[DebtTrancheParams] = []
        for row in df.itertuples(index=False):
            tranches.append(
                DebtTrancheParams(
                    name=str(row.tranche_name),
                    priority_level=int(row.priority_level),
                    initial_principal=float(row.initial_principal),
                    rate_base_type=str(row.rate_base_type),
                    base_rate=float(row.base_rate),
                    spread_bps=int(row.spread_bps),
                    grace_period_years=int(row.grace_period_years),
                    tenor_years=int(row.tenor_years),
                    amortization_style=str(row.amortization_style),
                )
            )
        if not tranches:
            raise ValueError("tranches.csv must define at least one tranche")
        return sorted(tranches, key=lambda t: t.priority_level)

    def _load_cfads_projection(self) -> CFADSProjectionParams:
        csv_path = self._require_file("revenue_projection.csv")
        df = pd.read_csv(csv_path)
        rows = df.to_dict(orient="records")
        return CFADSProjectionParams(rows=rows)

    def _load_debt_schedule(self) -> pd.DataFrame:
        csv_path = self._require_file("debt_schedule.csv")
        df = pd.read_csv(csv_path)
        required_cols = {"year", "tranche_name", "interest_due", "principal_due"}
        if not required_cols.issubset(df.columns):
            raise ValueError("debt_schedule.csv schema mismatch")
        return df.copy()

    def _load_rcapex_schedule(self) -> pd.DataFrame:
        csv_path = self._require_file("rcapex_schedule.csv")
        df = pd.read_csv(csv_path)
        required_cols = {"year", "rcapex_amount"}
        if not required_cols.issubset(df.columns):
            raise ValueError("rcapex_schedule.csv schema mismatch")
        return df.copy()

    def cfads_dataframe(self) -> pd.DataFrame:
        """Return the CFADS projection as a DataFrame for quick analysis."""
        return self.cfads_projection.to_dataframe()

    def to_dict(self) -> Dict[str, object]:
        """Serialize high-level components for logging/debugging."""
        return {
            "project": self.project,
            "tranches": self.tranches,
            "cfads_projection": self.cfads_projection.rows,
            "debt_schedule": self.debt_schedule.to_dict(orient="records"),
            "rcapex_schedule": self.rcapex_schedule.to_dict(orient="records"),
        }


__all__ = [
    "ProjectParams",
    "DebtTrancheParams",
    "CFADSProjectionParams",
    "ProjectParameters",
]
