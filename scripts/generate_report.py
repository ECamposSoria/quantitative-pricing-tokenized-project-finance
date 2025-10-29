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
    args = parser.parse_args()
    dashboards.not_implemented(args.input)


if __name__ == "__main__":
    main()
