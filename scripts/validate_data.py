"""Ensure input datasets satisfy schema requirements."""

import argparse

from pftoken.utils import validators


def main() -> None:
    """Validate input CSV files."""
    parser = argparse.ArgumentParser(description="Validate project finance input datasets.")
    parser.add_argument(
        "path",
        default="data/input/leo_iot",
        help="Folder to validate.",
    )
    args = parser.parse_args()
    validators.not_implemented(args.path)


if __name__ == "__main__":
    main()
