"""Sensitivity scenario tests for tokenized spread deltas."""

from __future__ import annotations

import csv
from pathlib import Path

from pftoken.pricing.spreads import (
    TokenizedSpreadConfig,
    TokenizedSpreadModel,
)
from pftoken.pricing.spreads.delta_decomposition import (
    ConsolidatedDeltaDecomposition,
    PerTrancheDeltaBreakdown,
)
from pftoken.pricing.spreads.tokenized import SensitivityScenario
from pftoken.waterfall.debt_structure import DebtStructure, Tranche


def _debt_structure() -> DebtStructure:
    return DebtStructure(
        [
            Tranche(
                name="senior",
                principal=60_000_000,
                rate=0.05,
                seniority=1,
                tenor_years=10,
                grace_period_years=2,
                amortization_style="sculpted",
            )
        ]
    )


def _base_decomposition() -> ConsolidatedDeltaDecomposition:
    per_tranche = {
        "senior": PerTrancheDeltaBreakdown(
            tranche="senior",
            principal_usd=60_000_000,
            delta_credit_bps=-30.0,
            delta_liquidity_bps=-32.0,
            delta_origination_bps=-8.0,
            delta_servicing_bps=-20.0,
            delta_infrastructure_bps=3.0,
        )
    }
    return ConsolidatedDeltaDecomposition(
        per_tranche=per_tranche,
        weighted_delta_credit_bps=-30.0,
        weighted_delta_liquidity_bps=-32.0,
        weighted_delta_origination_bps=-8.0,
        weighted_delta_servicing_bps=-20.0,
        weighted_delta_infrastructure_bps=3.0,
    )


def test_sensitivity_base_matches_decomposition():
    model = TokenizedSpreadModel(_debt_structure(), TokenizedSpreadConfig(auto_calibrate_liquidity=False))
    scenarios = model.simulate_delta_scenarios(base_decomposition=_base_decomposition(), debt_structure=_debt_structure())
    base = next(item for item in scenarios if item.name == "Base")
    assert abs(base.delta_liquidity_bps - (-32.0)) < 1e-6
    assert abs(base.total_delta_bps - _base_decomposition().total_weighted_delta_bps) < 1e-6


def test_sensitivity_liquidity_scale_applied():
    model = TokenizedSpreadModel(_debt_structure(), TokenizedSpreadConfig(auto_calibrate_liquidity=False))
    base_decomp = _base_decomposition()
    scenarios = model.simulate_delta_scenarios(base_decomposition=base_decomp, debt_structure=_debt_structure())
    base = next(item for item in scenarios if item.name == "Base")
    down = next(item for item in scenarios if "Tinlake TVL -50%" in item.name)
    assert abs(down.delta_liquidity_bps - base.delta_liquidity_bps * 0.5) < 1e-6


def test_sensitivity_beta_override_scales_origination():
    config = TokenizedSpreadConfig(auto_calibrate_liquidity=False, origination_beta=0.5)
    model = TokenizedSpreadModel(_debt_structure(), config)
    base_decomp = _base_decomposition()
    scenarios = model.simulate_delta_scenarios(base_decomposition=base_decomp, debt_structure=_debt_structure())
    base = next(item for item in scenarios if item.name == "Base")
    beta_low = next(item for item in scenarios if "Beta = 0.3" in item.name)
    assert beta_low.delta_origination_bps == base.delta_origination_bps * (0.3 / config.origination_beta)


def test_export_sensitivity_scenarios(tmp_path):
    scenarios = [
        SensitivityScenario(
            name="Test",
            liquidity_scale=1.0,
            beta_override=None,
            infra_tx_multiplier=1.0,
            delta_credit_bps=-30.0,
            delta_liquidity_bps=-32.0,
            delta_origination_bps=-8.0,
            delta_servicing_bps=-20.0,
            delta_infrastructure_bps=3.0,
            total_delta_bps=-87.0,
        )
    ]
    model = TokenizedSpreadModel(_debt_structure(), TokenizedSpreadConfig(auto_calibrate_liquidity=False))
    csv_path = tmp_path / "sensitivities" / "test.csv"
    written = model.export_sensitivity_scenarios(scenarios, str(csv_path))
    assert written.exists()
    with written.open() as fp:
        reader = csv.DictReader(fp)
        rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["scenario"] == "Test"
    assert "timestamp_utc" in rows[0]
