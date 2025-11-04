import pytest

from pftoken.models import CFADSScenarioInputs, calculate_cfads


def test_cfads_baseline_positive_cfads(project_parameters):
    statement = calculate_cfads(project_parameters, year=5)
    assert statement.year == 5
    assert statement.revenue > 0
    assert statement.cfads != 0
    assert statement.ebitda == pytest.approx(statement.revenue - statement.opex, rel=1e-6)


def test_cfads_revenue_scales_with_arpu(project_parameters):
    base = calculate_cfads(project_parameters, year=6)
    higher_arpu = calculate_cfads(
        project_parameters,
        year=6,
        scenario=CFADSScenarioInputs(arpu_multiplier=1.1),
    )
    assert higher_arpu.revenue > base.revenue
    assert higher_arpu.cfads > base.cfads


def test_cfads_invalid_year_raises(project_parameters):
    with pytest.raises(ValueError):
        calculate_cfads(project_parameters, year=99)


def test_cfads_rcapex_recorded_but_not_deducted(project_parameters):
    statement = calculate_cfads(project_parameters, year=5)
    assert statement.rcapex_investment > 0
    assert statement.cfads > 0
