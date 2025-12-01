import math

from pftoken.models import CFADSCalculator, ProjectParameters, RatioCalculator


def _relative_error(modeled: float, baseline: float) -> float:
    if baseline == 0:
        return abs(modeled - baseline)
    return abs((modeled - baseline) / baseline)


def test_dscr_matches_excel(cfads_calculator, project_parameters: ProjectParameters):
    cfads_vector = cfads_calculator.calculate_cfads_vector()
    ratio_calc = RatioCalculator(
        cfads_vector,
        project_parameters.debt_schedule,
        tranches=project_parameters.tranches,
    )
    results = ratio_calc.dscr_by_year(
        project_parameters.project.grace_period_years,
        project_parameters.project.tenor_years,
    )
    expected = {
        4: 1.3559322033898304,
        5: 1.5061420838568895,
        11: 2.8288579514696566,
    }
    for year, baseline in expected.items():
        modeled = results[year].value
        assert _relative_error(modeled, baseline) <= 1e-4


def test_llcr_per_tranche(cfads_calculator, project_parameters: ProjectParameters):
    """Test LLCR with cumulative debt by seniority.

    LLCR for each tranche = NPV(CFADS) / Cumulative debt up to that tranche.
    - Senior: NPV / Senior debt (most coverage)
    - Mezzanine: NPV / (Senior + Mezzanine debt)
    - Subordinated: NPV / Total debt (least coverage)
    """
    cfads_vector = cfads_calculator.calculate_cfads_vector()
    ratio_calc = RatioCalculator(
        cfads_vector,
        project_parameters.debt_schedule,
        tranches=project_parameters.tranches,
    )
    llcr = ratio_calc.llcr_by_tranche()

    # Sort tranches by priority_level (lower = more senior)
    sorted_tranches = sorted(project_parameters.tranches, key=lambda t: t.priority_level)

    # Calculate expected LLCR with cumulative debt
    cumulative_debt = 0.0
    weighted_coupon = sum(t.coupon_rate * t.initial_principal for t in sorted_tranches) / sum(t.initial_principal for t in sorted_tranches)

    for tranche in sorted_tranches:
        cumulative_debt += tranche.initial_principal / 1_000_000.0
        expected = _manual_llcr(cfads_vector, weighted_coupon, cumulative_debt)
        modeled = llcr[tranche.name].value
        assert _relative_error(modeled, expected) <= 1e-4, f"LLCR mismatch for {tranche.name}: {modeled:.2f} vs {expected:.2f}"
        assert modeled >= llcr[tranche.name].threshold

    # Verify Senior has highest LLCR (most coverage)
    senior_llcr = llcr[sorted_tranches[0].name].value
    sub_llcr = llcr[sorted_tranches[-1].name].value
    assert senior_llcr > sub_llcr, "Senior should have higher LLCR than Subordinated"


def test_plcr_alignment(cfads_calculator, project_parameters: ProjectParameters):
    cfads_vector = cfads_calculator.calculate_cfads_vector()
    ratio_calc = RatioCalculator(
        cfads_vector,
        project_parameters.debt_schedule,
        tranches=project_parameters.tranches,
    )
    modeled = ratio_calc.plcr()
    expected = _manual_plcr(cfads_vector, project_parameters.tranches)
    assert _relative_error(modeled, expected) <= 1e-4


def _manual_llcr(cfads_vector, discount_rate: float, outstanding_musd: float) -> float:
    npv = 0.0
    for year, cfads in sorted(cfads_vector.items()):
        npv += cfads / math.pow(1 + discount_rate, year)
    return npv / outstanding_musd


def _manual_plcr(cfads_vector, tranches):
    total_principal = sum(tr.initial_principal for tr in tranches) / 1_000_000.0
    weighted_coupon = sum(tr.coupon_rate * tr.initial_principal for tr in tranches) / sum(
        tr.initial_principal for tr in tranches
    )
    npv = 0.0
    for year, cfads in sorted(cfads_vector.items()):
        npv += cfads / math.pow(1 + weighted_coupon, year)
    return npv / total_principal
