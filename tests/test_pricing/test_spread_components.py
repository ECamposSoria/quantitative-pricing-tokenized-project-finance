"""Unit tests for spread decomposition components."""

from __future__ import annotations

import math
from pathlib import Path

from pftoken.pricing.spreads import (
    TokenizedSpreadConfig,
    TrancheSpreadInputs,
)
from pftoken.pricing.spreads.costs import OriginationServicingComponent
from pftoken.pricing.spreads.credit import CreditSpreadComponent
from pftoken.pricing.spreads.infrastructure import BlockchainInfrastructureTracker
from pftoken.pricing.spreads.liquidity import LiquiditySpreadComponent


def _tranche_inputs() -> TrancheSpreadInputs:
    return TrancheSpreadInputs(
        name="senior",
        principal=50_000_000.0,
        tenor_years=10,
        duration_years=5.0,
        pd=0.02,
        lgd=0.6,
    )


def test_credit_component_matches_formula():
    config = TokenizedSpreadConfig(market_price_of_risk=0.1)
    component = CreditSpreadComponent(config)
    inputs = _tranche_inputs()
    result = component.compute(inputs)
    expected = ((inputs.pd * inputs.lgd / inputs.duration_years) / (1 - inputs.pd)) * config.market_price_of_risk
    assert math.isclose(result.traditional_bps, expected * 10_000, rel_tol=1e-9)
    assert math.isclose(result.tokenized_bps, max(result.traditional_bps + config.credit_transparency_delta_bps, 0.0), rel_tol=1e-9)


def test_liquidity_component_applies_alpha_and_microstructure():
    config = TokenizedSpreadConfig(liquidity_alpha=0.5, auto_calibrate_liquidity=False)
    component = LiquiditySpreadComponent(config)
    result = component.compute(_tranche_inputs())
    assert result.traditional_bps > 0
    assert 0 < result.tokenized_bps < result.traditional_bps
    assert math.isclose(
        result.tokenized_bps,
        result.traditional_bps * result.metadata["microstructure_factor"] * (1 - config.liquidity_alpha),
        rel_tol=1e-9,
    )


def test_origination_and_servicing_components_reflect_beta_gamma():
    config = TokenizedSpreadConfig(origination_beta=0.4, servicing_gamma=0.3)
    component = OriginationServicingComponent(config)
    orig = component.compute_origination(_tranche_inputs())
    serv = component.compute_servicing(_tranche_inputs())
    expected_orig = (config.placement_bps + config.syndication_bps) / config.origination_fee_amortization_years
    expected_serv = config.paying_agent_bps + config.compliance_audit_bps
    assert orig.traditional_bps == expected_orig
    assert serv.traditional_bps == expected_serv
    assert orig.tokenized_bps == expected_orig * (1 - config.origination_beta)
    assert serv.tokenized_bps == min(expected_serv * (1 - config.servicing_gamma) + config.servicing_residual_bps, expected_serv)


def test_infrastructure_tracker_exports_csv(tmp_path):
    csv_path = tmp_path / "infra.csv"
    config = TokenizedSpreadConfig(infrastructure_csv_path=str(csv_path))
    tracker = BlockchainInfrastructureTracker(config)
    result = tracker.compute(_tranche_inputs())
    assert result.traditional_bps == 0
    assert result.tokenized_bps > 0
    written = tracker.export_cost_table(reference_principal=_tranche_inputs().principal)
    assert Path(written).exists()


def test_liquidity_component_uses_tinlake_metrics(monkeypatch):
    from types import SimpleNamespace

    fake_metrics = SimpleNamespace(
        tvl_usd=500_000_000.0,
        avg_daily_volume_usd=40_000_000.0,
        avg_pool_ticket_usd=12_000_000.0,
        datapoints=30,
        timestamp=1234567890,
    )

    def _fake_fetch():
        return fake_metrics

    monkeypatch.setattr("pftoken.pricing.spreads.liquidity.fetch_tinlake_metrics", _fake_fetch)
    config = TokenizedSpreadConfig(liquidity_alpha=0.4, auto_calibrate_liquidity=True)
    component = LiquiditySpreadComponent(config)
    result = component.compute(_tranche_inputs())
    assert "tinlake_metrics" in result.metadata
    assert result.metadata["tinlake_metrics"]["tvl_usd"] == fake_metrics.tvl_usd
