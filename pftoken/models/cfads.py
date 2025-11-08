"""CFADS utilities aligned with WP-02 requirements."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import pandas as pd

from .params import CFADSProjectionParams, ProjectParameters, ProjectParams


@dataclass(frozen=True)
class CFADSProfile:
    """Simple container for CFADS vectors keyed by year."""

    values: Dict[int, float]

    def as_list(self) -> list[float]:
        return [self.values[year] for year in sorted(self.values.keys())]


class CFADSCalculator:
    """Load CFADS projections directly from revenue_projection.csv."""

    def __init__(self, project: ProjectParams, projection: CFADSProjectionParams):
        self.project = project
        self.projection = projection

    @classmethod
    def from_project_parameters(cls, params: ProjectParameters) -> "CFADSCalculator":
        return cls(params.project, params.cfads_projection)

    def calculate_cfads_vector(self) -> Dict[int, float]:
        """Return {year: cfads} using the calibrated projection."""
        return self.projection.cfads_by_year()

    def load_cfads_from_projection(self) -> CFADSProfile:
        """Convenience wrapper mainly used by tests and validation scripts."""
        return CFADSProfile(self.calculate_cfads_vector())

    def apply_grace_period_adjustment(self, debt_schedule: pd.DataFrame) -> pd.DataFrame:
        """Force principal to zero during the grace period to avoid drift."""
        df = debt_schedule.copy()
        mask = df["year"] <= self.project.grace_period_years
        df.loc[mask, "principal_due"] = 0
        return df

    def apply_ramping_adjustment(
        self,
        debt_schedule: pd.DataFrame,
        cfads_vector: Dict[int, float] | None = None,
        target_dscr: float | None = None,
    ) -> pd.DataFrame:
        """Gradually scale principal during ramping (años 5-7)."""

        cfads_values = cfads_vector or self.calculate_cfads_vector()
        target = target_dscr or self.project.target_dscr_years_5_10
        df = debt_schedule.copy()
        ramp_years = max(1, int(max(self.project.ramping_period_years, 1)))
        start_year = self.project.grace_period_years + 1
        end_year = min(start_year + ramp_years - 1, self.project.tenor_years)

        for year in range(start_year, end_year + 1):
            service_target = cfads_values.get(year, 0.0) / target if target else 0.0
            year_mask = df["year"] == year
            interest_total = df.loc[year_mask, "interest_due"].sum() / 1_000_000.0
            current_principal = df.loc[year_mask, "principal_due"].sum() / 1_000_000.0
            desired_principal = max(service_target - interest_total, 0.0)
            if current_principal <= 0 or desired_principal <= 0:
                continue
            scale = desired_principal / current_principal
            df.loc[year_mask, "principal_due"] = (
                df.loc[year_mask, "principal_due"] * scale
            ).round().astype(int)
        return df


__all__ = ["CFADSCalculator", "CFADSProfile"]
