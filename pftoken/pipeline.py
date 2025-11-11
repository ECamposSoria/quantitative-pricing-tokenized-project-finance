"""High-level pipeline orchestrating CFADS → waterfall → ratios."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from pftoken.config.defaults import DEFAULT_RESERVE_POLICY
from pftoken.models import CFADSCalculator, ProjectParameters, compute_dscr_by_phase
from pftoken.waterfall import (
    ComparisonResult,
    CovenantEngine,
    DebtStructure,
    StructureComparator,
    WaterfallOrchestrator,
    WaterfallResult,
)


class FinancialPipeline:
    """End-to-end deterministic pipeline for the WP-02/03 stack."""

    def __init__(
        self,
        data_dir: Optional[str | Path] = None,
        params: Optional[ProjectParameters] = None,
    ):
        if params is None:
            if data_dir is None:
                raise ValueError("Either data_dir or params must be provided.")
            params = ProjectParameters.from_directory(data_dir)
        self.params = params
        self.debt_structure = DebtStructure.from_tranche_params(params.tranches)
        self.cfads_calculator = CFADSCalculator.from_project_parameters(params)
        self.covenant_engine = CovenantEngine()
        self.comparator = StructureComparator()

    def run(self) -> Dict[str, object]:
        cfads_vector = self.cfads_calculator.calculate_cfads_vector()
        dscr_results = compute_dscr_by_phase(
            cfads_vector,
            self.params.debt_schedule,
            grace_years=self.params.project.grace_period_years,
            tenor_years=self.params.project.tenor_years,
        )

        orchestrator = WaterfallOrchestrator(
            cfads_vector=cfads_vector,
            debt_structure=self.debt_structure,
            debt_schedule=self.params.debt_schedule,
            rcapex_schedule=self.params.rcapex_schedule,
            grace_period_years=self.params.project.grace_period_years,
            tenor_years=self.params.project.tenor_years,
            reserve_policy=DEFAULT_RESERVE_POLICY,
            covenant_engine=self.covenant_engine,
        )
        full_result = orchestrator.run()
        waterfall_results: Dict[int, WaterfallResult] = {
            period.year: period for period in full_result.periods
        }

        last_period = full_result.periods[-1]
        comparison = self.comparator.compare(
            self.debt_structure,
            dsra_target=last_period.dsra_target,
            dsra_balance=last_period.dsra_balance,
            mra_target=last_period.mra_target,
            mra_balance=last_period.mra_balance,
        )

        return {
            "cfads": cfads_vector,
            "dscr": dscr_results,
            "waterfall": waterfall_results,
            "breaches": self.covenant_engine.breach_history,
            "reserves": {
                "dsra_balance": full_result.dsra_series[-1],
                "mra_balance": full_result.mra_series[-1],
                "equity_irr": full_result.equity_irr,
            },
            "structure_comparison": comparison,
            "waterfall_equity_cashflows": full_result.equity_cashflows,
        }


__all__ = ["FinancialPipeline"]
