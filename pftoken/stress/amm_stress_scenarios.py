"""Predefined AMM stress scenarios for WP-14."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class AMMStressScenario:
    code: str
    name: str
    description: str
    params: dict


def build_scenarios() -> Dict[str, AMMStressScenario]:
    return {
        "PS": AMMStressScenario(
            code="PS",
            name="Panic Sell Ladder",
            description="Progressive sell pressure of reserves.",
            params={"steps": [0.10, 0.25, 0.50]},
        ),
        "LP": AMMStressScenario(
            code="LP",
            name="LP Withdrawal Cascade",
            description="Sequential LP exits reducing liquidity depth.",
            params={"steps": [0.10, 0.20, 0.30]},
        ),
        "FC": AMMStressScenario(
            code="FC",
            name="Flash Crash + Recovery",
            description="Sharp price drop followed by partial recovery.",
            params={"drop_fraction": 0.4, "recovery_fraction": 0.5},
        ),
    }


__all__ = ["AMMStressScenario", "build_scenarios"]
