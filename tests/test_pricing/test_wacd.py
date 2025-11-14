"""WACD calculator tests using modular spread decomposition."""

from __future__ import annotations

import math

from pftoken.models.merton import MertonResult
from pftoken.pricing import TokenizedSpreadConfig, WACDCalculator, WACDScenario
from pftoken.pricing.constants import PricingContext
from pftoken.waterfall.debt_structure import DebtStructure, Tranche


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


def _dummy_merton_results() -> dict[str, MertonResult]:
    return {
        "senior": MertonResult(
            tranche="senior",
            pd=0.02,
            lgd=0.4,
            expected_loss=0.02 * 0.4,
            distance_to_default=3.0,
            asset_volatility=0.25,
            recovery_rate=0.6,
        ),
        "mezz": MertonResult(
            tranche="mezz",
            pd=0.04,
            lgd=0.5,
            expected_loss=0.04 * 0.5,
            distance_to_default=2.2,
            asset_volatility=0.3,
            recovery_rate=0.5,
        ),
    }


def test_tokenized_structure_reduces_wacd_with_spread_components(monkeypatch):
    monkeypatch.setattr("pftoken.pricing.spreads.liquidity.fetch_tinlake_metrics", lambda: None)
    calculator = WACDCalculator(_structure())
    comparison = calculator.compare_traditional_vs_tokenized(merton_results=_dummy_merton_results())
    assert comparison["tokenized"] < comparison["traditional"]
    details = comparison["details"]
    assert "breakdowns" in details
    senior_components = details["breakdowns"]["senior"]["components"]
    assert "liquidity" in senior_components
    assert details["scenario_spreads_bps"]["tokenized"]["senior"] < details["scenario_spreads_bps"]["traditional"]["senior"]
    delta_info = details["delta_spread_bps"]
    assert delta_info["source"] == "computed"
    assert delta_info["used"] == delta_info["computed"]
    assert "delta_sensitivity" in comparison
    assert comparison["delta_sensitivity"]["scenarios"]
    assert "scenario_breakdowns" in comparison


def test_manual_deltas_remain_supported(monkeypatch):
    monkeypatch.setattr("pftoken.pricing.spreads.liquidity.fetch_tinlake_metrics", lambda: None)
    context = PricingContext(use_computed_deltas=False, tokenized_spread_delta_bps=-50, tokenized_origination_fee_bps=-20)
    calculator = WACDCalculator(
        _structure(),
        pricing_context=context,
        spread_config=TokenizedSpreadConfig(liquidity_alpha=0.4, auto_calibrate_liquidity=False),
    )
    base = calculator.compute(WACDScenario(name="traditional"), merton_results=_dummy_merton_results())
    shifted = calculator.compute(
        WACDScenario(name="traditional", spread_delta_bps=50),
        merton_results=_dummy_merton_results(),
    )
    expected_delta = 0.005 * (1 - calculator.pricing_context.corporate_tax_rate)
    assert math.isclose(shifted - base, expected_delta, rel_tol=1e-6)
    comparison = calculator.compare_traditional_vs_tokenized(merton_results=_dummy_merton_results())
    delta_info = comparison["details"]["delta_spread_bps"]
    assert delta_info["source"] == "override"
    assert delta_info["used"] == context.tokenized_spread_delta_bps
