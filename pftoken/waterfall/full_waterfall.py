"""Multi-period waterfall orchestration with DSRA/MRA lifecycle tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional

import numpy as np
import pandas as pd

from pftoken.config.defaults import DEFAULT_RESERVE_POLICY, ReservePolicy
from pftoken.models.ratios import RatioCalculator

from .debt_structure import DebtStructure
from .waterfall_engine import ReserveState, WaterfallEngine, WaterfallResult
from .covenants import CovenantEngine

USD_PER_MILLION = 1_000_000.0
IRR_TOLERANCE = 1e-7


@dataclass(frozen=True)
class FullWaterfallResult:
    periods: List[WaterfallResult]
    equity_cashflows: List[float]
    equity_irr: float
    total_dividends: float
    dsra_series: List[float] = field(default_factory=list)
    mra_series: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "equity_irr": self.equity_irr,
            "total_dividends": self.total_dividends,
            "periods": [period.__dict__ for period in self.periods],
            "equity_cashflows": self.equity_cashflows,
            "dsra_series": self.dsra_series,
            "mra_series": self.mra_series,
        }


class WaterfallOrchestrator:
    """Coordinates CFADS, ratios, and the single-period engine."""

    def __init__(
        self,
        cfads_vector: Mapping[int, float],
        debt_structure: DebtStructure,
        debt_schedule: pd.DataFrame,
        rcapex_schedule: pd.DataFrame,
        *,
        grace_period_years: int,
        tenor_years: int,
        reserve_policy: ReservePolicy | None = None,
        covenant_engine: CovenantEngine | None = None,
    ):
        self.cfads_vector = dict(sorted(cfads_vector.items()))
        self.debt_structure = debt_structure
        self.debt_schedule = debt_schedule.copy()
        self.rcapex_schedule = rcapex_schedule.copy()
        self.grace_period_years = grace_period_years
        self.tenor_years = tenor_years
        self.reserve_policy = reserve_policy or DEFAULT_RESERVE_POLICY
        self.covenant_engine = covenant_engine
        self.engine = WaterfallEngine(covenant_engine=covenant_engine)

    def run(self) -> FullWaterfallResult:
        ratio_calc = RatioCalculator(
            self.cfads_vector,
            self.debt_schedule,
            tranches=self.debt_structure.tranches,
        )
        dscr_map = ratio_calc.dscr_by_year(self.grace_period_years, self.tenor_years)
        reserves = ReserveState(
            dsra_months_cover=self.reserve_policy.dsra_months_cover,
            mra_target_pct=self.reserve_policy.mra_target_pct_next_rcapex,
            dsra_balance=self.reserve_policy.dsra_initial_musd * USD_PER_MILLION,
            lock_until_year=self.grace_period_years,
        )

        periods: List[WaterfallResult] = []
        equity_cashflows: List[float] = [-self.reserve_policy.dsra_initial_musd * USD_PER_MILLION]
        dsra_series: List[float] = [reserves.dsra_balance]
        mra_series: List[float] = [reserves.mra_balance]

        for year, cfads in self.cfads_vector.items():
            dscr_value = dscr_map[year].value if year in dscr_map else None
            period_result = self.engine.execute_waterfall(
                year=year,
                cfads_available=cfads,
                debt_structure=self.debt_structure,
                debt_schedule=self.debt_schedule,
                reserves=reserves,
                dscr_value=dscr_value,
                rcapex_schedule=self.rcapex_schedule,
            )
            periods.append(period_result)
            equity_cashflows.append(period_result.dividends)
            dsra_series.append(reserves.dsra_balance)
            mra_series.append(reserves.mra_balance)

        equity_irr = float(_compute_irr(equity_cashflows)) if any(equity_cashflows[1:]) else 0.0
        total_dividends = float(sum(period.dividends for period in periods))
        if self.covenant_engine is not None:
            self.covenant_engine.evaluate_llcr(ratio_calc.llcr_by_tranche(), period=self.tenor_years)

        return FullWaterfallResult(
            periods=periods,
            equity_cashflows=equity_cashflows,
            equity_irr=equity_irr,
            total_dividends=total_dividends,
            dsra_series=dsra_series,
            mra_series=mra_series,
        )


def _compute_irr(cashflows: List[float], *, guess: float = 0.1) -> float:
    """Simple Newton-Raphson IRR implementation to avoid heavy deps."""

    rate = guess
    for _ in range(100):
        npv = 0.0
        derivative = 0.0
        for idx, cf in enumerate(cashflows):
            denom = (1 + rate) ** idx
            npv += cf / denom
            if idx > 0:
                derivative -= idx * cf / ((1 + rate) ** (idx + 1))
        if abs(derivative) < 1e-12:
            break
        new_rate = rate - npv / derivative
        if abs(new_rate - rate) < IRR_TOLERANCE:
            return new_rate
        rate = new_rate
    return rate


__all__ = ["FullWaterfallResult", "WaterfallOrchestrator"]
