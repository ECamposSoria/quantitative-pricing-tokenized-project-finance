"""High-level pipeline orchestrating CFADS → waterfall → ratios."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from pftoken.models import CFADSCalculator, ProjectParameters, compute_dscr_by_phase
from pftoken.waterfall import (
    ComparisonResult,
    Covenant,
    CovenantEngine,
    CovenantType,
    DebtStructure,
    ReserveState,
    StructureComparator,
    WaterfallEngine,
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
        self.covenant_engine = CovenantEngine(
            [
                Covenant(
                    name="DSCR_Min",
                    metric=CovenantType.DSCR,
                    threshold=params.project.min_dscr_covenant,
                    action="block_dividends",
                )
            ]
        )
        self.waterfall_engine = WaterfallEngine(self.covenant_engine)
        self.comparator = StructureComparator()

    def run(self) -> Dict[str, object]:
        cfads_vector = self.cfads_calculator.calculate_cfads_vector()
        dscr_results = compute_dscr_by_phase(
            cfads_vector,
            self.params.debt_schedule,
            grace_years=self.params.project.grace_period_years,
            tenor_years=self.params.project.tenor_years,
        )

        reserves = ReserveState(
            dsra_months_cover=self.params.project.dsra_months_cover,
            mra_target_pct=self.params.project.mra_target_pct_next_rcapex,
        )
        waterfall_results: Dict[int, WaterfallResult] = {}
        for year, cfads in cfads_vector.items():
            dscr_value = dscr_results[year]["value"]
            result = self.waterfall_engine.execute_waterfall(
                year=year,
                cfads_available=cfads,
                debt_structure=self.debt_structure,
                debt_schedule=self.params.debt_schedule,
                reserves=reserves,
                dscr_value=dscr_value if dscr_value != float("inf") else None,
                rcapex_schedule=self.params.rcapex_schedule,
            )
            waterfall_results[year] = result

        comparison = self.comparator.compare(self.debt_structure)

        return {
            "cfads": cfads_vector,
            "dscr": dscr_results,
            "waterfall": waterfall_results,
            "breaches": self.covenant_engine.breach_history,
            "reserves": {"dsra_balance": reserves.dsra_balance, "mra_balance": reserves.mra_balance},
            "structure_comparison": comparison,
        }


__all__ = ["FinancialPipeline"]
