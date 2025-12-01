"""Factories for Monte Carlo path callbacks tied to baseline CFADS/debt (WP-07)."""

from __future__ import annotations

from typing import Callable, Mapping, Sequence, Dict

import numpy as np
import pandas as pd
import warnings

from .monte_carlo import SimulationCallback
from .path_dependent import PathDependentConfig, evaluate_first_passage
from .regime_switching import RegimeConfig, RegimeSwitchingProcess
from pftoken.waterfall.debt_structure import DebtStructure


def build_financial_path_callback(
    baseline_cfads: Mapping[int, float],
    debt_schedule: pd.DataFrame,
    years: Sequence[int],
    *,
    base_discount_rate: float,
    debt_structure: DebtStructure | None = None,
    include_tranche_cashflows: bool = False,
    launch_failure_impact: float = 0.4,
    usd_per_million: float = 1_000_000.0,
    grace_period_years: int = 0,
    path_config: PathDependentConfig | None = None,
    regime_config: RegimeConfig | None = None,
) -> SimulationCallback:
    """
    Create a callback that maps stochastic draws to CFADS/DSCR paths + asset values.

    Notes:
    - baseline_cfads is expected in millions of USD (MUSD) as produced by
      `CFADSCalculator.calculate_cfads_vector()`.
    - Discount rate uses the project's base_rate_reference (approx. risk-free). This can
      be swapped for WACC if PD sensitivity to leverage is desired.
    - Shapes: returns `dscr_paths` with (n_sims, n_periods) and `asset_values` (n_sims,).
    """

    years_sorted = list(sorted(years))
    n_periods = len(years_sorted)
    cfads_base = np.array([baseline_cfads[year] for year in years_sorted], dtype=float)
    cfads_base_musd = cfads_base  # already in MUSD
    debt_service = _debt_service_by_year(debt_schedule, years_sorted, usd_per_million=usd_per_million)
    principal_by_year = _principal_by_year(debt_schedule, years_sorted, usd_per_million=usd_per_million)
    total_principal_musd = float(principal_by_year.sum())
    debt_outstanding_musd = _outstanding_schedule(principal_by_year, total_principal_musd)
    debt_outstanding_usd = debt_outstanding_musd * usd_per_million
    discount_periods = np.arange(1, n_periods + 1, dtype=float)
    grace_mask = np.array(years_sorted) <= grace_period_years
    path_cfg = path_config or PathDependentConfig()
    regime_cfg = regime_config or RegimeConfig()
    regime_process = RegimeSwitchingProcess(regime_cfg) if regime_cfg.enable_regime_switching else None

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

        shocked_cfads = cfads_base_musd[None, :] * growth_factor[:, None]
        shocked_cfads *= 1.0 - launch_failure_impact * launch_failure[:, None]
        shocked_cfads = np.maximum(shocked_cfads, 0.0)

        regime_paths = None
        regime_recovery_adj = None
        regime_spread_lift_bps = None
        if regime_process is not None:
            regime_paths = regime_process.simulate_regimes(batch_size, n_periods)
            params_by_path = regime_process.get_params_by_path(regime_paths)
            growth = np.exp(params_by_path["mu"] - 0.5 * np.square(params_by_path["sigma"]))
            shocked_cfads *= np.clip(growth, 0.1, 5.0)
            regime_recovery_adj = params_by_path["recovery_adj"]
            regime_spread_lift_bps = params_by_path["spread_lift_bps"]

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
        discounted_cfads = shocked_cfads * disc_factors
        asset_values = np.sum(discounted_cfads, axis=1) * usd_per_million
        if asset_values.mean() < 0.1:
            warnings.warn(
                f"Asset values are very small vs expected scale (mean={asset_values.mean():.4f}); "
                "check units alignment between CFADS and debt."
            )

        asset_value_paths = None
        first_passage_default = None
        if path_cfg.enable_path_default:
            asset_value_paths = np.flip(
                np.cumsum(np.flip(discounted_cfads, axis=1), axis=1),
                axis=1,
            ) * usd_per_million
            first_passage_default = evaluate_first_passage(
                asset_value_paths,
                debt_outstanding_usd,
                path_cfg,
            )

        output = {
            "dscr_paths": dscr_paths,
            "asset_values": asset_values,
            "secondary_market_depth": secondary_market_depth,
            "smart_contract_risk": smart_contract_risk,
            # Store CFADS paths for dual-structure analysis (WP-12)
            # Units: MUSD (millions USD), shape (n_sims, n_periods)
            "cfads_paths": shocked_cfads,
            # Store rate shocks for hedging comparison (WP-13)
            # Units: decimal (e.g., 0.01 = 100 bps), shape (n_sims,)
            "rate_shock": rate_shock,
        }

        if asset_value_paths is not None:
            output["asset_value_paths"] = asset_value_paths
            output["first_passage_default"] = first_passage_default

        if regime_paths is not None:
            output["regime_paths"] = regime_paths
            output["regime_recovery_adj"] = regime_recovery_adj
            output["regime_spread_lift_bps"] = regime_spread_lift_bps

        if include_tranche_cashflows and debt_structure is not None:
            output["tranche_cashflows"] = _vectorized_tranche_cashflows(
                shocked_cfads,
                debt_schedule,
                debt_structure,
                years_sorted,
                usd_per_million=usd_per_million,
            )

        return output

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


