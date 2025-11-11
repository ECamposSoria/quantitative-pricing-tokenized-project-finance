"""Integration smoke test for CFADS → DSCR pipeline."""

import pytest

from pftoken.models import CFADSCalculator, compute_dscr_by_phase


def test_cfads_to_dscr_pipeline(project_parameters):
    calculator = CFADSCalculator.from_project_parameters(project_parameters)
    cfads_vector = calculator.calculate_cfads_vector()

    dscr = compute_dscr_by_phase(
        cfads_vector,
        project_parameters.debt_schedule,
        grace_years=project_parameters.project.grace_period_years,
        tenor_years=project_parameters.project.tenor_years,
    )

    assert len(dscr) == project_parameters.project.tenor_years
    assert dscr[5]["value"] == pytest.approx(1.450, abs=0.001)
    assert dscr[11]["value"] == pytest.approx(1.644, abs=0.001)
