import math

import pytest

from pftoken.amm.core.pool_v3 import ConcentratedLiquidityPool
from pftoken.amm.core.sqrt_price_math import Q96, sqrt_price_x96_to_tick, tick_to_sqrt_price_x96


def test_tick_roundtrip():
    tick = 1500
    sqrt_price = tick_to_sqrt_price_x96(tick)
    recovered = sqrt_price_x96_to_tick(sqrt_price)
    assert recovered == pytest.approx(tick, rel=1e-3)


def test_swap_within_single_range_zero_for_one():
    pool = ConcentratedLiquidityPool("t0", "t1", fee_bps=5, current_tick=0)
    pool.add_position("lp1", -1000, 1000, liquidity=10_000.0)

    result = pool.simulate_swap(100.0, "token0")
    assert result.amount_out > 0
    assert result.fee_paid > 0
    assert result.ticks_crossed == 0

    sqrt_after = result.final_sqrt_price_x96 / Q96
    assert sqrt_after < 1.0  # price should decrease on token0 in

    price_after = sqrt_after**2
    assert price_after < 1.0


def test_crosses_initialized_tick_on_large_swap():
    pool = ConcentratedLiquidityPool("t0", "t1", fee_bps=5, current_tick=0)
    pool.add_position("lp_low", -200, 0, liquidity=5_000.0)
    pool.add_position("lp_high", 0, 200, liquidity=5_000.0)

    result = pool.simulate_swap(200.0, "token0")

    assert result.ticks_crossed >= 1
    assert result.final_tick <= -200
    assert result.amount_out > 0
    assert result.fee_paid > 0


def test_one_for_zero_increases_price():
    pool = ConcentratedLiquidityPool("t0", "t1", fee_bps=5, current_tick=0)
    pool.add_position("lp_mid", -100, 100, liquidity=8_000.0)

    result = pool.simulate_swap(150.0, "token1")

    sqrt_after = result.final_sqrt_price_x96 / Q96
    assert sqrt_after > 1.0
    assert result.amount_out > 0
    assert result.ticks_crossed >= 0
