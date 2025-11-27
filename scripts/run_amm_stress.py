"""Run AMM liquidity stress scenarios via CLI."""

import argparse
from pprint import pprint

from pftoken.amm.core.pool_v2 import ConstantProductPool, PoolConfig, PoolState
from pftoken.stress.amm_metrics_export import get_stress_metrics
from pftoken.stress.amm_stress_scenarios import build_scenarios


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AMM liquidity stress scenarios.")
    parser.add_argument("--price", type=float, default=1.0, help="Initial price (token1 per token0).")
    parser.add_argument("--reserve0", type=float, default=1_000.0, help="Initial reserve0.")
    parser.add_argument("--reserve1", type=float, default=1_000.0, help="Initial reserve1.")
    parser.add_argument(
        "--scenarios",
        nargs="+",
        default=["PS", "LP", "FC"],
        help="Scenario codes to run (default: PS LP FC).",
    )
    args = parser.parse_args()

    pool = ConstantProductPool(
        PoolConfig(token0="T0", token1="T1"),
        PoolState(reserve0=args.reserve0, reserve1=args.reserve1),
    )

    all_scenarios = build_scenarios()
    selected = [all_scenarios[code] for code in args.scenarios if code in all_scenarios]
    metrics = get_stress_metrics(pool, selected)
    pprint(
        {
            "depth_curve": metrics.depth_curve.tolist(),
            "slippage_curve": metrics.slippage_curve.tolist(),
            "stressed_depths": {k: v.tolist() for k, v in metrics.stressed_depths.items()},
            "il_by_scenario": metrics.il_by_scenario,
            "recovery_steps": metrics.recovery_steps,
        }
    )


if __name__ == "__main__":
    main()
