#!/usr/bin/env python3
"""
Quick runner for WP-05 risk metrics on the LEO IoT dataset.

Outputs a JSON snapshot under outputs/leo_iot_results.json and prints
the same content to stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from pftoken.derivatives import (
    CapletPeriod,
    InterestRateCap,
    InterestRateCollar,
    InterestRateFloor,
    find_zero_cost_floor_strike,
)
from pftoken.pricing.constants import PricingContext
from pftoken.pricing.curve_loader import load_zero_curve_from_csv

# Add project root to import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pftoken.pipeline import FinancialPipeline  # noqa: E402
from pftoken.simulation import (  # noqa: E402
    MonteCarloConfig,
    MonteCarloPipeline,
    PipelineInputs,
    build_financial_path_callback,
)
from pftoken.pricing.base_pricing import TrancheCashFlow  # noqa: E402
from pftoken.pricing.zero_curve import CurvePoint, ZeroCurve  # noqa: E402
from pftoken.waterfall.debt_structure import DebtStructure  # noqa: E402
from pftoken.stress import StressScenarioLibrary  # noqa: E402
from pftoken.tokenization import TokenizationBenefits, compute_tokenization_wacd_impact  # noqa: E402
from pftoken.waterfall.contingent_amortization import (  # noqa: E402
    ContingentAmortizationConfig,
    DualStructureComparator,
)
from pftoken.hedging import HedgeConfig, run_hedging_comparison  # noqa: E402


def extract_dscr_fan_chart(mc_outputs, years: list[int]) -> dict | None:
    dscr_paths = mc_outputs.monte_carlo.derived.get("dscr_paths")
    if dscr_paths is None:
        return None
    return {
        "years": years,
        "p5": np.percentile(dscr_paths, 5, axis=0).tolist(),
        "p25": np.percentile(dscr_paths, 25, axis=0).tolist(),
        "p50": np.percentile(dscr_paths, 50, axis=0).tolist(),
        "p75": np.percentile(dscr_paths, 75, axis=0).tolist(),
        "p95": np.percentile(dscr_paths, 95, axis=0).tolist(),
    }


def extract_breach_curves(mc_outputs, years: list[int]) -> dict | None:
    if mc_outputs.breach_curves is None:
        return None
    curves = mc_outputs.breach_curves
    if isinstance(curves, dict) and "curves" in curves:
        curves = curves["curves"]
    survival = getattr(curves, "survival", None)
    breach_prob = getattr(curves, "breach_probability", None)
    hazard = getattr(curves, "hazard", None)
    if survival is None or breach_prob is None or hazard is None:
        return None
    cumulative = (1.0 - survival).tolist()
    return {
        "years": years,
        "cumulative": cumulative,
        "survival": survival.tolist(),
        "hazard": hazard.tolist(),
    }


def extract_asset_distribution(mc_outputs) -> dict | None:
    asset_values = mc_outputs.monte_carlo.derived.get("asset_values")
    if asset_values is None:
        return None
    return {
        "mean": float(np.mean(asset_values)),
        "std": float(np.std(asset_values, ddof=1)),
        "p5": float(np.percentile(asset_values, 5)),
        "p50": float(np.percentile(asset_values, 50)),
        "p95": float(np.percentile(asset_values, 95)),
    }


def extract_tranche_cashflows_from_waterfall(waterfall_results) -> dict[str, list[TrancheCashFlow]]:
    """Build deterministic tranche cashflows from WaterfallResult mapping."""

    cashflows: dict[str, list[TrancheCashFlow]] = {}
    for period in waterfall_results.values():
        for tranche, interest in period.interest_payments.items():
            principal = period.principal_payments.get(tranche, 0.0)
            if interest == 0 and principal == 0:
                continue
            cashflows.setdefault(tranche, []).append(
                TrancheCashFlow(year=period.year, interest=float(interest), principal=float(principal))
            )
    return cashflows


def build_zero_curve_from_base_rate(base_rate: float, tenor_years: int) -> ZeroCurve:
    """Create a simple flat zero curve from a base rate."""

    points = [
        CurvePoint(maturity_years=1.0, zero_rate=base_rate),
        CurvePoint(maturity_years=float(tenor_years), zero_rate=base_rate),
    ]
    return ZeroCurve(points=points, currency="USD")


def extract_tranche_metrics(mc_outputs, alpha_levels=(0.95, 0.99)) -> dict | None:
    if mc_outputs.pd_lgd_paths is None or mc_outputs.loss_paths is None:
        return None
    tranches = {}
    for idx, name in enumerate(mc_outputs.tranche_names):
        pd_path = mc_outputs.pd_lgd_paths[name]["pd"]
        lgd_path = mc_outputs.pd_lgd_paths[name]["lgd"]
        losses = mc_outputs.loss_paths[:, idx]
        var_95 = float(np.percentile(losses, alpha_levels[0] * 100))
        var_99 = float(np.percentile(losses, alpha_levels[1] * 100))
        tranches[name] = {
            "pd_mean": float(np.mean(pd_path)),
            "lgd": float(np.mean(lgd_path)),
            "expected_loss": float(np.mean(losses)),
            "capital_95": var_95,
            "capital_99": var_99,
        }
    return tranches


def extract_portfolio_risk(mc_outputs) -> dict | None:
    if mc_outputs.loss_paths is None:
        return None
    portfolio_loss = mc_outputs.loss_paths.sum(axis=1)
    var_95 = float(np.percentile(portfolio_loss, 95))
    var_99 = float(np.percentile(portfolio_loss, 99))
    return {
        "expected_loss": float(np.mean(portfolio_loss)),
        "var_95": var_95,
        "var_99": var_99,
        "cvar_95": float(portfolio_loss[portfolio_loss >= var_95].mean()),
        "cvar_99": float(portfolio_loss[portfolio_loss >= var_99].mean()),
    }


def run_stress_scenarios(baseline_dscr_min: float) -> dict:
    """Indicative stress ranking using deterministic sensitivities."""

    lib = StressScenarioLibrary()
    scenarios = lib.list_all()
    results = []
    for code, scenario in scenarios.items():
        delta = 0.0
        for shock in scenario.shocks:
            if shock.target == "revenue_growth":
                delta += shock.value * 2.0
            elif shock.target == "rate_shock":
                delta += shock.value * 1.5
            elif shock.target == "launch_failure" and shock.value > 0:
                delta -= 0.20
        stressed_dscr = baseline_dscr_min + delta
        results.append(
            {
                "code": code,
                "name": scenario.name,
                "dscr_min_stressed": round(stressed_dscr, 3),
                "delta": round(delta, 3),
            }
        )

    ranking = sorted(results, key=lambda x: x["delta"])
    near_misses = [
        {
            "code": r["code"],
            "metric": r["dscr_min_stressed"],
            "threshold": 1.0,
            "margin": round(r["dscr_min_stressed"] - 1.0, 3),
        }
        for r in results
        if 1.0 <= r["dscr_min_stressed"] <= 1.10
    ]

    return {
        "scenarios_run": list(scenarios.keys()),
        "ranking_by_dscr_impact": ranking,
        "near_misses": near_misses,
    }


def build_tokenization_analysis(traditional_wacd_bps: float, mc_outputs) -> dict:
    """Build tokenization analysis section with mechanism quantification."""

    benefits = TokenizationBenefits()
    depth_array = mc_outputs.monte_carlo.derived.get("secondary_market_depth")
    sc_risk_array = mc_outputs.monte_carlo.derived.get("smart_contract_risk")

    secondary_market_depth = 0.7
    if depth_array is not None:
        secondary_market_depth = float(np.nanmean(depth_array))

    wacd_impact = compute_tokenization_wacd_impact(
        traditional_wacd_bps=traditional_wacd_bps,
        secondary_market_depth=secondary_market_depth,
    )

    # Per-simulation benefit distribution (bps).
    benefits_per_sim = []
    if depth_array is not None:
        sc_risk = sc_risk_array if sc_risk_array is not None else np.zeros_like(depth_array)
        for depth, sc_flag in zip(depth_array, sc_risk):
            if sc_flag > 0.5:
                benefit = -50.0  # penalty for smart contract failure
            else:
                impact = compute_tokenization_wacd_impact(
                    traditional_wacd_bps=traditional_wacd_bps,
                    secondary_market_depth=float(depth),
                )
                benefit = impact["total_reduction_bps"]
            benefits_per_sim.append(benefit)

    benefit_distribution = None
    if benefits_per_sim:
        benefit_distribution = {
            "p5": float(np.percentile(benefits_per_sim, 5)),
            "p50": float(np.percentile(benefits_per_sim, 50)),
            "p95": float(np.percentile(benefits_per_sim, 95)),
            "mean": float(np.mean(benefits_per_sim)),
        }

    def depth_reduction(depth: float) -> float:
        return compute_tokenization_wacd_impact(traditional_wacd_bps, secondary_market_depth=depth)["total_reduction_bps"]

    return {
        "mechanisms": benefits.to_dict()["mechanisms"],
        "wacd_impact": wacd_impact,
        "benefit_distribution": benefit_distribution,
        "market_depth_sensitivity": {
            "depth_0.3": depth_reduction(0.3),
            "depth_0.5": depth_reduction(0.5),
            "depth_0.7": depth_reduction(0.7),
            "depth_0.9": depth_reduction(0.9),
        },
    }


def build_cap_hedging_section(
    *,
    curve,
    notional: float,
    strike: float = 0.04,
    schedule_years: int = 5,
    volatility: float | None = None,
) -> dict:
    """Price a simple cap (annual resets) and return a hedging payload."""

    vol = float(volatility if volatility is not None else PricingContext().cap_flat_volatility)
    max_year = max(1, min(schedule_years, 30))
    schedule = [CapletPeriod(start=i - 1 if i > 0 else 0.0, end=float(i)) for i in range(1, max_year + 1)]
    cap = InterestRateCap(notional=notional, strike=strike, reset_schedule=schedule)

    base = cap.price(curve, volatility=vol)
    par_swap = cap.par_swap_rate(curve)
    breakeven_rate = cap.breakeven_floating_rate(curve, volatility=vol)
    carry_pct = cap.carry_cost_pct(curve, volatility=vol)
    scenarios = [
        ("Base", curve, 0),
        ("+50bps", curve.apply_shock(parallel_bps=50), 50),
        ("-50bps", curve.apply_shock(parallel_bps=-50), -50),
    ]
    rows = []
    for name, shocked, pbps in scenarios:
        price = cap.price(shocked, volatility=vol)
        rows.append(
            {
                "scenario": name,
                "parallel_bps": pbps,
                "cap_price": price.total_value,
                "hedge_value": price.total_value - base.total_value,
            }
        )

    return {
        "interest_rate_cap": {
            "notional": notional,
            "strike": strike,
            "volatility": vol,
            "schedule_years": [p.end for p in schedule],
            "premium": base.total_value,
            "break_even_spread_bps": base.break_even_spread_bps,
            "breakeven_floating_rate": breakeven_rate,
            "carry_cost_pct": carry_pct,
            "par_swap_rate": par_swap,
            "scenarios": rows,
            "notes": "WP-11 InterestRateCap priced with flat vol; annual resets; premiums in USD.",
        }
    }


def build_collar_hedging_section(
    *,
    curve,
    notional: float,
    cap_strike: float = 0.04,
    floor_strike: float = 0.03,
    schedule_years: int = 5,
    volatility: float | None = None,
) -> dict:
    """Price a standard collar (long cap / short floor)."""

    vol = float(volatility if volatility is not None else PricingContext().cap_flat_volatility)
    schedule = [CapletPeriod(start=i - 1 if i > 0 else 0.0, end=float(i)) for i in range(1, schedule_years + 1)]
    cap = InterestRateCap(notional=notional, strike=cap_strike, reset_schedule=schedule)
    floor = InterestRateFloor(notional=notional, strike=floor_strike, reset_schedule=schedule)
    collar = InterestRateCollar(
        notional=notional,
        cap_strike=cap_strike,
        floor_strike=floor_strike,
        reset_schedule=schedule,
    )

    cap_price = cap.price(curve, volatility=vol)
    floor_price = floor.price(curve, volatility=vol)
    collar_price = collar.price(curve, volatility=vol)
    zero_cost = find_zero_cost_floor_strike(notional, cap_strike, schedule, curve, volatility=vol)

    return {
        "interest_rate_collar": {
            "notional": notional,
            "cap_strike": cap_strike,
            "floor_strike": floor_strike,
            "volatility": vol,
            "cap_premium": cap_price.total_value,
            "floor_premium": floor_price.total_value,
            "net_premium": collar_price.net_premium,
            "carry_cost_bps": collar_price.carry_cost_bps,
            "effective_rate_band": collar_price.effective_rate_band,
            "zero_cost_floor_strike": zero_cost,
            "notes": "Collar = long cap, short floor; premiums in USD.",
        }
    }


def build_hedging_comparison_section(
    mc_outputs,
    debt_structure: DebtStructure,
    grace_years: int,
    tenor_years: int,
    covenant: float = 1.20,
    cap_premium: float = 595_433.0,
    collar_net_premium: float = 326_139.0,
    cap_strike: float = 0.04,
    floor_strike: float = 0.03,
) -> dict | None:
    """
    Build hedging comparison section (WP-13).

    Runs Monte Carlo comparison across 3 hedging scenarios:
    - Unhedged (none)
    - Cap hedged
    - Collar hedged

    Uses stochastic rate shocks from MC simulation to calculate hedge payouts.
    """
    cfads_paths = mc_outputs.monte_carlo.derived.get("cfads_paths")
    rate_shocks = mc_outputs.monte_carlo.derived.get("rate_shock")

    if cfads_paths is None or rate_shocks is None:
        return None

    # Convert CFADS from MUSD to USD
    cfads_usd = cfads_paths * 1_000_000.0

    # Configure hedge parameters
    hedge_config = HedgeConfig(
        notional=debt_structure.total_principal,
        cap_strike=cap_strike,
        floor_strike=floor_strike,
        base_rate=debt_structure.calculate_wacd(),
        cap_premium=cap_premium,
        collar_net_premium=collar_net_premium,
    )

    # Configure contingent amortization (same as dual structure)
    config = ContingentAmortizationConfig(
        dscr_floor=1.25,
        dscr_target=1.50,
        dscr_accelerate=2.00,
        deferral_rate=0.12,
        max_deferral_pct=0.30,
        catch_up_enabled=True,
        balloon_cap_pct=0.50,
    )

    comparator = DualStructureComparator(
        principal=debt_structure.total_principal,
        interest_rate=debt_structure.calculate_wacd(),
        tenor=tenor_years,
        grace_years=grace_years,
        contingent_config=config,
    )

    # Run hedging comparison
    results = run_hedging_comparison(
        cfads_paths=cfads_usd,
        rate_shocks=rate_shocks,
        dual_comparator=comparator,
        covenant=covenant,
        config=hedge_config,
    )

    # Add rate shock statistics
    results["rate_shock_stats"] = {
        "mean_bps": float(np.mean(rate_shocks) * 10000),
        "std_bps": float(np.std(rate_shocks, ddof=1) * 10000),
        "p5_bps": float(np.percentile(rate_shocks, 5) * 10000),
        "p95_bps": float(np.percentile(rate_shocks, 95) * 10000),
        "simulations": len(rate_shocks),
    }

    return results


def build_dual_structure_analysis(
    mc_outputs,
    debt_structure: DebtStructure,
    grace_years: int,
    tenor_years: int,
    covenant: float = 1.20,
) -> dict | None:
    """
    Build dual structure comparison (Traditional vs Tokenized) for WP-12.

    Uses CFADS paths from Monte Carlo to compare breach probabilities
    under fixed vs DSCR-contingent amortization.

    Note: Filters out scenarios with negative CFADS in year 1 (construction
    losses), as these represent pre-operational cash flows where both
    structures would behave identically.
    """
    cfads_paths = mc_outputs.monte_carlo.derived.get("cfads_paths")
    if cfads_paths is None:
        return None

    # Convert from MUSD to USD for the comparator
    cfads_scenarios = cfads_paths * 1_000_000.0

    # Accept all scenarios including construction-phase negative CFADS
    # For LEO IoT satellite constellation: Years 1-4 are construction with equity-funded interest
    # Negative CFADS during grace period is expected and planned (not a breach)
    # The contingent amortization engine correctly handles construction financing
    total_count = len(cfads_scenarios)
    valid_count = total_count
    cfads_filtered = cfads_scenarios

    # Use weighted average rate from debt structure
    wacd = debt_structure.calculate_wacd()

    # Configure contingent amortization
    config = ContingentAmortizationConfig(
        dscr_floor=1.25,
        dscr_target=1.50,
        dscr_accelerate=2.00,
        deferral_rate=0.12,
        max_deferral_pct=0.30,
        catch_up_enabled=True,
        balloon_cap_pct=0.50,
    )

    comparator = DualStructureComparator(
        principal=debt_structure.total_principal,
        interest_rate=wacd,
        tenor=tenor_years,
        grace_years=grace_years,
        contingent_config=config,
    )

    results = comparator.run_monte_carlo_comparison(cfads_filtered, covenant)

    # Add configuration and filtering info to results
    results["config"] = {
        "principal": debt_structure.total_principal,
        "interest_rate": wacd,
        "tenor_years": tenor_years,
        "grace_years": grace_years,
        "covenant": covenant,
        "contingent_amortization": {
            "dscr_floor": config.dscr_floor,
            "dscr_target": config.dscr_target,
            "dscr_accelerate": config.dscr_accelerate,
            "max_deferral_pct": config.max_deferral_pct,
            "deferral_rate": config.deferral_rate,
            "balloon_cap_pct": config.balloon_cap_pct,
            "extension_years": config.extension_years,
            "extension_rate_spread": config.extension_rate_spread,
        },
    }
    results["filtering"] = {
        "total_scenarios": int(total_count),
        "valid_scenarios": int(valid_count),
        "filtered_pct": float((total_count - valid_count) / total_count * 100),
        "filter_reason": "No filtering applied - construction-phase negative CFADS accepted",
    }

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run MC risk metrics demo.")
    parser.add_argument("--sims", type=int, default=2000, help="Number of MC simulations (e.g., 10000 for prod)")
    parser.add_argument(
        "--hedge-curve-csv",
        type=Path,
        default=PROJECT_ROOT / "data" / "derived" / "market_curves" / "usd_combined_curve_2025-11-20.csv",
        help="Curve CSV to use for cap hedging section (defaults to combined market curve).",
    )
    parser.add_argument("--cap-strike", type=float, default=0.04, help="Cap strike for hedging section.")
    parser.add_argument("--cap-years", type=int, default=5, help="Number of annual caplets for hedging section.")
    parser.add_argument("--floor-strike", type=float, default=0.03, help="Floor strike for collar hedging.")
    parser.add_argument(
        "--include-collar",
        action="store_true",
        help="Include collar pricing (long cap / short floor) in hedging outputs.",
    )
    args = parser.parse_args()

    data_dir = PROJECT_ROOT / "data" / "input" / "leo_iot"
    output_dir = PROJECT_ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    pipeline = FinancialPipeline(data_dir=data_dir)
    cfads = pipeline.cfads_calculator.calculate_cfads_vector()
    years = [y for y in sorted(cfads.keys()) if y <= pipeline.params.project.tenor_years]
    det_run = pipeline.run(include_risk=False)
    tranche_cashflows = extract_tranche_cashflows_from_waterfall(det_run["waterfall"])
    zero_curve = build_zero_curve_from_base_rate(
        base_rate=pipeline.params.project.base_rate_reference,
        tenor_years=pipeline.params.project.tenor_years,
    )

    # Monte Carlo configuration (moderate size to keep runtime reasonable).
    mc_config = MonteCarloConfig(simulations=args.sims, seed=42, antithetic=True)
    debt_by_tranche = {t.name: t.principal / 1_000_000.0 for t in pipeline.debt_structure.tranches}  # MUSD
    tranche_returns = {t.name: t.rate for t in pipeline.debt_structure.tranches}

    path_callback = build_financial_path_callback(
        baseline_cfads=cfads,
        debt_schedule=pipeline.params.debt_schedule,
        years=years,
        base_discount_rate=pipeline.params.project.base_rate_reference,
        grace_period_years=pipeline.params.project.grace_period_years,
        debt_structure=pipeline.debt_structure,
        include_tranche_cashflows=True,
        usd_per_million=1_000_000.0,
    )

    mc_inputs = PipelineInputs(
        debt_by_tranche=debt_by_tranche,
        discount_rate=pipeline.params.project.base_rate_reference,
        horizon_years=pipeline.params.project.tenor_years,
        tranche_ead=debt_by_tranche,
        dscr_threshold=pipeline.params.project.min_dscr_covenant,
        llcr_threshold=pipeline.params.project.min_llcr_covenant,
    )
    mc_pipeline = MonteCarloPipeline(mc_config, mc_inputs, path_callback=path_callback)
    mc_outputs = mc_pipeline.run_complete_analysis(
        analyze_ratios=True,
        zero_curve=zero_curve,
        debt_structure=pipeline.debt_structure,
        tranche_cashflows=tranche_cashflows,
        include_tranche_cashflows=True,
    )

    pd_means = {
        name: float(np.mean(metrics["pd"])) for name, metrics in (mc_outputs.pd_lgd_paths or {}).items()
    }
    lgd_means = {
        name: float(np.mean(metrics["lgd"])) for name, metrics in (mc_outputs.pd_lgd_paths or {}).items()
    }
    if not pd_means or mc_outputs.loss_paths is None:
        raise RuntimeError("Monte Carlo pipeline did not produce PD/LGD/loss paths; cannot build risk metrics.")

    risk_inputs = {
        "pd": pd_means,
        "lgd": lgd_means,
        "loss_scenarios": mc_outputs.loss_paths,
        "simulations": mc_config.simulations,
        "seed": mc_config.seed,
        "run_frontier": True,
        "frontier_samples": 300,
        "tranche_returns": tranche_returns,
        "compare_structures": True,
        "compare_risk_tolerance": 0.05,
        "tokenization_spread_reduction_bps": 50,
        "traditional_constraints": {
            "min_senior_pct": 0.55,
            "max_sub_pct": 0.20,
        },
    }

    result = pipeline.run(include_risk=True, risk_inputs=risk_inputs)
    risk_metrics = result.get("risk_metrics", {})

    current_eval = risk_metrics.get("frontier", {}).get("current_structure_evaluation", {})
    structure_comparison = risk_metrics.get("structure_comparison", {})
    traditional_wacd_bps = structure_comparison.get("traditional", {}).get("wacd_bps", 752)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    dscr_paths = mc_outputs.monte_carlo.derived.get("dscr_paths")
    baseline_dscr_min = 1.3
    if dscr_paths is not None:
        dscr_finite = np.where(np.isnan(dscr_paths), np.inf, dscr_paths)
        baseline_dscr_min = float(np.nanpercentile(dscr_finite.min(axis=1), 50))

    mc_section = {
        "config": {
            "simulations": mc_config.simulations,
            "seed": mc_config.seed,
            "antithetic": mc_config.antithetic,
        },
        "dscr_fan_chart": extract_dscr_fan_chart(mc_outputs, years),
        "breach_probability": extract_breach_curves(mc_outputs, years),
        "asset_value_distribution": extract_asset_distribution(mc_outputs),
    }

    risk_section = {
        "portfolio": extract_portfolio_risk(mc_outputs),
        "tranches": extract_tranche_metrics(mc_outputs),
    }

    payload = {
        "timestamp_utc": timestamp,
        "monte_carlo": mc_section,
        "risk_metrics": risk_section,
        "stress_results": run_stress_scenarios(baseline_dscr_min),
        "tokenization_analysis": build_tokenization_analysis(traditional_wacd_bps, mc_outputs),
        "current_structure": current_eval.get("weights", {}),
        "current_wacd_pct": round(current_eval.get("expected_return", 0) * 100, 2),
        "is_efficient": current_eval.get("is_efficient", False),
        "structure_comparison": structure_comparison,
        "pricing_mc": mc_outputs.pricing_mc,
    }

    # Hedging (WP-11): append cap pricing using market curve if available, else fallback to flat curve.
    hedge_curve = zero_curve
    if args.hedge_curve_csv and args.hedge_curve_csv.exists():
        try:
            hedge_curve = load_zero_curve_from_csv(args.hedge_curve_csv)
        except Exception:
            hedge_curve = zero_curve
    payload["hedging"] = build_cap_hedging_section(
        curve=hedge_curve,
        notional=pipeline.debt_structure.total_principal,
        strike=args.cap_strike,
        schedule_years=args.cap_years,
    )
    if args.include_collar:
        payload["hedging"].update(
            build_collar_hedging_section(
                curve=hedge_curve,
                notional=pipeline.debt_structure.total_principal,
                cap_strike=args.cap_strike,
                floor_strike=args.floor_strike,
                schedule_years=args.cap_years,
            )
        )

    # Dual structure analysis (WP-12): Traditional vs Tokenized amortization comparison
    dual_structure = build_dual_structure_analysis(
        mc_outputs=mc_outputs,
        debt_structure=pipeline.debt_structure,
        grace_years=pipeline.params.project.grace_period_years,
        tenor_years=pipeline.params.project.tenor_years,
        covenant=pipeline.params.project.min_dscr_covenant,
    )
    if dual_structure is not None:
        payload["dual_structure_comparison"] = dual_structure

    # Hedging comparison (WP-13): Cap vs Collar under stochastic rate shocks
    # Get cap/collar premiums from the hedging section if available
    cap_premium = payload.get("hedging", {}).get("interest_rate_cap", {}).get("premium", 595_433.0)
    collar_section = payload.get("hedging", {}).get("interest_rate_collar", {})
    collar_net_premium = collar_section.get("net_premium", 326_139.0)

    hedging_comparison = build_hedging_comparison_section(
        mc_outputs=mc_outputs,
        debt_structure=pipeline.debt_structure,
        grace_years=pipeline.params.project.grace_period_years,
        tenor_years=pipeline.params.project.tenor_years,
        covenant=pipeline.params.project.min_dscr_covenant,
        cap_premium=cap_premium,
        collar_net_premium=collar_net_premium,
        cap_strike=args.cap_strike,
        floor_strike=args.floor_strike,
    )
    if hedging_comparison is not None:
        payload["hedging_comparison"] = hedging_comparison

    output_path = output_dir / "leo_iot_results.json"
    output_path.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))
    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()
