"""WP-02 coverage ratio helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping

import pandas as pd

from pftoken.config.defaults import (
    DEFAULT_COVENANT_LIMITS,
    DEFAULT_DSCR_THRESHOLDS,
    LLCR_TARGET_BY_PRIORITY,
    DSCRThresholds,
)
from .params import DebtTrancheParams


@dataclass(frozen=True)
class RatioObservation:
    year: int
    value: float
    phase: str
    cfads: float
    service: float
    threshold: float


@dataclass(frozen=True)
class LLCRObservation:
    tranche: str
    value: float
    threshold: float


@dataclass(frozen=True)
class RatioResults:
    dscr_by_year: Dict[int, RatioObservation]
    llcr_by_tranche: Dict[str, LLCRObservation]
    plcr: float


class RatioCalculator:
    """Computes DSCR/LLCR/PLCR metrics with deterministic thresholds."""

    def __init__(
        self,
        cfads_vector: Mapping[int, float],
        debt_schedule_df: pd.DataFrame,
        *,
        tranches: Iterable[DebtTrancheParams] | None = None,
        thresholds: DSCRThresholds | None = None,
    ):
        self.cfads_vector = dict(cfads_vector)
        self.debt_schedule = debt_schedule_df.copy()
        self.tranches = list(tranches or [])
        self.thresholds = thresholds or DEFAULT_DSCR_THRESHOLDS
        self._service = (
            self.debt_schedule.groupby("year")[["interest_due", "principal_due"]].sum().div(1_000_000.0)
        )

    def dscr_by_year(self, grace_years: int, tenor_years: int) -> Dict[int, RatioObservation]:
        results: Dict[int, RatioObservation] = {}
        for year in range(1, tenor_years + 1):
            cfads = float(self.cfads_vector.get(year, 0.0))
            interest = float(self._service.loc[year, "interest_due"]) if year in self._service.index else 0.0
            principal = float(self._service.loc[year, "principal_due"]) if year in self._service.index else 0.0
            if year <= grace_years:
                phase = "grace"
                service = interest
                threshold = self.thresholds.grace
            elif principal > 0:
                phase = "ramp" if year <= grace_years + 2 else "steady"
                service = interest + principal
                threshold = self.thresholds.ramp if phase == "ramp" else self.thresholds.steady
            elif interest == 0 and principal == 0:
                phase = "post"
                service = 0.0
                threshold = self.thresholds.steady
            else:
                phase = "steady"
                service = interest
                threshold = self.thresholds.steady
            dscr = float("inf") if service == 0 else cfads / service
            results[year] = RatioObservation(
                year=year,
                value=dscr,
                phase=phase,
                cfads=cfads,
                service=service,
                threshold=threshold,
            )
        return results

    def llcr_by_tranche(self) -> Dict[str, LLCRObservation]:
        """Calculate LLCR using cumulative debt by seniority.

        LLCR for each tranche = NPV(CFADS) / Cumulative debt up to that tranche.
        - Senior: NPV / Senior debt (most coverage, safest)
        - Mezzanine: NPV / (Senior + Mezzanine debt)
        - Subordinated: NPV / Total debt (least coverage)
        """
        if not self.tranches:
            return {}

        # Sort tranches by seniority (lower number = more senior)
        sorted_tranches = sorted(self.tranches, key=lambda t: self._get_seniority(t))

        llcr: Dict[str, LLCRObservation] = {}
        cumulative_debt = 0.0

        for tranche in sorted_tranches:
            # Use weighted average coupon for discounting
            discount_rate = self._weighted_average_coupon()
            npv_cfads = self._npv_cfads(discount_rate)

            # Add this tranche's debt to cumulative total
            tranche_debt = self._get_principal(tranche) / 1_000_000.0
            cumulative_debt += tranche_debt

            # LLCR = NPV(CFADS) / Cumulative debt
            llcr_value = float("inf") if cumulative_debt == 0 else npv_cfads / cumulative_debt
            threshold = LLCR_TARGET_BY_PRIORITY.get(self._get_seniority(tranche), DEFAULT_COVENANT_LIMITS.min_llcr)

            llcr[tranche.name] = LLCRObservation(
                tranche=tranche.name,
                value=llcr_value,
                threshold=threshold,
            )
        return llcr

    def plcr(self) -> float:
        if self.tranches:
            total_debt = sum(self._get_principal(tr) for tr in self.tranches) / 1_000_000.0
        else:
            total_debt = (
                self.debt_schedule.groupby("tranche_name")["principal_due"].sum().sum() / 1_000_000.0
                if not self.debt_schedule.empty
                else 0.0
            )
        discount_rate = self._weighted_average_coupon()
        npv_cfads = self._npv_cfads(discount_rate)
        return float("inf") if total_debt == 0 else npv_cfads / total_debt

    def _npv_cfads(self, rate: float) -> float:
        return sum(
            cfads / (1 + rate) ** year for year, cfads in sorted(self.cfads_vector.items())
        )

    def _weighted_average_coupon(self) -> float:
        if not self.tranches:
            return 0.08
        total = sum(self._get_principal(tr) for tr in self.tranches)
        if total == 0:
            return 0.0
        weighted = sum(self._get_coupon(tr) * self._get_principal(tr) for tr in self.tranches)
        return weighted / total

    def build_results(self, grace_years: int, tenor_years: int) -> RatioResults:
        return RatioResults(
            dscr_by_year=self.dscr_by_year(grace_years, tenor_years),
            llcr_by_tranche=self.llcr_by_tranche(),
            plcr=self.plcr(),
        )

    @staticmethod
    def _get_principal(tranche) -> float:
        return float(getattr(tranche, "principal", getattr(tranche, "initial_principal", 0.0)))

    @staticmethod
    def _get_coupon(tranche) -> float:
        return float(getattr(tranche, "coupon_rate", 0.0))

    @staticmethod
    def _get_seniority(tranche) -> int:
        return int(getattr(tranche, "seniority", getattr(tranche, "priority_level", 0)))


def compute_dscr_by_phase(
    cfads_vector: Dict[int, float],
    debt_schedule_df: pd.DataFrame,
    grace_years: int,
    tenor_years: int,
    thresholds: DSCRThresholds | None = None,
) -> Dict[int, Dict[str, float]]:
    """Backward-compatible helper returning DSCR grouped by phase."""

    calculator = RatioCalculator(
        cfads_vector,
        debt_schedule_df,
        thresholds=thresholds or DEFAULT_DSCR_THRESHOLDS,
    )
    results = calculator.dscr_by_year(grace_years, tenor_years)
    return {
        year: {
            "value": obs.value,
            "phase": obs.phase,
            "cfads": obs.cfads,
            "service": obs.service,
            "threshold": obs.threshold,
        }
        for year, obs in results.items()
    }


__all__ = [
    "RatioCalculator",
    "RatioResults",
    "RatioObservation",
    "LLCRObservation",
    "compute_dscr_by_phase",
]
