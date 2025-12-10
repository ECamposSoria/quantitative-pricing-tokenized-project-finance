"""Debt structure modeling utilities for WP-03."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

import pandas as pd

from pftoken.models.params import DebtTrancheParams


USD_PER_MILLION = 1_000_000


@dataclass
class Tranche:
    """Single tranche definition used by the waterfall engine."""

    name: str
    principal: float
    rate: float
    seniority: int
    tenor_years: int
    grace_period_years: int
    amortization_style: str
    spread_bps: int = 0
    rate_base_type: str = "fixed"

    @property
    def coupon_rate(self) -> float:
        return self.rate

    @property
    def base_rate(self) -> float:
        base = self.rate - self.spread_bps / 10_000.0
        return base if base >= 0 else 0.0

    def calculate_periodic_interest(self, balance: float, periods_per_year: int = 1) -> float:
        """Annualized interest payment for the provided balance."""
        if periods_per_year <= 0:
            raise ValueError("periods_per_year must be positive")
        periodic_rate = self.coupon_rate / periods_per_year
        return balance * periodic_rate

    def calculate_amortization_schedule(
        self,
        debt_schedule: pd.DataFrame,
        periods_per_year: int = 1,
    ) -> pd.DataFrame:
        """Return the scheduled principal profile filtered for this tranche."""

        mask = debt_schedule["tranche_name"].str.lower() == self.name.lower()
        schedule = debt_schedule.loc[mask, ["year", "interest_due", "principal_due"]].copy()
        if schedule.empty:
            raise ValueError(f"No scheduled payments found for tranche {self.name}")
        schedule["interest_due"] = schedule["interest_due"] / USD_PER_MILLION
        schedule["principal_due"] = schedule["principal_due"] / USD_PER_MILLION
        schedule["periods_per_year"] = periods_per_year
        return schedule.reset_index(drop=True)

    def to_dict(self) -> dict:
        """Serialize the tranche to a dict compatible with CSV/from_dicts ingestion."""

        base_rate = self.rate - self.spread_bps / 10_000.0
        if base_rate < 0:
            base_rate = 0.0
        return {
            "tranche_name": self.name,
            "priority_level": self.seniority,
            "initial_principal": self.principal,
            "rate_base_type": self.rate_base_type,
            "base_rate": base_rate,
            "spread_bps": self.spread_bps,
            "grace_period_years": self.grace_period_years,
            "tenor_years": self.tenor_years,
            "amortization_style": self.amortization_style,
            "coupon_rate": self.rate,
        }


class DebtStructure:
    """Container for ordered tranches with helper analytics."""

    def __init__(self, tranches: Sequence[Tranche]):
        if not tranches:
            raise ValueError("At least one tranche is required.")
        self.tranches: List[Tranche] = sorted(tranches, key=lambda t: t.seniority)
        seniorities = [t.seniority for t in self.tranches]
        if len(seniorities) != len(set(seniorities)):
            raise ValueError("Seniority levels must be unique per tranche.")

    def to_dicts(self) -> List[dict]:
        """Serialize the full debt structure to a list of dictionaries."""

        return [tranche.to_dict() for tranche in self.tranches]

    @property
    def total_principal(self) -> float:
        return sum(tranche.principal for tranche in self.tranches)

    def calculate_wacd(self, *, include_spreads: bool = True) -> float:
        """Weighted average cost of debt; include spreads by default."""
        total = self.total_principal
        if total == 0:
            return 0.0

        def _effective_rate(tranche: Tranche) -> float:
            base = tranche.base_rate
            return base + tranche.spread_bps / 10_000.0 if include_spreads else base

        return sum((tranche.principal / total) * _effective_rate(tranche) for tranche in self.tranches)

    def get_tranche(self, name: str) -> Tranche:
        for tranche in self.tranches:
            if tranche.name.lower() == name.lower():
                return tranche
        raise KeyError(f"Unknown tranche: {name}")

    @classmethod
    def from_csv(cls, csv_path: str | Path) -> "DebtStructure":
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
            missing = required - set(df.columns)
            raise ValueError(f"Missing columns in tranches CSV: {missing}")
        tranches = []
        for row in df.itertuples(index=False):
            base_rate = float(row.base_rate)
            spread = float(row.spread_bps) / 10_000.0
            tranches.append(
                Tranche(
                    name=str(row.tranche_name),
                    principal=float(row.initial_principal),
                    rate=base_rate + spread,
                    seniority=int(row.priority_level),
                    tenor_years=int(row.tenor_years),
                    grace_period_years=int(row.grace_period_years),
                    amortization_style=str(row.amortization_style),
                    spread_bps=int(row.spread_bps),
                    rate_base_type=str(row.rate_base_type),
                )
            )
        return cls(tranches)

    @classmethod
    def from_tranche_params(cls, tranche_params: Iterable[DebtTrancheParams]) -> "DebtStructure":
        tranches = [
            Tranche(
                name=param.name,
                principal=param.initial_principal,
                rate=param.base_rate + param.spread_bps / 10_000.0,
                seniority=param.priority_level,
                tenor_years=param.tenor_years,
                grace_period_years=param.grace_period_years,
                amortization_style=param.amortization_style,
                spread_bps=param.spread_bps,
                rate_base_type=param.rate_base_type,
            )
            for param in tranche_params
        ]
        return cls(tranches)

    @classmethod
    def from_dicts(cls, rows: Iterable[dict]) -> "DebtStructure":
        """Construct a DebtStructure from a sequence of tranche dictionaries."""

        tranches = []
        for row in rows:
            try:
                name = row["tranche_name"]
                priority = int(row["priority_level"])
                principal = float(row["initial_principal"])
                rate_base_type = row.get("rate_base_type", "fixed")
                base_rate = float(row.get("base_rate", 0.0))
                spread_bps = int(row.get("spread_bps", 0))
                grace_period_years = int(row.get("grace_period_years", 0))
                tenor_years = int(row.get("tenor_years", 0))
                amortization_style = row.get("amortization_style", "sculpted")
            except KeyError as exc:  # pragma: no cover - defensive
                raise ValueError(f"Missing column in tranche dict: {exc}") from exc

            coupon_rate = base_rate + spread_bps / 10_000.0
            tranches.append(
                Tranche(
                    name=name,
                    principal=principal,
                    rate=coupon_rate,
                    seniority=priority,
                    tenor_years=tenor_years,
                    grace_period_years=grace_period_years,
                    amortization_style=amortization_style,
                    spread_bps=spread_bps,
                    rate_base_type=rate_base_type,
                )
            )
        return cls(tranches)


__all__ = ["Tranche", "DebtStructure"]
