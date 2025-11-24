import numpy as np

from pftoken.pricing.base_pricing import TrancheCashFlow
from pftoken.pricing.zero_curve import CurvePoint, ZeroCurve
from pftoken.simulation.monte_carlo import MonteCarloConfig
from pftoken.simulation.pipeline import MonteCarloPipeline, PipelineInputs
from pftoken.waterfall.debt_structure import DebtStructure, Tranche


def _simple_zero_curve() -> ZeroCurve:
    return ZeroCurve(points=[CurvePoint(maturity_years=1, zero_rate=0.05), CurvePoint(maturity_years=5, zero_rate=0.05)])


def _simple_debt_structure() -> DebtStructure:
    tranche = Tranche(
        name="Senior",
        principal=100.0,
        rate=0.06,
        seniority=1,
        tenor_years=5,
        grace_period_years=0,
        amortization_style="sculpted",
    )
    return DebtStructure([tranche])


def _tranche_cashflows():
    return {
        "Senior": [
            TrancheCashFlow(year=1, interest=6.0, principal=20.0),
            TrancheCashFlow(year=2, interest=5.0, principal=20.0),
            TrancheCashFlow(year=3, interest=4.0, principal=20.0),
            TrancheCashFlow(year=4, interest=3.0, principal=20.0),
            TrancheCashFlow(year=5, interest=2.0, principal=20.0),
        ]
    }


def test_pipeline_populates_pricing_mc_when_curve_and_structure_provided():
    zero_curve = _simple_zero_curve()
    debt_structure = _simple_debt_structure()

    config = MonteCarloConfig(simulations=5, seed=1)
    inputs = PipelineInputs(
        debt_by_tranche={"Senior": 100.0},
        discount_rate=0.05,
        horizon_years=5.0,
    )
    pipeline = MonteCarloPipeline(config, inputs)
    outputs = pipeline.run_complete_analysis(
        zero_curve=zero_curve,
        debt_structure=debt_structure,
        tranche_cashflows=_tranche_cashflows(),
    )

    assert outputs.pricing_mc is not None
    assert "prices" in outputs.pricing_mc
    assert "duration_convexity" in outputs.pricing_mc
    assert "rate_sensitivity" in outputs.pricing_mc


def test_pipeline_skips_pricing_mc_without_curve_or_structure():
    config = MonteCarloConfig(simulations=3, seed=1)
    inputs = PipelineInputs(
        debt_by_tranche={"Senior": 100.0},
        discount_rate=0.05,
        horizon_years=5.0,
    )
    pipeline = MonteCarloPipeline(config, inputs)
    outputs = pipeline.run_complete_analysis()

    assert outputs.pricing_mc is None
