"""Factories for Monte Carlo path callbacks tied to baseline CFADS/debt (WP-07)."""

from __future__ import annotations

from typing import Callable, Mapping, Sequence

import numpy as np
import pandas as pd
import warnings

from .monte_carlo import SimulationCallback


def build_financial_path_callback(
    baseline_cfads: Mapping[int, float],
    debt_schedule: pd.DataFrame,
    years: Sequence[int],
    *,
    base_discount_rate: float,
    launch_failure_impact: float = 0.4,
    usd_per_million: float = 1_000_000.0,
    grace_period_years: int = 0,
) -> SimulationCallback:
    """
    Create a callback that maps stochastic draws to CFADS/DSCR paths + asset values.

    Notes:
    - Discount rate uses the project's base_rate_reference (approx. risk-free). This can
      be swapped for WACC if PD sensitivity to leverage is desired.
    - Shapes: returns `dscr_paths` with (n_sims, n_periods) and `asset_values` (n_sims,).
    """

    years_sorted = list(sorted(years))
    n_periods = len(years_sorted)
    cfads_base = np.array([baseline_cfads[year] for year in years_sorted], dtype=float)
    debt_service = _debt_service_by_year(debt_schedule, years_sorted, usd_per_million=usd_per_million)
    discount_periods = np.arange(1, n_periods + 1, dtype=float)
    grace_mask = np.array(years_sorted) <= grace_period_years

    def path_callback(batch: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]:
        batch_size = len(next(iter(batch.values())))

        # Fetch shocks with safe fallbacks.
        revenue_growth = np.asarray(batch.get("revenue_growth", np.zeros(batch_size)), dtype=float)
        churn_rate = np.asarray(batch.get("churn_rate", np.zeros(batch_size)), dtype=float)
        opex_inflation = np.asarray(batch.get("opex_inflation", np.zeros(batch_size)), dtype=float)
        launch_failure = np.asarray(batch.get("launch_failure", np.zeros(batch_size)), dtype=float)
        rate_shock = np.asarray(batch.get("rate_shock", np.zeros(batch_size)), dtype=float)
        regulatory_delay = np.asarray(batch.get("regulatory_delay", np.zeros(batch_size)), dtype=float)
        satellite_degradation = np.asarray(batch.get("satellite_degradation", np.zeros(batch_size)), dtype=float)
        competitive_pressure = np.asarray(batch.get("competitive_pressure", np.zeros(batch_size)), dtype=float)
        ground_segment_cost = np.asarray(batch.get("ground_segment_cost", np.zeros(batch_size)), dtype=float)
        secondary_market_depth = np.asarray(batch.get("secondary_market_depth", np.ones(batch_size) * 0.7), dtype=float)
        smart_contract_risk = np.asarray(batch.get("smart_contract_risk", np.zeros(batch_size)), dtype=float)

        effective_growth = (
            revenue_growth
            * (1.0 - churn_rate)
            * (1.0 / np.maximum(opex_inflation, 1e-6))
            * (1.0 / np.maximum(competitive_pressure, 1e-6))
            * (1.0 - satellite_degradation)
            * (1.0 - 0.3 * regulatory_delay)
            * (1.0 / np.maximum(ground_segment_cost, 1e-6))
        )
        growth_factor = np.clip(effective_growth, 0.1, None)  # avoid collapsing CFADS

        shocked_cfads = cfads_base[None, :] * growth_factor[:, None]
        shocked_cfads *= 1.0 - launch_failure_impact * launch_failure[:, None]
        shocked_cfads = np.maximum(shocked_cfads, 0.0)

        has_debt_service = debt_service > 1e-9
        dscr_paths = np.where(
            has_debt_service,
            shocked_cfads / np.maximum(debt_service, 1e-9),
            np.nan,
        )
        if grace_period_years > 0:
            dscr_paths[:, grace_mask] = np.nan

        discount_rate = np.maximum(base_discount_rate + rate_shock, 1e-6)
        disc_factors = 1.0 / np.power(1.0 + discount_rate[:, None], discount_periods[None, :])
        asset_values = np.sum(shocked_cfads * disc_factors, axis=1)
        if asset_values.mean() < 0.1:
            warnings.warn(
                f"Asset values are very small vs expected scale (mean={asset_values.mean():.4f}); "
                "check units alignment between CFADS and debt."
            )

        return {
            "dscr_paths": dscr_paths,
            "asset_values": asset_values,
            "secondary_market_depth": secondary_market_depth,
            "smart_contract_risk": smart_contract_risk,
        }

    return path_callback


def _debt_service_by_year(debt_schedule: pd.DataFrame, years: Sequence[int], *, usd_per_million: float) -> np.ndarray:
    cols = {"year", "interest_due", "principal_due"}
    if not cols.issubset(debt_schedule.columns):
        raise ValueError("debt_schedule must contain year, interest_due, principal_due columns.")
    ds = (
        debt_schedule.groupby("year")[["interest_due", "principal_due"]]
        .sum()
        .reindex(years, fill_value=0.0)
        .sum(axis=1)
        .to_numpy()
    )
    return np.asarray(ds, dtype=float) / usd_per_million


__all__ = ["build_financial_path_callback"]
