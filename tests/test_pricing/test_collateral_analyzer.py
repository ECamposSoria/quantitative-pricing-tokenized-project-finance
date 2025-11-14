"""CollateralAnalyzer tests."""

from __future__ import annotations

import pytest

from pftoken.pricing import CollateralAnalyzer
from pftoken.waterfall.debt_structure import DebtStructure, Tranche

from tests.fixtures.forward_curves import build_flat_curve


def _structure() -> DebtStructure:
    return DebtStructure(
        [
            Tranche(
                name="senior",
                principal=50_000_000,
                rate=0.05,
                seniority=1,
                tenor_years=10,
                grace_period_years=2,
                amortization_style="sculpted",
            ),
            Tranche(
                name="mezz",
                principal=20_000_000,
                rate=0.08,
                seniority=2,
                tenor_years=10,
                grace_period_years=2,
                amortization_style="sculpted",
            ),
        ]
    )


def test_collateral_analyzer_generates_recoveries():
    curve = build_flat_curve("USD", rate=0.0, years=5)
    analyzer = CollateralAnalyzer(_structure(), curve, collateral_value=70_000_000)
    results = analyzer.analyze()
    assert pytest.approx(results["senior"].recovery_rate, rel=1e-6) == 1.0
    assert pytest.approx(results["mezz"].recovery_rate, rel=1e-6) == 0.125
    assert analyzer.lgd("senior") == pytest.approx(0.0, rel=1e-6)
