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
    args = parser.parse_args()
    pipeline.not_implemented(args.config)


if __name__ == "__main__":
    main()
