from pftoken.models import ProjectParameters


def test_project_parameters_basic_loading(project_parameters: ProjectParameters):
    project = project_parameters.project
    assert project.analysis_horizon_years == 15
    assert project.grace_period_years == 4
    assert project.ramping_period_months == 24

    tranches = project_parameters.tranches
    assert len(tranches) == 3
    assert tranches[0].name == "senior"
    assert tranches[0].initial_principal == 43_200_000

    cfads_df = project_parameters.cfads_dataframe()
    assert cfads_df.shape[0] == project.analysis_horizon_years

    debt_columns = set(project_parameters.debt_schedule.columns)
    assert {"year", "tranche_name", "interest_due", "principal_due"}.issubset(debt_columns)
