#!/usr/bin/env python3
"""
Quick runner for WP-05 risk metrics on the LEO IoT dataset.

Outputs a JSON snapshot under outputs/wp05_risk_metrics.json and prints
the same content to stdout.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# Add project root to import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pftoken.pipeline import FinancialPipeline  # noqa: E402


def main() -> None:
    data_dir = PROJECT_ROOT / "data" / "input" / "leo_iot"
    output_dir = PROJECT_ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    pipeline = FinancialPipeline(data_dir=data_dir)

    risk_inputs = {
        "pd": {"senior": 0.01, "mezzanine": 0.03, "subordinated": 0.10},
        "lgd": {"senior": 0.40, "mezzanine": 0.55, "subordinated": 1.00},
        "correlation": np.array(
            [
                [1.0, 0.3, 0.2],
                [0.3, 1.0, 0.4],
                [0.2, 0.4, 1.0],
            ]
        ),
        "simulations": 10_000,
        "seed": 42,
        # Efficient frontier
        "run_frontier": True,
        "frontier_samples": 500,
        "tranche_returns": {
            "senior": 0.06,
            "mezzanine": 0.085,
            "subordinated": 0.12,
        },
        # Structure comparison (traditional vs tokenized)
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

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    payload = {
        "timestamp_utc": timestamp,
        "current_structure": current_eval.get("weights", {}),
        "current_wacd_pct": round(current_eval.get("expected_return", 0) * 100, 2),
        "is_efficient": current_eval.get("is_efficient", False),
        "structure_comparison": structure_comparison,
    }

    output_path = output_dir / "wp05_risk_metrics.json"
    output_path.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))
    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()
