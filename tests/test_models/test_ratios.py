import pytest

from pftoken.models import compute_dscr_by_phase


@pytest.fixture
def dscr_results(cfads_calculator, project_parameters):
    vector = cfads_calculator.calculate_cfads_vector()
    params = project_parameters.project
    schedule = project_parameters.debt_schedule
    return compute_dscr_by_phase(
        vector,
        schedule,
        grace_years=params.grace_period_years,
        tenor_years=params.tenor_years,
    )


def test_dscr_grace_year_four(dscr_results):
    assert dscr_results[4]["value"] == pytest.approx(0.942, abs=0.001)


def test_dscr_amortization_year_five(dscr_results):
    assert dscr_results[5]["value"] == pytest.approx(1.450, abs=0.001)


def test_dscr_steady_state_year_eleven(dscr_results):
    assert dscr_results[11]["value"] == pytest.approx(1.644, abs=0.001)
