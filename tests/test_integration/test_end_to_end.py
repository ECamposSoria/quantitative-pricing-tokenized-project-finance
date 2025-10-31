"""Integration test covering CFADS → debt service → ratio calculations."""

import numpy as np

from pftoken.models import (
    ProjectParameters,
    calculate_cfads,
    compute_dscr,
    compute_llcr,
    compute_plcr,
)


def test_cfads_waterfall_integration(project_parameters: ProjectParameters):
    """Validate simple pipeline from CFADS outputs into ratio analytics."""

    params = project_parameters
    years = list(params.timeline_years)

    # 1) Generate CFADS statements for the full horizon.
    statements = [calculate_cfads(params, year=y) for y in years]
    cfads = np.array([stmt.cfads for stmt in statements], dtype=float)

    # Ensure RCAPEX years (5 & 10) drive positive capex and expected CFADS dips.
    capex_by_year = {stmt.year: stmt.capex for stmt in statements}
    assert capex_by_year[5] > 0
    assert capex_by_year[10] > 0
    assert cfads[years.index(5)] < 0
    assert cfads[years.index(10)] < 0

    # 2) Aggregate debt service (interest + principal) per year.
    debt_sched = params.debt_service_schedule.groupby("year")[
        ["interest_due", "principal_due"]
    ].sum()
    debt_service = debt_sched.reindex(years, fill_value=0.0).sum(axis=1).to_numpy()

    # 3) Compute DSCR time series and verify numerical consistency.
    dscr = compute_dscr(cfads, debt_service)
    assert dscr.shape == cfads.shape
    mask_service = debt_service > 0
    assert np.isfinite(dscr[mask_service]).all()

    # 4) Compute LLCR and PLCR using the validated CFADS stream.
    discount_rate = params.rate_curve.base_rate
    initial_debt = sum(tranche.notional for tranche in params.debt.tranches)
    paid_principal_to_year5 = params.debt_service_schedule.loc[
        params.debt_service_schedule["year"] < 5, "principal_due"
    ].sum()
    outstanding_year5 = initial_debt - paid_principal_to_year5

    llcr_year5 = compute_llcr(
        cfads[years.index(5) :], outstanding_year5, discount_rate
    )
    plcr_full = compute_plcr(cfads, initial_debt, discount_rate)

    assert np.isfinite(llcr_year5)
    assert np.isfinite(plcr_full)
    # LLCR should worsen in heavy RCAPEX years but remain finite.
    assert llcr_year5 < plcr_full
