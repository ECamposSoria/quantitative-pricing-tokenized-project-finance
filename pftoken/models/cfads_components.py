"""Deterministic CFADS component calculations aligned with locked datasets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

import pandas as pd

from pftoken.config.defaults import (
    DEFAULT_RESERVE_POLICY,
    RCAPEX_DIET_MUSD,
    ReservePolicy,
)

TOLERANCE = 1e-4


@dataclass(frozen=True)
class CFADSResult:
    """Container that traces every component contributing to CFADS."""

    year: int
    revenue_gross: float
    opex: float
    maintenance_opex: float
    working_cap_change: float
    ebitda: float
    capex: float
    rcapex: float
    tax_paid: float
    pre_tax_cash: float
    cfads: float
    baseline_cfads: float
    relative_error: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "year": self.year,
            "revenue_gross": self.revenue_gross,
            "opex": self.opex,
            "maintenance_opex": self.maintenance_opex,
            "working_cap_change": self.working_cap_change,
            "ebitda": self.ebitda,
            "capex": self.capex,
            "rcapex": self.rcapex,
            "tax_paid": self.tax_paid,
            "pre_tax_cash": self.pre_tax_cash,
            "cfads": self.cfads,
            "baseline_cfads": self.baseline_cfads,
            "relative_error": self.relative_error,
        }


class CFADSComponentCalculator:
    """Build CFADS deterministically from the revenue projection table."""

    def __init__(
        self,
        projection: pd.DataFrame,
        *,
        reserve_policy: ReservePolicy | None = None,
    ):
        self.reserve_policy = reserve_policy or DEFAULT_RESERVE_POLICY
        self._projection = projection.copy()
        self._results: List[CFADSResult] | None = None

    def validate_rcapex_diet(self) -> None:
        """Ensure RCAPEX schedule matches the locked hard-coded diet."""
        for year, expected in RCAPEX_DIET_MUSD.items():
            match = self._projection.loc[self._projection["year"] == year, "rcapex"]
            if match.empty:
                raise ValueError(f"RCAPEX schedule missing year {year}")
            actual = float(match.iloc[0])
            if abs(actual - expected) > 1e-6:
                raise ValueError(
                    f"RCAPEX diet mismatch for year {year}: {actual} vs {expected}"
                )

    def build_components(self) -> List[CFADSResult]:
        if self._results is not None:
            return self._results

        self.validate_rcapex_diet()
        df = self._projection.copy()
        required_cols = [
            "year",
            "revenue_gross",
            "opex",
            "maintenance_opex",
            "working_cap_change",
            "tax_paid",
            "capex",
            "rcapex",
            "cfads",
        ]
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise ValueError(f"CFADS projection missing columns: {sorted(missing)}")

        df["ebitda"] = df["revenue_gross"] - df["opex"] - df["maintenance_opex"]
        df["operating_cash"] = df["ebitda"] - df["working_cap_change"]
        df["pre_tax_cash"] = df["operating_cash"] - df["capex"] - df["rcapex"]
        # Taxes are locked in the Excel baseline, so we rely on the provided column.
        df["tax_paid_modeled"] = df["tax_paid"]
        df["cfads_modeled"] = df["pre_tax_cash"] - df["tax_paid_modeled"]

        results: List[CFADSResult] = []
        for row in df.itertuples(index=False):
            baseline_cfads = float(row.cfads)
            cfads_modeled = float(row.cfads_modeled)
            relative_error = 0.0
            if baseline_cfads != 0:
                relative_error = abs((cfads_modeled - baseline_cfads) / baseline_cfads)
            else:
                relative_error = abs(cfads_modeled - baseline_cfads)
            if relative_error > TOLERANCE:
                raise AssertionError(
                    f"CFADS mismatch for year {row.year}: "
                    f"{cfads_modeled} vs baseline {baseline_cfads} "
                    f"(rel err {relative_error:.6f})"
                )
            results.append(
                CFADSResult(
                    year=int(row.year),
                    revenue_gross=float(row.revenue_gross),
                    opex=float(row.opex),
                    maintenance_opex=float(row.maintenance_opex),
                    working_cap_change=float(row.working_cap_change),
                    ebitda=float(row.ebitda),
                    capex=float(row.capex),
                    rcapex=float(row.rcapex),
                    tax_paid=float(row.tax_paid_modeled),
                    pre_tax_cash=float(row.pre_tax_cash),
                    cfads=cfads_modeled,
                    baseline_cfads=baseline_cfads,
                    relative_error=relative_error,
                )
            )

        self._results = results
        return results


__all__ = ["CFADSComponentCalculator", "CFADSResult", "TOLERANCE"]
