import math

import numpy as np

from pftoken.derivatives import (
    CapletPeriod,
    InterestRateCap,
    InterestRateCollar,
    find_zero_cost_floor_strike,
)
from pftoken.pricing.base_pricing import TrancheCashFlow
from pftoken.pricing.zero_curve import CurvePoint, ZeroCurve
from pftoken.pricing_mc.contracts import RateScenarioDefinition, StochasticPricingInputs
from pftoken.pricing_mc.sensitivity import InterestRateSensitivity
from pftoken.simulation.pipeline import PipelineOutputs
from pftoken.waterfall.debt_structure import DebtStructure, Tranche


def flat_curve(rate: float) -> ZeroCurve:
    return ZeroCurve(
        [CurvePoint(maturity_years=0.5, zero_rate=rate), CurvePoint(maturity_years=5.0, zero_rate=rate)]
    )


def schedule(n: int = 5) -> list[CapletPeriod]:
    return [CapletPeriod(start=i - 1 if i > 0 else 0.0, end=float(i)) for i in range(1, n + 1)]


def test_collar_net_premium_less_than_cap():
    curve = flat_curve(0.04)
    cap = InterestRateCap(notional=1_000_000, strike=0.04, reset_schedule=schedule())
    cap_premium = cap.price(curve, volatility=0.20).total_value

    collar = InterestRateCollar(
        notional=1_000_000,
        cap_strike=0.04,
        floor_strike=0.03,
        reset_schedule=schedule(),
    )
    result = collar.price(curve, volatility=0.20)

    assert result.net_premium < cap_premium
    assert result.cap_premium > result.floor_premium


def test_collar_payoff_within_band():
    collar = InterestRateCollar(
        notional=1_000_000,
        cap_strike=0.04,
        floor_strike=0.03,
        reset_schedule=schedule(1),
    )
    assert math.isclose(collar.payoff_at_rate(0.035), 0.035)
    assert math.isclose(collar.payoff_at_rate(0.05), 0.04)
    assert math.isclose(collar.payoff_at_rate(0.02), 0.03)


def test_zero_cost_floor_strike_exists():
    curve = flat_curve(0.04)
    strike = find_zero_cost_floor_strike(
        notional=50_000_000,
        cap_strike=0.04,
        reset_schedule=schedule(),
        zero_curve=curve,
        volatility=0.20,
    )
    assert strike is not None
    assert 0.01 < strike < 0.04


def test_collar_integration_with_sensitivity():
    class DummyMCResult:
        def __init__(self, sims: int = 3):
            self.draws = {"x": np.zeros(sims)}
            self.derived = {}

    debt = DebtStructure(
        [
            Tranche(
                name="senior",
                principal=100.0,
                rate=0.05,
                seniority=1,
                tenor_years=5,
                grace_period_years=0,
                amortization_style="sculpted",
            )
        ]
    )
    cashflows = {"senior": [TrancheCashFlow(year=1, interest=5.0, principal=100.0)]}
    base_curve = flat_curve(0.04)
    inputs = StochasticPricingInputs(
        mc_outputs=PipelineOutputs(monte_carlo=DummyMCResult()),
        base_curve=base_curve,
        debt_structure=debt,
        tranche_cashflows=cashflows,
    )
    sensitivity = InterestRateSensitivity(inputs)
    collar = InterestRateCollar(
        notional=100.0,
        cap_strike=0.04,
        floor_strike=0.03,
        reset_schedule=[CapletPeriod(start=0.5, end=1.0)],
    )
    scenario = RateScenarioDefinition(name="+50bps", parallel_bps=50.0)
    hedged = sensitivity.analyze_with_hedge(
        collar,
        scenarios=[scenario],
    )
    hedge_result = hedged["hedge_results"][0]
    scenario_total = sum(hedged["baseline"]["scenarios"][scenario.name].values())
    assert math.isclose(
        hedge_result["hedged_total_price"],
        scenario_total + hedge_result["hedge_value"],
        rel_tol=1e-9,
    )
