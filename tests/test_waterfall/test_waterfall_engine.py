import pytest

from pftoken.models import ProjectParameters
from pftoken.waterfall import DebtStructure, ReserveState, WaterfallEngine


@pytest.fixture
def waterfall_setup(project_parameters: ProjectParameters):
    debt_structure = DebtStructure.from_tranche_params(project_parameters.tranches)
    debt_schedule = project_parameters.debt_schedule
    rcapex = project_parameters.rcapex_schedule
    reserves = ReserveState(
        dsra_months_cover=project_parameters.project.dsra_months_cover,
        mra_target_pct=project_parameters.project.mra_target_pct_next_rcapex,
    )
    engine = WaterfallEngine()
    return engine, debt_structure, debt_schedule, rcapex, reserves


def test_waterfall_grace_period_interest_only(waterfall_setup):
    engine, debt_structure, debt_schedule, rcapex, reserves = waterfall_setup
    result = engine.execute_waterfall(
        year=1,
        cfads_available=-0.6,
        debt_structure=debt_structure,
        debt_schedule=debt_schedule,
        reserves=reserves,
        dscr_value=-0.113,
        rcapex_schedule=rcapex,
    )
    assert sum(result.principal_payments.values()) == 0
    assert "payment_shortfall" in result.events
    assert result.dsra_funding >= 0


def test_waterfall_amortization_year_five(waterfall_setup):
    engine, debt_structure, debt_schedule, rcapex, reserves = waterfall_setup
    result = engine.execute_waterfall(
        year=5,
        cfads_available=12.4,
        debt_structure=debt_structure,
        debt_schedule=debt_schedule,
        reserves=reserves,
        dscr_value=1.45,
        rcapex_schedule=rcapex,
    )
    assert sum(result.principal_payments.values()) > 0
    assert result.cash_sweep == 0
    assert "payment_shortfall" not in result.events
