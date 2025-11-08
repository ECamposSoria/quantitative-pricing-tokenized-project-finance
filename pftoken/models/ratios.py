"""WP-02 coverage ratio helpers."""

from __future__ import annotations

from typing import Dict

import pandas as pd


def compute_dscr_by_phase(
    cfads_vector: Dict[int, float],
    debt_schedule_df: pd.DataFrame,
    grace_years: int,
    tenor_years: int,
) -> Dict[int, Dict[str, float]]:
    """Return DSCR, CFADS and service grouped by operating phase."""

    grouped = debt_schedule_df.groupby("year")[["interest_due", "principal_due"]].sum().div(
        1_000_000.0
    )
    results: Dict[int, Dict[str, float]] = {}

    for year in range(1, tenor_years + 1):
        cfads = float(cfads_vector.get(year, 0.0))
        interest = float(grouped.loc[year, "interest_due"]) if year in grouped.index else 0.0
        principal = float(grouped.loc[year, "principal_due"]) if year in grouped.index else 0.0

        if year <= grace_years:
            phase = "grace"
            service = interest
        elif interest == 0 and principal == 0:
            phase = "post"
            service = 0.0
        elif principal > 0:
            phase = "amortizing"
            service = interest + principal
        else:
            phase = "steady"
            service = interest

        dscr = float("inf") if service == 0 else cfads / service
        results[year] = {
            "value": dscr,
            "phase": phase,
            "cfads": cfads,
            "service": service,
        }

    return results


__all__ = ["compute_dscr_by_phase"]
