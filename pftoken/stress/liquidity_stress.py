"""
AMM liquidity stress scenarios and metrics for WP-14/WP-09 integration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Sequence

import numpy as np

from pftoken.amm.analysis.impermanent_loss import il_v2
from pftoken.amm.core.pool_v2 import ConstantProductPool
from pftoken.amm.core.pool_v2 import SwapQuote


@dataclass(frozen=True)
class LiquidityStressResult:
    depleted_liquidity: float
    max_drawdown: float


@dataclass(frozen=True)
class ScenarioOutcome:
    name: str
    price_path: np.ndarray
    liquidity_path: np.ndarray
    slippage_curve: np.ndarray
    il: float
    recovery_steps: int


def stress_liquidity(liquidity_series: Iterable[float], shock_fraction: float) -> LiquidityStressResult:
    """
    Apply a proportional liquidity shock and compute stress metrics.
    """
    if not 0 <= shock_fraction <= 1:
        raise ValueError("shock_fraction must lie in [0, 1].")
    series = np.asarray(list(liquidity_series), dtype=float)
    if series.size == 0:
        raise ValueError("liquidity_series cannot be empty.")
    shocked = series * (1 - shock_fraction)
    drawdown = (series - shocked) / series
    return LiquidityStressResult(
        depleted_liquidity=float(series.sum() - shocked.sum()),
        max_drawdown=float(drawdown.max()),
    )


def _price(pool: ConstantProductPool) -> float:
    return pool.price()


def _simulate_sell(pool: ConstantProductPool, sell_fraction: float) -> SwapQuote:
    """Simulate selling token0 into the pool for token1 as stress."""
    amount_in = pool.state.reserve0 * sell_fraction
    return pool.simulate_swap(amount_in, side_in="token0")


def panic_sell_ladder(pool: ConstantProductPool, steps: Sequence[float]) -> ScenarioOutcome:
    prices = []
    liquidity = []
    slippages = []
    base_price = _price(pool)
    for frac in steps:
        quote = _simulate_sell(pool, frac)
        prices.append(_price(pool))
        liquidity.append(pool.state.reserve0 + pool.state.reserve1 / base_price)
        slippages.append((quote.price_after - quote.price_before) / quote.price_before)
    price_path = np.asarray(prices, dtype=float)
    liquidity_path = np.asarray(liquidity, dtype=float)
    il = il_v2(price_path[-1] / price_path[0])
    return ScenarioOutcome(
        name="panic_sell_ladder",
        price_path=price_path,
        liquidity_path=liquidity_path,
        slippage_curve=np.column_stack((steps, np.asarray(slippages, dtype=float))),
        il=il,
        recovery_steps=0,
    )


def lp_withdrawal_cascade(pool: ConstantProductPool, steps: Sequence[float]) -> ScenarioOutcome:
    prices = []
    liquidity = []
    base_price = _price(pool)
    for frac in steps:
        pool.state.reserve0 *= 1 - frac
        pool.state.reserve1 *= 1 - frac
        prices.append(_price(pool))
        liquidity.append(pool.state.reserve0 + pool.state.reserve1 / base_price)
    price_path = np.asarray(prices, dtype=float)
    liquidity_path = np.asarray(liquidity, dtype=float)
    il = il_v2(price_path[-1] / price_path[0]) if price_path[0] > 0 else 0.0
    slippage_curve = np.column_stack((steps, np.zeros(len(steps))))
    return ScenarioOutcome(
        name="lp_withdrawal_cascade",
        price_path=price_path,
        liquidity_path=liquidity_path,
        slippage_curve=slippage_curve,
        il=il,
        recovery_steps=0,
    )


def flash_crash_recovery(pool: ConstantProductPool, drop_fraction: float, recovery_fraction: float) -> ScenarioOutcome:
    base_price = _price(pool)
    crashed_price = base_price * (1 - drop_fraction)
    recovered_price = crashed_price + drop_fraction * recovery_fraction * base_price

    price_path = np.array([base_price, crashed_price, recovered_price], dtype=float)
    liquidity_path = np.array(
        [
            pool.state.reserve0 + pool.state.reserve1 / base_price,
            pool.state.reserve0 + pool.state.reserve1 / crashed_price,
            pool.state.reserve0 + pool.state.reserve1 / recovered_price,
        ],
        dtype=float,
    )
    il = il_v2(recovered_price / base_price)
    recovery_steps = 1 if recovered_price >= base_price * 0.9 else 2
    slippage_curve = np.column_stack(
        ([0.0, drop_fraction, recovery_fraction], np.zeros(3, dtype=float))
    )
    return ScenarioOutcome(
        name="flash_crash_recovery",
        price_path=price_path,
        liquidity_path=liquidity_path,
        slippage_curve=slippage_curve,
        il=il,
        recovery_steps=recovery_steps,
    )


__all__ = [
    "LiquidityStressResult",
    "ScenarioOutcome",
    "stress_liquidity",
    "panic_sell_ladder",
    "lp_withdrawal_cascade",
    "flash_crash_recovery",
]
