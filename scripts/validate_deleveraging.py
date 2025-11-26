#!/usr/bin/env python3
"""Validate deleveraging outcome based on leo_iot_results.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    path = Path("outputs/leo_iot_results.json")
    if not path.exists():
        print(f"Missing output file: {path}")
        return 1

    data = json.loads(path.read_text())
    breach = data.get("monte_carlo", {}).get("breach_probability", {})
    cumulative = breach.get("cumulative", [])
    finite = [p for p in cumulative if isinstance(p, (int, float))]
    max_breach = max(finite) if finite else float("nan")

    print(f"Max cumulative breach probability: {max_breach:.3f}")
    print("Target: < 0.20")
    if max_breach < 0.20:
        print("\n✅ PASS: Deleveraging successful")
        return 0
    print("\n❌ FAIL: Breach still above target")
    return 1


if __name__ == "__main__":
    sys.exit(main())