def _principal_by_year(debt_schedule: pd.DataFrame, years: Sequence[int], *, usd_per_million: float) -> np.ndarray:
    if "principal_due" not in debt_schedule.columns:
        raise ValueError("debt_schedule must contain principal_due column.")
    principal = (
        debt_schedule.groupby("year")["principal_due"]
        .sum()
        .reindex(years, fill_value=0.0)
        .to_numpy()
    )
    return np.asarray(principal, dtype=float) / usd_per_million


def _outstanding_schedule(principal_by_year: np.ndarray, total_principal_musd: float) -> np.ndarray:
    """Outstanding principal before payments in each period."""

    outstanding = np.empty_like(principal_by_year, dtype=float)
    balance = total_principal_musd
    for idx, principal in enumerate(principal_by_year):
        outstanding[idx] = balance
        balance = max(balance - principal, 0.0)
    return outstanding


def _vectorized_tranche_cashflows(
    shocked_cfads: np.ndarray,
    debt_schedule: pd.DataFrame,
    debt_structure: DebtStructure,
    years: Sequence[int],
    *,
    usd_per_million: float,
) -> Dict[str, np.ndarray]:
    """
    Simplified waterfall: allocate shocked CFADS by seniority-first against scheduled payments.

    Notes:
        - Ignores DSRA/MRA path dependence; provides a fast approximation for MC pricing.
        - Assumes debt_schedule contains tranche_name, year, interest_due, principal_due.
    """

    n_sims, n_periods = shocked_cfads.shape
    if n_periods != len(years):
        raise ValueError("Mismatch between shocked CFADS periods and provided years.")

    schedule: Dict[str, np.ndarray] = {}
    for tranche in debt_structure.tranches:
        mask = debt_schedule["tranche_name"].str.lower() == tranche.name.lower()
        sched = (
            debt_schedule.loc[mask, ["year", "interest_due", "principal_due"]]
            .groupby("year")[["interest_due", "principal_due"]]
            .sum()
            .reindex(years, fill_value=0.0)
            .sum(axis=1)
            .to_numpy()
            / usd_per_million
        )
        schedule[tranche.name] = sched

    remaining = shocked_cfads.copy()
    cashflows: Dict[str, np.ndarray] = {}
    for tranche in debt_structure.tranches:
        sched = schedule.get(tranche.name)
        sched_matrix = np.broadcast_to(sched, (n_sims, n_periods))
        pay = np.minimum(remaining, sched_matrix)
        cashflows[tranche.name] = pay * usd_per_million
        remaining = np.maximum(remaining - pay, 0.0)
    return cashflows


__all__ = ["build_financial_path_callback"]
