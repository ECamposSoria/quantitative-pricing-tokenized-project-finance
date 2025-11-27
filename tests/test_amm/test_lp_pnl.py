import pytest

from pftoken.amm.analysis.lp_pnl import LPPnLDecomposition, pnl_decomposition, pnl_vs_hold


def test_pnl_vs_hold_basic():
    breakdown = pnl_vs_hold(fees_collected=5.0, initial_value=100.0, final_pool_value=102.0, final_hold_value=101.0)
    assert breakdown.fees_earned == 5.0
    assert breakdown.net_pnl == 7.0


def test_pnl_decomposition_v2_defaults():
    result = pnl_decomposition(
        amount0_start=1.0,
        amount1_start=0.0,
        price_start=1.0,
        price_end=2.0,
        fees_earned=1.0,
    )
    assert isinstance(result, LPPnLDecomposition)
    # Price appreciation positive, IL negative for v2 move up
    assert result.price_appreciation > 0
    assert result.impermanent_loss < 0
    assert result.net_pnl == pytest.approx(
        result.fees_earned + result.price_appreciation + result.impermanent_loss
    )


def test_pnl_decomposition_v3_range():
    result = pnl_decomposition(
        amount0_start=1.0,
        amount1_start=0.0,
        price_start=1.0,
        price_end=1.1,
        fees_earned=0.5,
        tick_lower=-100,
        tick_upper=100,
    )
    assert result.net_pnl != 0
