import numpy as np

from pftoken.pricing.base_pricing import TrancheCashFlow
from pftoken.pricing.zero_curve import CurvePoint, ZeroCurve
from pftoken.pricing_mc.contracts import RateScenarioDefinition, StochasticPricingInputs
from pftoken.pricing_mc.duration_convexity import DurationConvexityAnalyzer
from pftoken.pricing_mc.sensitivity import InterestRateSensitivity
from pftoken.pricing_mc.stochastic_pricing import StochasticPricing
from pftoken.simulation.monte_carlo import MonteCarloResult
from pftoken.simulation.pipeline import PipelineOutputs
from pftoken.waterfall.debt_structure import DebtStructure, Tranche


def _build_zero_curve() -> ZeroCurve:
    return ZeroCurve(
        points=[
            CurvePoint(maturity_years=1, zero_rate=0.05),
            CurvePoint(maturity_years=2, zero_rate=0.05),
        ],
        currency="USD",
    )


def test_stochastic_pricing_uses_mc_cashflows_and_defaults():
    zero_curve = _build_zero_curve()
    tranche = Tranche(
        name="Senior",
        principal=100.0,
        rate=0.06,
        seniority=1,
        tenor_years=2,
        grace_period_years=0,
        amortization_style="sculpted",
    )
    debt_structure = DebtStructure([tranche])

    # Two cashflow periods, 5 simulations; one simulation defaults (loss > 0).
    cf_matrix = np.tile(np.array([60.0, 60.0]), (5, 1))
    loss_paths = np.array([[0.0], [0.0], [1.0], [0.0], [0.0]])
    mc_result = MonteCarloResult(draws={}, derived={"tranche_cashflows": {"Senior": cf_matrix}})
    outputs = PipelineOutputs(
        monte_carlo=mc_result,
        pd_lgd_paths=None,
        loss_paths=loss_paths,
        tranche_names=["Senior"],
    )
    inputs = StochasticPricingInputs(
        mc_outputs=outputs,
        base_curve=zero_curve,
        debt_structure=debt_structure,
    )

    pricing = StochasticPricing(inputs)
    result = pricing.price()
    dist = result.tranche_prices["Senior"]

    # Four scenarios price at PV, one scenario defaulted to zero.
    pv_single = (60 / 1.05) + (60 / (1.05**2))
    expected_mean = ((4 * pv_single) + 0.0) / 5 / tranche.principal
    assert abs(dist.mean - expected_mean) < 1e-6
    assert dist.prob_below_par == 0.2  # one defaulted scenario out of five


def test_duration_convexity_analyzer_extends_existing_metrics():
    zero_curve = _build_zero_curve()
    analyzer = DurationConvexityAnalyzer(zero_curve, epsilon_bps=100.0)
    cashflows = [
        TrancheCashFlow(year=1, interest=5.0, principal=55.0),
        TrancheCashFlow(year=2, interest=4.0, principal=46.0),
    ]
    tranche = Tranche(
        name="Senior",
        principal=100.0,
        rate=0.06,
        seniority=1,
        tenor_years=2,
        grace_period_years=0,
        amortization_style="sculpted",
    )

    result = analyzer.analyze(
        tranche=tranche,
        cashflows=cashflows,
        bucket_definitions=[(0, 2), (2, 5)],
    )

    assert result.price > 0
    assert result.effective_duration > 0
    assert set(result.key_rate_durations.keys()) == {"0-2y", "2-5y"}


def test_interest_rate_sensitivity_reuses_zero_curve_shocks():
    zero_curve = _build_zero_curve()
    tranche = Tranche(
        name="Senior",
        principal=100.0,
        rate=0.06,
        seniority=1,
        tenor_years=2,
        grace_period_years=0,
        amortization_style="sculpted",
    )
    debt_structure = DebtStructure([tranche])

    cf_matrix = np.tile(np.array([60.0, 60.0]), (3, 1))
    mc_result = MonteCarloResult(draws={}, derived={"tranche_cashflows": {"Senior": cf_matrix}})
    outputs = PipelineOutputs(
        monte_carlo=mc_result,
        tranche_names=["Senior"],
    )
    inputs = StochasticPricingInputs(
        mc_outputs=outputs,
        base_curve=zero_curve,
        debt_structure=debt_structure,
    )

    sensitivity = InterestRateSensitivity(inputs)
    scenarios = [
        RateScenarioDefinition(name="Base", parallel_bps=0.0),
        RateScenarioDefinition(name="+50bps", parallel_bps=50.0),
    ]
    results = sensitivity.run(scenarios)

    assert "Base" in results["scenarios"]
    assert "Senior" in results["scenarios"]["Base"]
    assert results["tornado"]["Senior"][0]["scenario"] in {"Base", "+50bps"}


def test_price_distribution_near_par():
    zero_curve = _build_zero_curve()
    tranche = Tranche(
        name="Senior",
        principal=100.0,
        rate=0.06,
        seniority=1,
        tenor_years=2,
        grace_period_years=0,
        amortization_style="sculpted",
    )
    debt_structure = DebtStructure([tranche])

    cf_matrix = np.tile(np.array([60.0, 60.0]), (5, 1))
    # Simulate tranche cashflows in MUSD to exercise scaling
    mc_result = MonteCarloResult(draws={}, derived={"tranche_cashflows": {"Senior": cf_matrix}})
    outputs = PipelineOutputs(
        monte_carlo=mc_result,
        tranche_names=["Senior"],
    )
    inputs = StochasticPricingInputs(
        mc_outputs=outputs,
        base_curve=zero_curve,
        debt_structure=debt_structure,
    )
    pricing = StochasticPricing(inputs)
    result = pricing.price()
    dist = result.tranche_prices["Senior"]
    assert 0.5 < dist.mean < 2.0, f"Price {dist.mean} not near par"
