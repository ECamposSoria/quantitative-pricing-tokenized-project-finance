import numpy as np

from pftoken.amm.core.pool_v2 import ConstantProductPool, PoolConfig, PoolState
from pftoken.amm.pricing.market_price import (
    arbitrage_signal,
    depth_curve,
    execution_price,
    spot_price,
    twap_sampling,
)


def make_pool():
    config = PoolConfig(token0="A", token1="B", fee_bps=30)
    state = PoolState(reserve0=1_000.0, reserve1=1_000.0)
    return ConstantProductPool(config, state)


def test_execution_price_reflects_slippage():
    pool = make_pool()
    p_small = execution_price(pool, amount_in=1.0, side="token0")
    p_large = execution_price(pool, amount_in=200.0, side="token0")
    assert p_large < p_small  # buying more token1 should push price down (token0 in)


def test_depth_curve_monotonic():
    pool = make_pool()
    prices = [0.8, 1.0, 1.2]
    curve = depth_curve(pool, prices)
    depths = curve[:, 1]
    assert depths[0] == 0.0
    assert depths[-1] >= depths[0]


def test_twap_sampling_constant():
    pool = make_pool()
    samples = twap_sampling(pool, intervals=5)
    assert samples.shape == (5,)
    assert np.allclose(samples, spot_price(pool))


def test_arbitrage_signal_threshold():
    sig = arbitrage_signal(pool_price=1.02, reference_price=1.0, threshold=0.01)
    assert sig is not None
    assert sig["direction"] == "sell_pool_buy_reference"
