#!/usr/bin/env python3
"""
Export deterministic CSV snapshots for the Excel validation workbook.

Usage:
    python scripts/export_excel_validation.py \
        --data-dir data/input/leo_iot \
        --output-root data/output/excel_exports
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from pftoken.config.defaults import DEFAULT_RESERVE_POLICY
from pftoken.models import CFADSCalculator, ProjectParameters, RatioCalculator
from pftoken.waterfall import DebtStructure, WaterfallOrchestrator


def main() -> None:
    parser = argparse.ArgumentParser(description="Export CSVs for Excel QA.")
    parser.add_argument("--data-dir", default="data/input/leo_iot", help="Path to the locked CSV input directory.")
    parser.add_argument(
        "--output-root",
        default="data/output/excel_exports",
        help="Folder where timestamped CSV snapshots will be created.",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_root = Path(args.output_root)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    target = output_root / timestamp
    target.mkdir(parents=True, exist_ok=True)

    params = ProjectParameters.from_directory(data_dir)
    cfads_calc = CFADSCalculator.from_project_parameters(params)
    cfads_df = pd.DataFrame([result.to_dict() for result in cfads_calc.cfads_results])
    cfads_df.to_csv(target / "cfads_components.csv", index=False)

    ratio_calc = RatioCalculator(
        cfads_calc.calculate_cfads_vector(),
        params.debt_schedule,
        tranches=params.tranches,
    )
    dscr_map = ratio_calc.dscr_by_year(
        params.project.grace_period_years,
        params.project.tenor_years,
    )
    ratios_df = pd.DataFrame(
        [
            {"year": year, **obs.__dict__}
            for year, obs in dscr_map.items()
        ]
    )
    ratios_df.to_csv(target / "ratios.csv", index=False)

    debt_structure = DebtStructure.from_tranche_params(params.tranches)
    orchestrator = WaterfallOrchestrator(
        cfads_vector=cfads_calc.calculate_cfads_vector(),
        debt_structure=debt_structure,
        debt_schedule=params.debt_schedule,
        rcapex_schedule=params.rcapex_schedule,
        grace_period_years=params.project.grace_period_years,
        tenor_years=params.project.tenor_years,
        reserve_policy=DEFAULT_RESERVE_POLICY,
    )
    waterfall_result = orchestrator.run()
    waterfall_df = pd.DataFrame(
        [
            {"year": period.year, "dividends": period.dividends, "cash_sweep": period.cash_sweep}
            | {"interest_" + k: v for k, v in period.interest_payments.items()}
            | {"principal_" + k: v for k, v in period.principal_payments.items()}
        ]
        for period in waterfall_result.periods
    )
    waterfall_df.to_csv(target / "waterfall.csv", index=False)

    print(f"Exported CFADS/Ratios/Waterfall snapshots to {target}")


if __name__ == "__main__":
    main()
