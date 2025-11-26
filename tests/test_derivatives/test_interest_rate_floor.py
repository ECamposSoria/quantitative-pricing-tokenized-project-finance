import math

import numpy as np

from pftoken.derivatives import CapletPeriod, InterestRateFloor
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


def test_floor_prices_positive_when_itm():
    curve = flat_curve(0.03)
    period = CapletPeriod(start=0.5, end=1.0)
    floor = InterestRateFloor(notional=1_000_000, strike=0.05, reset_schedule=[period])
    result = floor.price(curve, volatility=0.20)
    assert result.total_value > 0
    assert result.break_even_spread_bps > 0


def test_floor_prices_near_zero_when_otm():
    curve = flat_curve(0.04)
    period = CapletPeriod(start=0.5, end=1.0)
    floor = InterestRateFloor(notional=1_000_000, strike=0.02, reset_schedule=[period])
    result = floor.price(curve, volatility=0.20)
    assert result.total_value < 1_000  # effectively OTM


def test_floor_implied_volatility_recovers_input():
    curve = flat_curve(0.03)
    schedule = [CapletPeriod(start=0.5, end=1.0)]
    floor = InterestRateFloor(notional=1_000_000, strike=0.04, reset_schedule=schedule)
    target = floor.price(curve, volatility=0.30).total_value
    solved = floor.implied_volatility(target_price=target, zero_curve=curve, bracket=(0.01, 1.0))
    assert math.isclose(solved, 0.30, rel_tol=1e-3)


def test_floor_break_even_spread_matches_pv01():
    curve = flat_curve(0.025)
    schedule = [CapletPeriod(start=0.5, end=1.0), CapletPeriod(start=1.0, end=2.0)]
    floor = InterestRateFloor(notional=500_000, strike=0.03, reset_schedule=schedule)
    result = floor.price(curve, volatility=0.22)
    pv01 = sum(floor.notional * c.period.year_fraction() * c.discount_factor for c in result.floorlet_values)
    implied = result.total_value / pv01 * 10_000.0
    assert math.isclose(result.break_even_spread_bps, implied, rel_tol=1e-9)


def test_floor_integration_with_sensitivity():
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
    floor = InterestRateFloor(
        notional=100.0,
        strike=0.04,
        reset_schedule=[CapletPeriod(start=0.5, end=1.0)],
    )
    scenario = RateScenarioDefinition(name="+50bps", parallel_bps=50.0)
    hedged = sensitivity.analyze_with_hedge(
        floor,
        scenarios=[scenario],
    )
    hedge_result = hedged["hedge_results"][0]
    assert hedge_result["hedge_value"] < 0  # short floor effect: premium rises when rates fall, drop when rise
