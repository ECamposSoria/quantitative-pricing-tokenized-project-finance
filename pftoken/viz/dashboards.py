"""Dashboard composition utilities for WP-03 outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from matplotlib.figure import Figure
import numpy as np

from pftoken.models import ProjectParameters
from pftoken.pipeline import FinancialPipeline

from . import plots

USD_PER_MILLION = 1_000_000


def build_financial_dashboard(
    params: ProjectParameters,
    mc_ratio_summary: dict | None = None,
) -> Dict[str, Figure]:
    """Generate the extended dashboard using the financial pipeline outputs."""

    pipeline = FinancialPipeline(params=params)
    outputs = pipeline.run()
    cfads_vector = outputs["cfads"]
    waterfall_results = outputs["waterfall"]
    comparison = outputs["structure_comparison"]

    years = sorted(cfads_vector.keys())
    cfads_musd = np.array([cfads_vector[year] for year in years], dtype=float)
    debt_service_musd = (
        params.debt_schedule.groupby("year")[["interest_due", "principal_due"]]
        .sum()
        .reindex(years, fill_value=0.0)
        .sum(axis=1)
        .to_numpy()
        / USD_PER_MILLION
    )

    figures: Dict[str, Figure] = {}
    figures["cfads_vs_debt_service"] = plots.plot_cfads_vs_debt_service(
        years, cfads_musd, debt_service_musd
    )

    dscr_series = [outputs["dscr"][year]["value"] for year in years]
    figures["dscr_timeseries"] = plots.plot_dscr_series(
        years, dscr_series, min_threshold=params.project.min_dscr_covenant
    )

    snapshot_years = [min(4, years[-1]), min(5, years[-1]), min(11, years[-1])]
    labels = [f"DSCR Y{year}" for year in snapshot_years]
    values = [outputs["dscr"][year]["value"] for year in snapshot_years]
    thresholds = [
        params.project.dscr_grace_threshold if year <= params.project.grace_period_years else params.project.min_dscr_covenant
        for year in snapshot_years
    ]
    figures["ratio_snapshot"] = plots.plot_ratio_snapshot(labels, values, thresholds)

    tranche_labels = [tranche.name for tranche in params.tranches]
    notionals = [tranche.initial_principal for tranche in params.tranches]
    figures["capital_structure"] = plots.plot_capital_structure(tranche_labels, notionals)

    interest_series = [
        sum(waterfall_results[year].interest_payments.values()) / USD_PER_MILLION for year in years
    ]
    principal_series = [
        sum(waterfall_results[year].principal_payments.values()) / USD_PER_MILLION for year in years
    ]
    dividends_series = [waterfall_results[year].dividends / USD_PER_MILLION for year in years]
    figures["waterfall_cascade"] = plots.plot_waterfall_cascade(
        years, interest_series, principal_series, dividends_series
    )

    dsra_balance = [waterfall_results[year].dsra_balance / USD_PER_MILLION for year in years]
    dsra_target = [waterfall_results[year].dsra_target / USD_PER_MILLION for year in years]
    mra_balance = [waterfall_results[year].mra_balance / USD_PER_MILLION for year in years]
    mra_target = [waterfall_results[year].mra_target / USD_PER_MILLION for year in years]
    figures["reserves_levels"] = plots.plot_reserve_levels(
        years, dsra_balance, dsra_target, mra_balance, mra_target
    )

    thresholds_full = [
        params.project.dscr_grace_threshold if year <= params.project.grace_period_years else params.project.min_dscr_covenant
        for year in years
    ]
    figures["covenant_heatmap"] = plots.plot_covenant_heatmap(years, dscr_series, thresholds_full)

    radar_metrics = [
        ("Costo", comparison.wacd_tokenized * 100),
        ("HHI", comparison.concentration_tokenized),
        ("Δbps", abs(comparison.delta_wacd_bps) / 100.0),
    ]
    figures["structure_radar"] = plots.plot_structure_radar(
        radar_metrics, baseline=comparison.concentration_traditional
    )

    if mc_ratio_summary:
        percentiles = mc_ratio_summary.get("percentiles", {})
        p50 = percentiles.get(50)
        if p50 is not None:
            fan_years = years[: len(p50)]
            figures["dscr_fan_chart"] = plots.plot_fan_chart(
                fan_years,
                percentiles=percentiles,
                threshold=params.project.min_dscr_covenant,
                title="DSCR Fan Chart (MC)",
            )

    return figures


def save_dashboard(figures: Dict[str, Figure], output_dir: Path | str) -> None:
    """Persist dashboard figures to disk for manual sharing or reports."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    for name, fig in figures.items():
        fig.savefig(output_path / f"{name}.png", dpi=150, bbox_inches="tight")


__all__ = ["build_financial_dashboard", "save_dashboard"]
