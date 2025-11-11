import math

from scipy.stats import norm

from pftoken.models import (
    CFADSCalculator,
    ProjectParameters,
    load_placeholder_calibration,
)
from pftoken.models.merton import MertonModel


def test_merton_pd_lgd_el(cfads_calculator: CFADSCalculator, project_parameters: ProjectParameters):
    calibration = load_placeholder_calibration()
    cfads_vector = cfads_calculator.calculate_cfads_vector()
    model = MertonModel(
        cfads_vector,
        project_parameters.tranches,
        discount_rate=project_parameters.project.base_rate_reference,
        calibration=calibration,
    )
    results = model.run()

    asset_value = _pv_cfads(cfads_vector, project_parameters.project.base_rate_reference)
    horizon = len(cfads_vector)

    ordered = ["senior", "mezzanine", "subordinated"]
    for name in ordered:
        res = results[name]
        cal = calibration.params[name]
        debt = next(tr.initial_principal for tr in project_parameters.tranches if tr.name == name) / 1_000_000.0
        dd = (
            math.log(asset_value / debt)
            + (project_parameters.project.base_rate_reference - 0.5 * cal.asset_volatility**2) * horizon
        ) / (cal.asset_volatility * math.sqrt(horizon))
        expected_pd = max(norm.cdf(-dd), cal.pd_floor)
        expected_lgd = 1.0 - cal.recovery_rate
        assert math.isclose(res.pd, expected_pd, rel_tol=1e-4)
        assert math.isclose(res.lgd, expected_lgd, rel_tol=1e-4)
        assert math.isclose(res.expected_loss, expected_pd * expected_lgd, rel_tol=1e-4)
        assert res.pd >= cal.pd_floor
        assert res.distance_to_default == res.distance_to_default  # finite


def _pv_cfads(cfads_vector, discount_rate):
    npv = 0.0
    for idx, (_, cfads) in enumerate(sorted(cfads_vector.items()), start=1):
        npv += cfads / (1 + discount_rate) ** idx
    return npv
