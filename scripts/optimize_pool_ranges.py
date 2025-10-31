"""CLI utility to optimise Uniswap v3 style ranges."""

import argparse

from pftoken.amm.analysis import range_optimizer


def main() -> None:
    parser = argparse.ArgumentParser(description="Optimise AMM tick ranges.")
    parser.add_argument("--target-price", type=float, required=True, help="Target price (token1 per token0).")
    parser.add_argument(
        "--width-hint",
        type=int,
        default=1_000,
        help="Approximate width (in ticks) for the liquidity position.",
    )
    args = parser.parse_args()
    result = range_optimizer.optimize_ticks(args.target_price, width_hint=args.width_hint)
    print(f"Lower tick: {result.lower_tick}\nUpper tick: {result.upper_tick}\nSuccess: {result.success}\n{result.message}")


if __name__ == "__main__":
    main()
