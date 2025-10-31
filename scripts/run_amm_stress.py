"""Run standalone AMM liquidity stress tests via CLI."""

import argparse

from pftoken.stress import liquidity_stress


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AMM liquidity stress scenarios.")
    parser.add_argument(
        "--shock",
        type=float,
        default=0.3,
        help="Shock fraction to apply to liquidity series.",
    )
    parser.add_argument(
        "--series",
        nargs="+",
        type=float,
        default=[1000, 900, 850, 800],
        help="Liquidity levels to shock (defaults to a simple sample path).",
    )
    args = parser.parse_args()
    result = liquidity_stress.stress_liquidity(args.series, args.shock)
    print(f"Depleted liquidity: {result.depleted_liquidity:.2f}")
    print(f"Max drawdown: {result.max_drawdown:.2%}")


if __name__ == "__main__":
    main()
