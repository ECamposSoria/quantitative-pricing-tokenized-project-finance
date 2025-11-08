"""Cash flow waterfall execution with DSRA/MRA support."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd

from .covenants import CovenantEngine
from .debt_structure import DebtStructure

USD_PER_MILLION = 1_000_000


@dataclass
class ReserveState:
    """Tracks DSRA/MRA balances and targets."""

    dsra_months_cover: int
    mra_target_pct: float
    dsra_balance: float = 0.0
    mra_balance: float = 0.0
    dsra_target: float = 0.0
    mra_target: float = 0.0

    def update_targets(self, next_service: float, next_rcapex: float) -> None:
        ratio = max(self.dsra_months_cover, 0) / 12.0
        self.dsra_target = next_service * ratio
        self.mra_target = next_rcapex * self.mra_target_pct

    def is_dsra_full(self) -> bool:
        return self.dsra_balance >= self.dsra_target - 1.0

    def is_mra_full(self) -> bool:
        return self.mra_balance >= self.mra_target - 1.0


@dataclass
class WaterfallResult:
    year: int
    cfads_available: float
    interest_payments: Dict[str, float] = field(default_factory=dict)
    principal_payments: Dict[str, float] = field(default_factory=dict)
    dsra_funding: float = 0.0
    mra_funding: float = 0.0
    cash_sweep: float = 0.0
    dividends: float = 0.0
    remaining_cash: float = 0.0
    events: List[str] = field(default_factory=list)
    dsra_balance: float = 0.0
    dsra_target: float = 0.0
    mra_balance: float = 0.0
    mra_target: float = 0.0


class WaterfallEngine:
    """Executes the strict waterfall ordering for a single period."""

    def __init__(self, covenant_engine: Optional[CovenantEngine] = None):
        self.covenant_engine = covenant_engine

    def execute_waterfall(
        self,
        *,
        year: int,
        cfads_available: float,
        debt_structure: DebtStructure,
        debt_schedule: pd.DataFrame,
        reserves: ReserveState,
        dscr_value: Optional[float] = None,
        rcapex_schedule: Optional[pd.DataFrame] = None,
    ) -> WaterfallResult:
        cash = max(cfads_available, 0.0) * USD_PER_MILLION
        result = WaterfallResult(year=year, cfads_available=cfads_available)
        if cfads_available < 0:
            result.events.append("cfads_deficit")

        # Step 1: Pay interest
        for tranche in debt_structure.tranches:
            scheduled = self._scheduled_amount(debt_schedule, year, tranche.name, "interest_due")
            paid, cash, events = self._pay_with_dsra(scheduled, cash, reserves)
            result.events.extend(events)
            result.interest_payments[tranche.name] = paid

        # Step 2: Fund DSRA
        next_service = self._service_for_year(debt_schedule, year + 1)
        next_rcapex = self._rcapex_for_year(rcapex_schedule, year + 1)
        reserves.update_targets(next_service, next_rcapex)
        dsra_shortfall = max(reserves.dsra_target - reserves.dsra_balance, 0.0)
        dsra_funding = min(cash, dsra_shortfall)
        reserves.dsra_balance += dsra_funding
        cash -= dsra_funding
        result.dsra_funding = dsra_funding
        result.dsra_balance = reserves.dsra_balance
        result.dsra_target = reserves.dsra_target

        # Step 3: Pay principal
        for tranche in debt_structure.tranches:
            scheduled = self._scheduled_amount(debt_schedule, year, tranche.name, "principal_due")
            paid, cash, events = self._pay_with_dsra(scheduled, cash, reserves)
            result.events.extend(events)
            result.principal_payments[tranche.name] = paid

        # Step 4: Fund MRA
        mra_shortfall = max(reserves.mra_target - reserves.mra_balance, 0.0)
        mra_funding = min(cash, mra_shortfall)
        reserves.mra_balance += mra_funding
        cash -= mra_funding
        result.mra_funding = mra_funding
        result.mra_balance = reserves.mra_balance
        result.mra_target = reserves.mra_target

        # Step 5: Cash sweep logic
        sweep_threshold = 1.15
        cash_sweep = 0.0
        if dscr_value is not None and dscr_value < sweep_threshold and cash > 0:
            cash_sweep = cash
            cash = 0.0
            result.events.append("cash_sweep_triggered")
        result.cash_sweep = cash_sweep

        # Step 6: Dividends (only if DSCR healthy and reserves full)
        dividend_threshold = 1.30
        dividends = 0.0
        if (
            dscr_value is not None
            and dscr_value > dividend_threshold
            and reserves.is_dsra_full()
            and reserves.is_mra_full()
        ):
            dividends = cash
            cash = 0.0
        result.dividends = dividends
        result.remaining_cash = cash

        if self.covenant_engine and dscr_value is not None:
            enforcement = self.covenant_engine.apply_covenant_actions(dscr_value, year)
            for action, active in enforcement.items():
                if active:
                    result.events.append(action)

        return result

    @staticmethod
    def _scheduled_amount(df: pd.DataFrame, year: int, tranche_name: str, column: str) -> float:
        mask = (df["year"] == year) & (df["tranche_name"].str.lower() == tranche_name.lower())
        return float(df.loc[mask, column].sum())

    @staticmethod
    def _service_for_year(df: pd.DataFrame, year: int) -> float:
        if df is None or year not in df["year"].values:
            return 0.0
        mask = df["year"] == year
        return float(df.loc[mask, ["interest_due", "principal_due"]].sum().sum())

    @staticmethod
    def _rcapex_for_year(df: Optional[pd.DataFrame], year: int) -> float:
        if df is None or "year" not in df.columns:
            return 0.0
        mask = df["year"] == year
        return float(df.loc[mask, "rcapex_amount"].sum()) * USD_PER_MILLION

    @staticmethod
    def _pay_with_dsra(amount: float, cash: float, reserves: ReserveState):
        """Pay scheduled amount using available cash, then DSRA if necessary."""
        events: List[str] = []
        paid = min(cash, amount)
        cash -= paid
        shortfall = amount - paid
        if shortfall > 0 and reserves.dsra_balance > 0:
            draw = min(reserves.dsra_balance, shortfall)
            reserves.dsra_balance -= draw
            paid += draw
            shortfall -= draw
            events.append("dsra_draw")
        if shortfall > 0:
            events.append("payment_shortfall")
        return paid, cash, events


__all__ = ["ReserveState", "WaterfallEngine", "WaterfallResult"]
