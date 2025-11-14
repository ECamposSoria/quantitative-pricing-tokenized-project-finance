"""Zero curve construction tests."""

from __future__ import annotations

import math

import pytest

from pftoken.pricing.zero_curve import CurveInstrument, ZeroCurve


def test_bootstrap_flat_curve_produces_expected_rates():
    instruments = [
        CurveInstrument(maturity_years=year, rate=0.05, instrument_type="deposit")
        for year in range(1, 6)
    ]
    curve = ZeroCurve.bootstrap(instruments, currency="USD")
    assert len(curve.points) == 5
    assert pytest.approx(curve.spot_rate(3.0), rel=1e-6) == 0.05
    df_3 = curve.discount_factor(3.0)
    assert pytest.approx(df_3, rel=1e-6) == (1 / (1.05**3))


def test_apply_shock_adjusts_rates():
    base = ZeroCurve.bootstrap([CurveInstrument(maturity_years=1, rate=0.04)], currency="USD")
    shocked = base.apply_shock(parallel_bps=50)
    assert pytest.approx(shocked.spot_rate(1.0), rel=1e-6) == 0.045
    bucketed = base.apply_shock(bucket_shocks={(0, 1.5): 25})
    assert pytest.approx(bucketed.spot_rate(1.0), rel=1e-6) == 0.0425


def test_forward_rate_consistency():
    instruments = [
        CurveInstrument(maturity_years=year, rate=0.03 + 0.002 * year, instrument_type="deposit")
        for year in range(1, 5)
    ]
    curve = ZeroCurve.bootstrap(instruments, currency="USD")
    fwd = curve.forward_rate(1.0, 2.0)
    df1 = curve.discount_factor(1.0)
    df2 = curve.discount_factor(2.0)
    expected = (df1 / df2) - 1.0
    assert math.isclose(fwd, expected, rel_tol=1e-6)

