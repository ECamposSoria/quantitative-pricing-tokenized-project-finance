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
        4: 0.941619586,  # Excel `Ratios` tab baseline
        5: 1.45,
        11: 1.644014,
    }
    for year, baseline in expected.items():
        modeled = results[year].value
        assert _relative_error(modeled, baseline) <= 1e-4


def test_llcr_per_tranche(cfads_calculator, project_parameters: ProjectParameters):
    cfads_vector = cfads_calculator.calculate_cfads_vector()
    ratio_calc = RatioCalculator(
        cfads_vector,
        project_parameters.debt_schedule,
        tranches=project_parameters.tranches,
    )
    llcr = ratio_calc.llcr_by_tranche()
    for tranche in project_parameters.tranches:
        expected = _manual_llcr(cfads_vector, tranche.coupon_rate, tranche.initial_principal / 1_000_000.0)
        modeled = llcr[tranche.name].value
        assert _relative_error(modeled, expected) <= 1e-4
        assert modeled >= llcr[tranche.name].threshold


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
