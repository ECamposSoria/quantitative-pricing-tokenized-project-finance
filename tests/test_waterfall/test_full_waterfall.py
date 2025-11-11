import pytest

from pftoken.models import CFADSCalculator, ProjectParameters
from pftoken.waterfall import DebtStructure, WaterfallOrchestrator


def _relative_error(modeled: float, baseline: float) -> float:
    if baseline == 0:
        return abs(modeled - baseline)
    return abs((modeled - baseline) / baseline)


def test_full_waterfall_matches_debt_schedule(
    project_parameters: ProjectParameters, cfads_calculator: CFADSCalculator
):
    debt_structure = DebtStructure.from_tranche_params(project_parameters.tranches)
    orchestrator = WaterfallOrchestrator(
        cfads_vector=cfads_calculator.calculate_cfads_vector(),
        debt_structure=debt_structure,
        debt_schedule=project_parameters.debt_schedule,
        rcapex_schedule=project_parameters.rcapex_schedule,
        grace_period_years=project_parameters.project.grace_period_years,
        tenor_years=project_parameters.project.tenor_years,
    )
    result = orchestrator.run()

    assert len(result.periods) == project_parameters.project.tenor_years
    assert result.equity_cashflows[0] == pytest.approx(-18_000_000, abs=1)
    expected_interest = (
        project_parameters.debt_schedule.groupby(["year", "tranche_name"])["interest_due"].sum()
    )
    expected_principal = (
        project_parameters.debt_schedule.groupby(["year", "tranche_name"])["principal_due"].sum()
    )

    for period in result.periods:
        for tranche in debt_structure.tranches:
            key = (period.year, tranche.name)
            modeled_interest = period.interest_payments.get(tranche.name, 0.0)
            modeled_principal = period.principal_payments.get(tranche.name, 0.0)
            exp_interest = float(expected_interest.get(key, 0.0))
            exp_principal = float(expected_principal.get(key, 0.0))
            assert _relative_error(modeled_interest, exp_interest) <= 1e-4
            assert _relative_error(modeled_principal, exp_principal) <= 1e-4

    assert len(result.dsra_series) == len(result.periods) + 1
    assert len(result.mra_series) == len(result.periods) + 1
    assert result.total_dividends >= 0
    assert result.equity_irr >= 0
