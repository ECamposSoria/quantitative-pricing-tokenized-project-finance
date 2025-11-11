"""Lightweight healthcheck entrypoint for Docker containers."""

from __future__ import annotations

import importlib
import sys


def main() -> None:
    modules = [
        "pftoken.models",
        "pftoken.waterfall",
        "pftoken.simulation",
    ]
    for module in modules:
        importlib.import_module(module)
    print("healthy")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(f"healthcheck failed: {exc}", file=sys.stderr)
        raise
