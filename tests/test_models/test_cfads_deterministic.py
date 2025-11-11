import pytest

from pftoken.config.defaults import INITIAL_DSRA_FUNDING_MUSD, RCAPEX_DIET_MUSD


def test_cfads_components_match_excel(cfads_calculator):
    """Ensure modeled CFADS stays within 0.01% of the Excel baseline."""
    for result in cfads_calculator.cfads_results:
        assert result.relative_error <= 1e-4


def test_cfads_total_cfads_sum(cfads_calculator):
    vector = cfads_calculator.calculate_cfads_vector()
    assert sum(vector.values()) == pytest.approx(196.5, abs=1e-3)


def test_rcapex_diet_locked(project_parameters):
    schedule = project_parameters.rcapex_schedule
    for year, target in RCAPEX_DIET_MUSD.items():
        actual = float(schedule.loc[schedule["year"] == year, "rcapex_amount"].iloc[0])
        assert actual == pytest.approx(target, abs=1e-6)


def test_dsra_baseline_constant():
    assert INITIAL_DSRA_FUNDING_MUSD == pytest.approx(18.0, abs=1e-6)
