"""Dashboard composition utilities for the deterministic analytics."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable

from matplotlib.figure import Figure
import numpy as np
import pandas as pd

from pftoken.models import (
    ProjectParameters,
    calculate_cfads,
    compute_dscr,
    compute_llcr,
    compute_plcr,
)

from . import plots


def build_financial_dashboard(
    params: ProjectParameters,
) -> Dict[str, Figure]:
    """
    Build a minimal dashboard (figures) based on available deterministic metrics.

    Returns a dictionary mapping component identifiers to matplotlib Figures:
    - `cfads_vs_debt_service`
    - `dscr_timeseries`
    - `ratio_snapshot`
    - `capital_structure`
    """
    years = list(params.timeline_years)
    statements = [calculate_cfads(params, year) for year in years]
    cfads = np.array([stmt.cfads for stmt in statements], dtype=float)

    debt_service = (
        params.debt_service_schedule.groupby("year")[["interest_due", "principal_due"]]
        .sum()
        .reindex(years, fill_value=0.0)
        .sum(axis=1)
        .to_numpy()
    )

    figures: Dict[str, Figure] = {}
    figures["cfads_vs_debt_service"] = plots.plot_cfads_vs_debt_service(
        years, cfads, debt_service
    )

    min_dscr = params.covenants.min_dscr
    dscr_series = compute_dscr(cfads, debt_service)
    figures["dscr_timeseries"] = plots.plot_dscr_series(
        years, dscr_series, min_threshold=min_dscr
    )

    # Ratio snapshot uses LLCR at year 5 (or earliest available) and PLCR overall.
    discount_rate = params.rate_curve.base_rate
    initial_debt = sum(tranche.notional for tranche in params.debt.tranches)
    pivot_year = 5 if 5 in years else years[0]
    index_pivot = years.index(pivot_year)
    paid_principal = params.debt_service_schedule.loc[
        params.debt_service_schedule["year"] < pivot_year, "principal_due"
    ].sum()
    outstanding = initial_debt - paid_principal
    llcr_value = compute_llcr(
        cfads[index_pivot:],
        outstanding,
        discount_rate,
    )
    plcr_value = compute_plcr(cfads, initial_debt, discount_rate)
    ratio_labels = ["LLCR", "PLCR"]
    ratio_values = [llcr_value, plcr_value]
    ratio_thresholds = [params.covenants.min_llcr, params.covenants.min_llcr]
    figures["ratio_snapshot"] = plots.plot_ratio_snapshot(
        ratio_labels, ratio_values, ratio_thresholds
    )

    tranche_labels = [tranche.name for tranche in params.debt.tranches]
    notionals = [tranche.notional for tranche in params.debt.tranches]
    figures["capital_structure"] = plots.plot_capital_structure(
        tranche_labels, notionals
    )

    return figures


def save_dashboard(figures: Dict[str, Figure], output_dir: Path | str) -> None:
    """Persist dashboard figures to disk for manual sharing or reports."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    for name, fig in figures.items():
        fig.savefig(output_path / f"{name}.png", dpi=150, bbox_inches="tight")


__all__ = ["build_financial_dashboard", "save_dashboard"]
