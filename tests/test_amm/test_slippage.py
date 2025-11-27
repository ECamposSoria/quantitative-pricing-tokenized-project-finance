import numpy as np

from pftoken.amm.pricing.slippage import aggregate_slippage, slippage_curve, slippage_percent


def test_slippage_percent_positive_move():
    assert slippage_percent(100, 105) == 0.05


def test_aggregate_slippage():
    vals = [0.01, -0.02, 0.03]
    agg = aggregate_slippage(vals)
    assert agg == np.mean(np.abs(vals))


def test_slippage_curve_increasing_sizes():
    base_price = 1.0

    def price_after(size):
        return base_price * (1 - 0.001 * size)

    curve = slippage_curve(base_price, sizes=[1, 5, 10], price_after_fn=price_after)
    slippages = curve[:, 1]
    assert slippages[2] < slippages[0]  # more negative slippage for bigger size
