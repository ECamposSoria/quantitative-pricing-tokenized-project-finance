"""CLI utility to compare DCF valuations with AMM market prices."""

import argparse

from pftoken.amm.pricing import dcf_integration


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare DCF valuation series with AMM prices.")
    parser.add_argument("--dcf", nargs="+", type=float, required=True, help="Space separated DCF prices.")
    parser.add_argument("--market", nargs="+", type=float, required=True, help="Space separated AMM prices.")
    parser.add_argument(
        "--weight-market",
        type=float,
        default=0.5,
        help="Weight assigned to market prices when blending with DCF.",
    )
    args = parser.parse_args()

    blended = dcf_integration.blend_price(args.dcf[-1], args.market[-1], weight_market=args.weight_market)
    deviations = dcf_integration.discrepancy_series(args.dcf, args.market)
    print(f"Blended terminal price: {blended:.6f}")
    print(f"Average deviation: {deviations.mean():.6f}")


if __name__ == "__main__":
    main()
