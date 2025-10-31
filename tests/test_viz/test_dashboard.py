import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.figure as mpl_fig

from pftoken.models import ProjectParameters
from pftoken.viz import dashboards


def test_build_financial_dashboard(project_parameters: ProjectParameters):
    figures = dashboards.build_financial_dashboard(project_parameters)
    assert set(figures.keys()) == {
        "cfads_vs_debt_service",
        "dscr_timeseries",
        "ratio_snapshot",
        "capital_structure",
    }
    for fig in figures.values():
        assert isinstance(fig, mpl_fig.Figure)
