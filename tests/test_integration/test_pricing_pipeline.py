"""Integration test covering FinancialPipeline + pricing stack."""

from __future__ import annotations

from pathlib import Path

import pytest

from pftoken.models.merton import MertonModel
from pftoken.pipeline import FinancialPipeline
from pftoken.pricing import CollateralAnalyzer, PricingEngine, WACDCalculator
from pftoken.pricing.constants import PRICING_REL_TOLERANCE

from tests.fixtures.forward_curves import build_flat_curve


@pytest.mark.integration
def test_financial_pipeline_pricing_end_to_end(monkeypatch):
    monkeypatch.setattr("pftoken.pricing.spreads.liquidity.fetch_tinlake_metrics", lambda: None)
    data_dir = Path(__file__).resolve().parents[2] / "data" / "input" / "leo_iot"
    pipeline = FinancialPipeline(data_dir=data_dir)
    outputs = pipeline.run()
    wacd_rate = pipeline.debt_structure.calculate_wacd()
    zero_curve = build_flat_curve("USD", rate=wacd_rate, years=pipeline.params.project.tenor_years)
    collateral = CollateralAnalyzer(pipeline.debt_structure, zero_curve)
    engine = PricingEngine(zero_curve, collateral_analyzer=collateral)
    pricing = engine.price_from_waterfall(outputs["waterfall"], pipeline.debt_structure)

    for metrics in pricing.values():
        assert 0.5 <= metrics.price_per_par <= 1.5
        assert metrics.macaulay_duration > 0
        assert metrics.convexity >= 0
        if metrics.lgd is not None:
            assert 0 <= metrics.lgd <= 1

    merton = MertonModel(
        outputs["cfads"],
        pipeline.params.tranches,
        discount_rate=pipeline.params.project.base_rate_reference,
    )
    merton_results = merton.run()

    wacd = WACDCalculator(pipeline.debt_structure)
    comparison = wacd.compare_traditional_vs_tokenized(
        merton_results=merton_results,
        tranche_metrics=pricing,
    )
    assert comparison["tokenized"] <= comparison["traditional"]
    assert comparison["details"]["breakdowns"]
    assert "tokenized" in comparison["details"]["scenario_spreads_bps"]
    assert "delta_decomposition" in comparison["details"]
    assert "delta_sensitivity" in comparison
    assert comparison["delta_sensitivity"]["scenarios"]
