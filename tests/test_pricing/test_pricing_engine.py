"""PricingEngine unit tests."""

from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt
import pytest

from pftoken.pricing import PricingEngine
from pftoken.waterfall.debt_structure import DebtStructure, Tranche
from pftoken.waterfall.waterfall_engine import WaterfallResult

from tests.fixtures.forward_curves import build_flat_curve

matplotlib.use("Agg")


def _make_period(year: int, interest: float, principal: float) -> WaterfallResult:
    period = WaterfallResult(year=year, cfads_available=1.0)
    period.interest_payments["senior"] = interest
    period.principal_payments["senior"] = principal
    return period


def test_pricing_engine_matches_par_value():
    curve = build_flat_curve("USD", rate=0.05, years=5)
    tranche = Tranche(
        name="senior",
        principal=10_000_000,
        rate=0.05,
        seniority=1,
        tenor_years=5,
        grace_period_years=1,
        amortization_style="level",
    )
    structure = DebtStructure([tranche])
    waterfall = {
        period.year: period
        for period in [
            _make_period(year=1, interest=500_000, principal=2_000_000),
            _make_period(year=2, interest=400_000, principal=2_000_000),
            _make_period(year=3, interest=300_000, principal=2_000_000),
            _make_period(year=4, interest=200_000, principal=2_000_000),
            _make_period(year=5, interest=100_000, principal=2_000_000),
        ]
    }
    engine = PricingEngine(curve)
    metrics = engine.price_from_waterfall(waterfall, structure)["senior"]
    assert pytest.approx(metrics.price_per_par, rel=1e-4) == 1.0
    assert pytest.approx(metrics.ytm, rel=1e-4) == 0.05
    assert metrics.macaulay_duration > 0
    assert metrics.ytm_label == "risk-free YTM"
    assert pytest.approx(metrics.risk_free_curve_rate, rel=1e-6) == 0.05
    assert abs(metrics.spread_over_curve) < 1e-9
    assert "risk-free" in metrics.explanatory_note.lower()
    payload = engine.price_from_waterfall(waterfall, structure, as_dict=True)["senior"]
    assert payload["ytm_label"] == "risk-free YTM"
    assert "risk_free_curve_rate" in payload
    assert isinstance(payload.get("cashflows"), list)
    assert payload["cashflows"][0]["year"] == 1
    fig = engine.plot_tranche_cashflows("senior", metrics)
    assert len(fig.axes) == 1
    fig2 = engine.plot_discount_curve()
    assert len(fig2.axes) == 1
    plt.close(fig)
    plt.close(fig2)


def test_ytm_is_below_coupon_when_price_above_par():
    curve = build_flat_curve("USD", rate=0.03, years=5)
    tranche = Tranche(
        name="senior",
        principal=5_000_000,
        rate=0.05,
        seniority=1,
        tenor_years=5,
        grace_period_years=0,
        amortization_style="level",
    )
    structure = DebtStructure([tranche])
    waterfall = {
        year: _make_period(year=year, interest=250_000, principal=1_000_000)
        for year in range(1, 6)
    }
    engine = PricingEngine(curve)
    metrics = engine.price_from_waterfall(waterfall, structure)["senior"]
    assert metrics.price_per_par > 1.0
    assert metrics.ytm < tranche.rate
