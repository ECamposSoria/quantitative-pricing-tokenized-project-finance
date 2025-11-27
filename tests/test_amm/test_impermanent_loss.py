import math

import numpy as np
import pytest

from pftoken.amm.analysis.impermanent_loss import (
    fee_breakeven,
    il_surface,
    il_v2,
    il_v3_range,
    impermanent_loss_series,
)


def test_il_v2_symmetry_and_known_point():
    assert il_v2(1.0) == 0.0
    # Known IL at 4x move ≈ -0.20
    assert il_v2(4.0) == pytest.approx(-0.2, rel=1e-3)


def test_il_v3_range_in_range_and_out_of_range():
    # Price stays inside the range → IL similar magnitude to v2
    il_inside = il_v3_range(price_start=1.0, price_end=1.1, tick_lower=-100, tick_upper=100)
    assert il_inside < 0
    # Price moves far above range → position becomes all token1, IL is negative vs hold
    il_outside = il_v3_range(price_start=1.0, price_end=10.0, tick_lower=-100, tick_upper=100)
    assert il_outside < 0


def test_il_surface_shape_and_values():
    ratios = [0.9, 1.0, 1.1]
    ranges = [(-100, 100), (0, 200)]
    surface = il_surface(ratios, ranges)
    assert surface.shape == (len(ranges), len(ratios))
    assert surface[0, 1] == 0.0  # ratio 1.0 → no IL


def test_fee_breakeven_basic():
    days = fee_breakeven(il_abs=10.0, daily_fees=2.0, holding_period_days=10)
    assert days == 5.0
    assert math.isinf(fee_breakeven(il_abs=10.0, daily_fees=0.0, holding_period_days=10))


def test_impermanent_loss_series_vectorized():
    arr = impermanent_loss_series([1.0, 4.0])
    assert np.allclose(arr, [0.0, il_v2(4.0)])
