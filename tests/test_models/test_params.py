import math

import pytest

from pftoken.models import (
    DebtStructure,
    DebtTranche,
    MonteCarloConfig,
    ProjectParameters,
)


def test_project_parameters_from_directory(project_parameters: ProjectParameters):
    financials = project_parameters.financials
    assert financials.horizon_years == 12
    assert math.isclose(financials.tax_rate, 0.25)

    weights = project_parameters.debt.weights()
    assert len(weights) == 3
    assert math.isclose(sum(weights), 1.0, rel_tol=1e-6)

    assert "interest_due" in project_parameters.debt_service_schedule.columns


def test_debt_structure_requires_positive_notional():
    with pytest.raises(ValueError):
        DebtStructure(
            tranches=[
                DebtTranche(
                    name="senior",
                    notional=60_000_000,
                    interest_rate=0.06,
                    rate_spread=0.02,
                    tenor_years=10,
                    grace_period_years=1,
                    priority=1,
                ),
                DebtTranche(
                    name="mezz",
                    notional=30_000_000,
                    interest_rate=0.08,
                    rate_spread=0.04,
                    tenor_years=10,
                    grace_period_years=1,
                    priority=2,
                ),
                DebtTranche(
                    name="sub",
                    notional=-10_000_000,
                    interest_rate=0.1,
                    rate_spread=0.06,
                    tenor_years=10,
                    grace_period_years=2,
                    priority=3,
                ),
            ]
        )


def test_monte_carlo_correlation_dimension_validation():
    with pytest.raises(ValueError):
        MonteCarloConfig(
            simulations=1000,
            volatilities={"a": 0.1, "b": 0.2},
            correlation_matrix=((1.0, 0.3, 0.4), (0.3, 1.0, 0.5), (0.4, 0.5, 1.0)),
            seeds={"core": 1},
        )


def test_manual_validation_catches_schedule_out_of_range(project_parameters):
    bad_schedule = project_parameters.debt_service_schedule.copy()
    bad_schedule.loc[0, "year"] = max(project_parameters.timeline_years) + 10

    with pytest.raises(ValueError):
        ProjectParameters(
            financials=project_parameters.financials,
            debt=project_parameters.debt,
            operational=project_parameters.operational,
            rate_curve=project_parameters.rate_curve,
            monte_carlo=project_parameters.monte_carlo,
            reserves=project_parameters.reserves,
            covenants=project_parameters.covenants,
            timeline_years=project_parameters.timeline_years,
            debt_service_schedule=bad_schedule,
            rcapex_schedule=project_parameters.rcapex_schedule,
        )
