#!/usr/bin/env python3
"""
Find portfolios that dominate the current 60/25/15 structure on risk/return/WACD.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from pftoken.pipeline import FinancialPipeline
from pftoken.pricing.wacd import WACDCalculator


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "input" / "leo_iot"


def main() -> None:
    pipeline = FinancialPipeline(data_dir=DATA_DIR)
    wacd_calc = WACDCalculator(debt_structure=pipeline.debt_structure)
    tax_rate = wacd_calc.pricing_context.corporate_tax_rate
    tranche_rates = {t.name.lower(): t.rate for t in pipeline.debt_structure.tranches}

    risk_inputs = {
        "pd": {"senior": 0.01, "mezzanine": 0.03, "subordinated": 0.10},
        "lgd": {"senior": 0.40, "mezzanine": 0.55, "subordinated": 1.00},
        "correlation": np.array([[1.0, 0.3, 0.2], [0.3, 1.0, 0.4], [0.2, 0.4, 1.0]]),
        "simulations": 10_000,
        "seed": 42,
        "run_frontier": True,
        "frontier_samples": 500,
        "tranche_returns": {"senior": 0.06, "mezzanine": 0.085, "subordinated": 0.12},
        "wacd_calc": wacd_calc,
        "tolerance": 0.01,  # ±1% slack when treating dimensions as “held equal”
    }

    result = pipeline.run(include_risk=True, risk_inputs=risk_inputs)
    risk_metrics = result.get("risk_metrics", {})
    frontier = risk_metrics.get("frontier", {})
    if not frontier:
        print("No frontier data found.")
        return

    current_eval = frontier.get("current_structure_evaluation") or {}
    current_weights = frontier.get("current_weights", {})
    # If WACD missing, compute with current weights
    if current_eval and current_weights:
        try:
            curr_w = wacd_calc.compute_with_weights(current_weights, apply_tokenized_deltas=True)
            current_eval["wacd_after_tax"] = curr_w.get("wacd_after_tax")
        except Exception:
            # Fallback to coupon-only WACD
            current_eval["wacd_after_tax"] = sum(
                current_weights.get(name, 0.0) * rate * (1 - tax_rate) for name, rate in tranche_rates.items()
            )

    current_return = current_eval.get("expected_return")
    current_risk = current_eval.get("risk")
    current_wacd = current_eval.get("wacd_after_tax")

    tol = float(risk_inputs.get("tolerance", 0.02))

    # Search ALL frontier points, not just efficient ones
    points = frontier.get("frontier_points") or frontier.get("efficient_3d") or frontier.get("efficient") or []
    if not points:
        print("No frontier points found.")
        return
    print(f"Searching {len(points)} frontier points with ±{tol*100:.0f}% tolerance...")

    # Enrich points with WACD if missing
    enriched_points = []
    for pt in points:
        if pt.get("wacd_after_tax") is None:
            try:
                wacd_res = wacd_calc.compute_with_weights(pt.get("weights", {}), apply_tokenized_deltas=True)
                pt["wacd_after_tax"] = wacd_res.get("wacd_after_tax")
            except Exception:
                pt["wacd_after_tax"] = sum(
                    pt.get("weights", {}).get(name, 0.0) * rate * (1 - tax_rate) for name, rate in tranche_rates.items()
                )
        enriched_points.append(pt)
    points = enriched_points

    def classify(candidate: dict) -> tuple[str | None, list[str]]:
        better = []
        same = []

        cand_wacd = candidate.get("wacd_after_tax")
        cand_return = candidate.get("expected_return")
        cand_risk = candidate.get("risk")

        def leq(a, b):
            return a is not None and b is not None and a <= b * (1 + tol)

        def geq(a, b):
            return a is not None and b is not None and a >= b * (1 - tol)

        # WACD
        if current_wacd is not None and cand_wacd is not None:
            if cand_wacd < current_wacd * (1 - tol):
                better.append("wacd")
            elif leq(cand_wacd, current_wacd):
                same.append("wacd")
        # Return
        if current_return is not None and cand_return is not None:
            if cand_return > current_return * (1 + tol):
                better.append("return")
            elif geq(cand_return, current_return):
                same.append("return")
        # Risk
        if current_risk is not None and cand_risk is not None:
            if cand_risk < current_risk * (1 - tol):
                better.append("risk")
            elif leq(cand_risk, current_risk):
                same.append("risk")

        if len(better) == 3:
            return "better3", better
        if len(better) >= 2 and len(better) + len(same) == 3:
            return "better2", better
        if len(better) == 1 and len(better) + len(same) == 3:
            return "better1", better
        return None, better

    dominating = []
    secondary = []
    single = []
    for pt in points:
        category, better_dims = classify(pt)
        if category == "better3":
            dominating.append((pt, better_dims))
        elif category == "better2":
            secondary.append((pt, better_dims))
        elif category == "better1":
            single.append((pt, better_dims))

    def fmt_pt(pt: dict) -> dict:
        return {
            "weights": pt.get("weights", {}),
            "return_pct": round(pt.get("expected_return", 0) * 100, 3) if pt.get("expected_return") is not None else None,
            "risk": pt.get("risk"),
            "wacd_pct": round(pt.get("wacd_after_tax", 0) * 100, 3) if pt.get("wacd_after_tax") is not None else None,
        }

    print(f"Current weights: {current_weights}")
    print(
        f"Current return={current_return:.4f} risk={current_risk:.4f} "
        f"wacd={current_wacd if current_wacd is not None else float('nan'):.4f}"
    )
    print(f"Dominating portfolios found: {len(dominating)}")
    if dominating:
        top = dominating[:5]
        print("\nTop dominating candidates (up to 5):")
        for pt, better in top:
            print(json.dumps({"better_dims": better, **fmt_pt(pt)}, indent=2))
    else:
        print("No full dominators found.")
    if secondary:
        print("\nBetter in 2 dimensions (others held within tolerance):")
        for pt, better in secondary[:5]:
            print(json.dumps({"better_dims": better, **fmt_pt(pt)}, indent=2))
    if single:
        print("\nBetter in 1 dimension (others held within tolerance):")
        for pt, better in single[:5]:
            print(json.dumps({"better_dims": better, **fmt_pt(pt)}, indent=2))


if __name__ == "__main__":
    main()
