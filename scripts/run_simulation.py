"""CLI wrapper to run Monte Carlo simulations."""

import argparse

from pftoken.simulation import pipeline


def main() -> None:
    """Parse CLI arguments and trigger the simulation pipeline."""
    parser = argparse.ArgumentParser(description="Run the project finance simulation pipeline.")
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to the simulation configuration file.",
    )
    parser.add_argument(
        "--amm",
        action="store_true",
        help="Enable AMM integration pipeline.",
    )
    args = parser.parse_args()
    pipeline.not_implemented(args.config, enable_amm=args.amm)


if __name__ == "__main__":
    main()
