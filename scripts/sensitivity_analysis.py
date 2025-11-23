#!/usr/bin/env python3
"""
Sensitivity analysis for tokenization thesis defense.

Generates:
1. Tokenization benefit sensitivity to market depth.
2. Break-even analysis for tokenization viability.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pftoken.tokenization import compute_tokenization_wacd_impact  # noqa: E402


def sensitivity_to_market_depth(traditional_wacd_bps: float = 752) -> pd.DataFrame:
    """Tokenization benefit sensitivity to secondary market depth."""

    depths = np.linspace(0, 1, 21)
    results = []
    for depth in depths:
        impact = compute_tokenization_wacd_impact(traditional_wacd_bps, secondary_market_depth=depth)
        results.append(
            {
                "market_depth": depth,
                "tokenized_wacd_bps": impact["tokenized_wacd_bps"],
                "total_reduction_bps": impact["total_reduction_bps"],
                "liquidity_reduction": impact["breakdown"]["liquidity_reduction_bps"],
                "operational_reduction": impact["breakdown"]["operational_reduction_bps"],
                "transparency_reduction": impact["breakdown"]["transparency_reduction_bps"],
            }
        )
    return pd.DataFrame(results)


def break_even_analysis(traditional_wacd_bps: float = 752, tokenization_fixed_cost_bps: float = 10.0) -> dict:
    """Find break-even market depth for tokenization to be beneficial."""

    depths = np.linspace(0, 1, 101)
    for depth in depths:
        impact = compute_tokenization_wacd_impact(traditional_wacd_bps, secondary_market_depth=depth)
        net_benefit = impact["total_reduction_bps"] - tokenization_fixed_cost_bps
        if net_benefit >= 0:
            return {
                "break_even_depth": depth,
                "break_even_reduction_bps": impact["total_reduction_bps"],
                "net_benefit_at_0.7_depth": compute_tokenization_wacd_impact(
                    traditional_wacd_bps, secondary_market_depth=0.7
                )["total_reduction_bps"]
                - tokenization_fixed_cost_bps,
            }
    return {"break_even_depth": None, "message": "Tokenization never breaks even under current assumptions"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Sensitivity analysis for thesis")
    parser.add_argument("--wacd", type=float, default=752, help="Traditional WACD in bps")
    parser.add_argument("--output", type=str, default="outputs/sensitivity_analysis.json")
    args = parser.parse_args()

    depth_sensitivity = sensitivity_to_market_depth(args.wacd)
    break_even = break_even_analysis(args.wacd)

    output = {
        "traditional_wacd_bps": args.wacd,
        "depth_sensitivity": depth_sensitivity.to_dict(orient="records"),
        "break_even_analysis": break_even,
        "key_findings": {
            "benefit_at_0.5_depth": float(
                depth_sensitivity.loc[np.isclose(depth_sensitivity.market_depth, 0.5), "total_reduction_bps"].iloc[0]
            ),
            "benefit_at_0.7_depth": float(
                depth_sensitivity.loc[np.isclose(depth_sensitivity.market_depth, 0.7), "total_reduction_bps"].iloc[0]
            ),
            "benefit_at_0.9_depth": float(
                depth_sensitivity.loc[np.isclose(depth_sensitivity.market_depth, 0.9), "total_reduction_bps"].iloc[0]
            ),
            "max_benefit_bps": float(depth_sensitivity["total_reduction_bps"].max()),
        },
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2))

    print(f"Sensitivity analysis saved to: {output_path}")
    print("\nKey Findings:")
    print(f"  Break-even market depth: {break_even.get('break_even_depth', 'N/A')}")
    print(f"  Benefit at 0.7 depth: {output['key_findings']['benefit_at_0.7_depth']:.1f} bps")
    print(f"  Maximum benefit: {output['key_findings']['max_benefit_bps']:.1f} bps")


if __name__ == "__main__":
    main()
