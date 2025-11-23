import pytest

from pftoken.pricing.wacd import WACDCalculator
from pftoken.waterfall.debt_structure import DebtStructure, Tranche


def _dummy_calc():
    tranches = [
        Tranche(name="senior", principal=60, rate=0.06, seniority=1, tenor_years=10, grace_period_years=0, amortization_style="bullet"),
        Tranche(name="mezzanine", principal=25, rate=0.085, seniority=2, tenor_years=10, grace_period_years=0, amortization_style="bullet"),
        Tranche(name="subordinated", principal=15, rate=0.12, seniority=3, tenor_years=10, grace_period_years=0, amortization_style="bullet"),
    ]
    calc = WACDCalculator(DebtStructure(tranches))
    # Bypass spread model computation with fixed spreads = 0
    calc._scenario_spreads = {"traditional": {t.name: 0.0 for t in tranches}, "tokenized": {t.name: 0.0 for t in tranches}}
    calc._breakdowns = {}
    calc._ensure_breakdowns = lambda *args, **kwargs: None
    return calc


def test_compute_with_weights_uses_alternative_allocation():
    calc = _dummy_calc()
    weights = {"senior": 0.02, "mezzanine": 0.92, "subordinated": 0.06}
    res = calc.compute_with_weights(weights, apply_tokenized_deltas=False)
    # After-tax factor ~0.75; weighted rate should reflect new weights
    expected_before_tax = 0.02 * 0.06 + 0.92 * 0.085 + 0.06 * 0.12
    expected_after_tax = expected_before_tax * (1 - calc.pricing_context.corporate_tax_rate)
    assert res["wacd_after_tax"] == pytest.approx(expected_after_tax)
    assert res["weights"]["mezzanine"] == 0.92


def test_optimized_wacd_exceeds_current_when_mezz_weighted():
    calc = _dummy_calc()
    current_weights = {"senior": 0.60, "mezzanine": 0.25, "subordinated": 0.15}
    optimized_weights = {"senior": 0.02, "mezzanine": 0.92, "subordinated": 0.06}
    current = calc.compute_with_weights(current_weights, apply_tokenized_deltas=False)["wacd_after_tax"]
    optimized = calc.compute_with_weights(optimized_weights, apply_tokenized_deltas=False)["wacd_after_tax"]
    assert optimized > current
