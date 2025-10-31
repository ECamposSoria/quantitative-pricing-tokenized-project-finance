"""CLI helper to generate reporting artifacts."""

import argparse

from pftoken.viz import dashboards


def main() -> None:
    """Builds project finance dashboards."""
    parser = argparse.ArgumentParser(description="Generate dashboards from simulation output.")
    parser.add_argument(
        "--input",
        default="data/output/simulation_results/latest.csv",
        help="Simulation results to visualise.",
    )
    parser.add_argument(
        "--include-amm",
        action="store_true",
        help="Include AMM dashboards in the generated report.",
    )
    args = parser.parse_args()
    dashboards.not_implemented(args.input, include_amm=args.include_amm)


if __name__ == "__main__":
    main()
