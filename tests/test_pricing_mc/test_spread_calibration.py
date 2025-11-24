import numpy as np

from pftoken.pricing_mc.spread_calibration import CalibrationPoint, SpreadCalibrator
from pftoken.pricing_mc.spread_calibration import SpreadCalibrationResult


def test_spread_calibrator_fits_expected_relationship():
    # Synthetic linear relationship with known coefficients.
    # spread = 50 + 120*(pd*lgd) + 10*liq + 2*tenor + 0.5*base
    points = []
    rng = np.random.default_rng(42)
    for _ in range(30):
        pd = rng.uniform(0.01, 0.05)
        lgd = rng.uniform(0.3, 0.6)
        tenor = rng.uniform(1, 10)
        liquidity = rng.uniform(0.1, 1.0)
        base = rng.uniform(50, 200)
        spread = 50 + 120 * (pd * lgd) + 10 * liquidity + 2 * tenor + 0.5 * base
        points.append(
            CalibrationPoint(
                rating="BBB",
                tenor_years=tenor,
                pd=pd,
                lgd=lgd,
                observed_spread_bps=spread,
                liquidity_proxy=liquidity,
                base_spread_bps=base,
            )
        )

    calibrator = SpreadCalibrator()
    result = calibrator.fit(points)

    # Predict on a new point; allow loose tolerance to account for ridge/rounding.
    pred = calibrator.predict(pd=0.03, lgd=0.4, tenor_years=5, liquidity_proxy=0.5, base_spread_bps=100, rating="BBB")
    expected = 50 + 120 * (0.03 * 0.4) + 10 * 0.5 + 2 * 5 + 0.5 * 100
    assert result.rmse < 1e-6
    assert abs(pred - expected) < 1e-4


def test_ridge_regularization_shrinks_coefficients():
    points = [
        CalibrationPoint(rating=None, tenor_years=5, pd=0.02, lgd=0.5, observed_spread_bps=200, liquidity_proxy=0.5, base_spread_bps=80),
        CalibrationPoint(rating=None, tenor_years=7, pd=0.03, lgd=0.6, observed_spread_bps=260, liquidity_proxy=0.6, base_spread_bps=90),
        CalibrationPoint(rating=None, tenor_years=10, pd=0.04, lgd=0.55, observed_spread_bps=310, liquidity_proxy=0.7, base_spread_bps=110),
    ]
    calibrator_no_ridge = SpreadCalibrator(lambda_ridge=0.0)
    calibrator_ridge = SpreadCalibrator(lambda_ridge=1.0)
    res_no_ridge = calibrator_no_ridge.fit(points)
    res_ridge = calibrator_ridge.fit(points)

    # Compare magnitude of slope coefficients (pd_lgd) to ensure ridge shrinks them.
    coef_no_ridge = res_no_ridge.coefficients["global"]["pd_lgd"]
    coef_ridge = res_ridge.coefficients["global"]["pd_lgd"]
    assert abs(coef_ridge) < abs(coef_no_ridge)


def test_calibration_result_serialization_roundtrip():
    original = SpreadCalibrationResult(
        coefficients={"global": {"intercept": 1.0, "pd_lgd": 2.0, "liquidity_proxy": 3.0, "tenor_years": 4.0, "base_spread_bps": 5.0}},
        rmse=0.1,
        r2=0.9,
        num_points=5,
    )
    restored = SpreadCalibrationResult.from_dict(original.to_dict())
    assert restored.coefficients == original.coefficients
    assert restored.rmse == original.rmse
    assert restored.r2 == original.r2
    assert restored.num_points == original.num_points
