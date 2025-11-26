import math

import numpy as np

from pftoken.derivatives import InterestRateCap, CapletPeriod
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


def test_caplet_pricing_matches_black_formula():
    curve = flat_curve(0.05)
    period = CapletPeriod(start=0.5, end=1.0)
    cap = InterestRateCap(notional=1_000_000, strike=0.04, reset_schedule=[period])
    result = cap.price(curve, volatility=0.20)

    forward = curve.forward_rate(period.start, period.end)
    df = curve.discount_factor(period.end)
    tau = period.year_fraction()
    sigma_sqrt = 0.20 * math.sqrt(period.start)
    d1 = (math.log(forward / cap.strike) + 0.5 * sigma_sqrt**2) / sigma_sqrt
    d2 = d1 - sigma_sqrt
    expected = df * tau * (forward * 0.5 * (1 + math.erf(d1 / math.sqrt(2))) - cap.strike * 0.5 * (1 + math.erf(d2 / math.sqrt(2))))
    assert math.isclose(result.total_value, expected * cap.notional, rel_tol=1e-6)
    assert result.caplet_values[0].value > 0


def test_cap_total_equals_sum_of_caplets():
    curve = flat_curve(0.03)
    schedule = [CapletPeriod(start=0.5, end=1.0), CapletPeriod(start=1.0, end=1.5)]
    cap = InterestRateCap(notional=500_000, strike=0.025, reset_schedule=schedule)
    result = cap.price(curve, volatility=0.15)

    manual_total = sum(item.value for item in result.caplet_values)
    assert math.isclose(result.total_value, manual_total, rel_tol=1e-9)


def test_implied_volatility_recovers_input():
    curve = flat_curve(0.04)
    schedule = [CapletPeriod(start=0.5, end=1.0)]
    cap = InterestRateCap(notional=1_000_000, strike=0.04, reset_schedule=schedule)
    target = cap.price(curve, volatility=0.30).total_value

    solved = cap.implied_volatility(target_price=target, zero_curve=curve, bracket=(0.01, 1.0))
    assert math.isclose(solved, 0.30, rel_tol=1e-3)


def test_break_even_spread_bps_matches_premium_equivalent():
    curve = flat_curve(0.02)
    schedule = [CapletPeriod(start=0.5, end=1.0), CapletPeriod(start=1.0, end=2.0)]
    cap = InterestRateCap(notional=750_000, strike=0.018, reset_schedule=schedule)
    result = cap.price(curve, volatility=0.25)

    pv01 = sum(cap.notional * c.period.year_fraction() * curve.discount_factor(c.period.end) for c in result.caplet_values)
    implied = result.total_value / pv01 * 10_000.0
    assert math.isclose(result.break_even_spread_bps, implied, rel_tol=1e-9)


def test_breakeven_and_carry_cost_helpers():
    curve = flat_curve(0.03)
    schedule = [CapletPeriod(start=0.25, end=1.25), CapletPeriod(start=1.25, end=2.25)]
    cap = InterestRateCap(notional=1_000_000, strike=0.028, reset_schedule=schedule)
    result = cap.price(curve, volatility=0.22)

    annuity = sum(
        cap.notional * period.year_fraction() * curve.discount_factor(period.end)
        for period in schedule
    )
    expected_breakeven = cap.strike + result.total_value / annuity
    assert math.isclose(cap.breakeven_floating_rate(curve, volatility=0.22), expected_breakeven, rel_tol=1e-9)

    avg_tenor = sum(p.year_fraction() for p in schedule) / len(schedule)
    expected_carry_pct = (result.total_value / cap.notional) / avg_tenor * 100.0
    assert math.isclose(cap.carry_cost_pct(curve, volatility=0.22), expected_carry_pct, rel_tol=1e-9)


def test_interest_rate_sensitivity_with_hedge():
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
    cap = InterestRateCap(
        notional=100.0,
        strike=0.04,
        reset_schedule=[CapletPeriod(start=0.5, end=1.0)],
    )
    scenario = RateScenarioDefinition(name="+50bps", parallel_bps=50.0)
    hedged = sensitivity.analyze_with_hedge(
        cap,
        scenarios=[scenario],
    )
    hedge_result = hedged["hedge_results"][0]
    scenario_total = sum(hedged["baseline"]["scenarios"][scenario.name].values())

    assert hedge_result["hedge_value"] > 0  # cap gains value when rates rise
    assert math.isclose(
        hedge_result["hedged_total_price"],
        scenario_total + hedge_result["hedge_value"],
        rel_tol=1e-9,
    )
