from __future__ import annotations

from pftoken.pricing.spreads import (
    TokenizedSpreadConfig,
    TokenizedSpreadModel,
)
from pftoken.pricing.spreads.base import (
    PerTrancheSpreadBreakdown,
    SpreadComponentResult,
)
from pftoken.waterfall.debt_structure import DebtStructure, Tranche


def _breakdown(name: str, components: dict[str, tuple[float, float]]) -> PerTrancheSpreadBreakdown:
    breakdown = PerTrancheSpreadBreakdown(tranche=name)
    for comp_name, (trad, tokenized) in components.items():
        breakdown.add_component(SpreadComponentResult(comp_name, trad, tokenized, {}))
    return breakdown


def test_delta_decomposition_weighted_totals():
    debt = DebtStructure(
        [
            Tranche(
                name="senior",
                principal=60_000_000,
                rate=0.05,
                seniority=1,
                tenor_years=10,
                grace_period_years=2,
                amortization_style="sculpted",
            ),
            Tranche(
                name="mezz",
                principal=40_000_000,
                rate=0.08,
                seniority=2,
                tenor_years=10,
                grace_period_years=2,
                amortization_style="sculpted",
            ),
        ]
    )
    model = TokenizedSpreadModel(debt, TokenizedSpreadConfig(auto_calibrate_liquidity=False))
    breakdowns = {
        "senior": _breakdown(
            "senior",
            {
                "credit": (50.0, 50.0),
                "liquidity": (80.0, 40.0),
                "origination": (15.0, 7.0),
                "servicing": (25.0, 0.0),
                "infrastructure": (0.0, 5.0),
            },
        ),
        "mezz": _breakdown(
            "mezz",
            {
                "credit": (60.0, 60.0),
                "liquidity": (90.0, 60.0),
                "origination": (15.0, 10.0),
                "servicing": (25.0, 0.0),
                "infrastructure": (0.0, 5.0),
            },
        ),
    }

    decomp = model.compute_delta_decomposition(breakdowns, debt)

    # Credit deltas deberían ser cero
    assert all(delta.delta_credit_bps == 0 for delta in decomp.per_tranche.values())

    # Infraestructura debe ser positiva (tokenizado > tradicional)
    assert all(delta.delta_infrastructure_bps >= 0 for delta in decomp.per_tranche.values())

    # Weighted totals
    assert decomp.weighted_delta_liquidity_bps == (-40 * 0.6) + (-30 * 0.4)
    assert decomp.weighted_delta_origination_bps == (-8 * 0.6) + (-5 * 0.4)
    assert decomp.weighted_delta_servicing_bps == (-25) * (0.6 + 0.4)
    assert decomp.total_weighted_delta_bps == (
        decomp.weighted_delta_credit_bps
        + decomp.weighted_delta_liquidity_bps
        + decomp.weighted_delta_origination_bps
        + decomp.weighted_delta_servicing_bps
        + decomp.weighted_delta_infrastructure_bps
    )

    # to_dict incluye totales
    payload = decomp.to_dict()
    assert "weighted_totals" in payload
    senior_dict = payload["per_tranche"]["senior"]
    assert senior_dict["total_delta_bps"] == sum(
        senior_dict[key]
        for key in [
            "delta_credit_bps",
            "delta_liquidity_bps",
            "delta_origination_bps",
            "delta_servicing_bps",
            "delta_infrastructure_bps",
        ]
    )
