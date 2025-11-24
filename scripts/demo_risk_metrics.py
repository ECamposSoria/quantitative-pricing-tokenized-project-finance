#!/usr/bin/env python3
"""
Quick runner for WP-05 risk metrics on the LEO IoT dataset.

Outputs a JSON snapshot under outputs/wp05_risk_metrics.json and prints
the same content to stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

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


def main() -> None:
    parser = argparse.ArgumentParser(description="Run MC risk metrics demo.")
    parser.add_argument("--sims", type=int, default=2000, help="Number of MC simulations (e.g., 10000 for prod)")
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

    output_path = output_dir / "wp05_risk_metrics.json"
    output_path.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))
    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()
