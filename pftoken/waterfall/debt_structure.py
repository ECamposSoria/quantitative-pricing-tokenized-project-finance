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


class DebtStructure:
    """Container for ordered tranches with helper analytics."""

    def __init__(self, tranches: Sequence[Tranche]):
        if not tranches:
            raise ValueError("At least one tranche is required.")
        self.tranches: List[Tranche] = sorted(tranches, key=lambda t: t.seniority)
        seniorities = [t.seniority for t in self.tranches]
        if len(seniorities) != len(set(seniorities)):
            raise ValueError("Seniority levels must be unique per tranche.")

    @property
    def total_principal(self) -> float:
        return sum(tranche.principal for tranche in self.tranches)

    def calculate_wacd(self) -> float:
        """Weighted average cost of debt."""
        total = self.total_principal
        if total == 0:
            return 0.0
        return sum(tranche.principal / total * tranche.rate for tranche in self.tranches)

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


__all__ = ["Tranche", "DebtStructure"]
