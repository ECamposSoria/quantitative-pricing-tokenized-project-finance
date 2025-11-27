"""Concentrated-liquidity pool (Uniswap v3 style) with swap simulation."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Literal, Optional

from .sqrt_price_math import (
    MAX_SQRT_PRICE_X96,
    MIN_SQRT_PRICE_X96,
    Q96,
    get_amount0_delta,
    get_amount1_delta,
    sqrt_price_x96_to_tick,
    tick_to_sqrt_price_x96,
)

Side = Literal["token0", "token1"]


@dataclass(frozen=True)
class RangePosition:
    owner: str
    lower_tick: int
    upper_tick: int
    liquidity: float

    def contains(self, tick: int) -> bool:
        return self.lower_tick <= tick < self.upper_tick


@dataclass(frozen=True)
class SwapResult:
    amount_in: float
    amount_out: float
    fee_paid: float
    final_sqrt_price_x96: int
    final_tick: int
    ticks_crossed: int


@dataclass
class ConcentratedLiquidityPool:
    token0: str
    token1: str
    fee_bps: int = 5  # 0.05% default like many v3 pools
    current_tick: int = 0
    sqrt_price_x96: Optional[int] = None
    positions: List[RangePosition] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.sqrt_price_x96 is None:
            self.sqrt_price_x96 = tick_to_sqrt_price_x96(self.current_tick)
        if self.fee_bps < 0:
            raise ValueError("Fee basis points must be non-negative.")

    # ---------------------------- liquidity management ---------------------
    def active_liquidity(self) -> float:
        """Aggregate liquidity for the current tick."""
        return self._liquidity_at_tick(self.current_tick)

    def add_position(self, owner: str, lower_tick: int, upper_tick: int, liquidity: float) -> None:
        if lower_tick >= upper_tick:
            raise ValueError("lower_tick must be strictly less than upper_tick.")
        if liquidity <= 0:
            raise ValueError("liquidity must be positive.")
        self.positions.append(
            RangePosition(owner=owner, lower_tick=lower_tick, upper_tick=upper_tick, liquidity=liquidity)
        )

    def remove_position(self, owner: str, lower_tick: int, upper_tick: int) -> None:
        self.positions = [
            pos
            for pos in self.positions
            if not (pos.owner == owner and pos.lower_tick == lower_tick and pos.upper_tick == upper_tick)
        ]

    def exposure_by_range(self) -> Dict[tuple[int, int], float]:
        """Summarize liquidity distribution by (lower_tick, upper_tick)."""
        buckets: Dict[tuple[int, int], float] = {}
        for pos in self.positions:
            key = (pos.lower_tick, pos.upper_tick)
            buckets[key] = buckets.get(key, 0.0) + pos.liquidity
        return buckets

    # ---------------------------- pricing helpers -------------------------
    def set_current_tick(self, new_tick: int) -> None:
        self.current_tick = new_tick
        self.sqrt_price_x96 = tick_to_sqrt_price_x96(new_tick)

    def price_estimate(self) -> float:
        sqrt_price = self.sqrt_price_x96 / Q96
        return sqrt_price**2

    def list_positions(self) -> Iterable[RangePosition]:
        return tuple(self.positions)

    # ---------------------------- swap simulation -------------------------
    def simulate_swap(self, amount_in: float, side_in: Side) -> SwapResult:
        if amount_in <= 0:
            raise ValueError("Swap amount must be positive.")
        if side_in not in ("token0", "token1"):
            raise ValueError("side_in must be 'token0' or 'token1'.")

        zero_for_one = side_in == "token0"
        fee_fraction = self.fee_bps / 10_000

        sqrt_price = self.sqrt_price_x96 / Q96
        tick = self.current_tick
        liquidity = self._liquidity_at_tick(tick)
        if liquidity <= 0:
            raise ValueError("No active liquidity at the current tick.")

        liquidity_net = self._build_liquidity_net()
        amount_remaining = amount_in
        amount_out = 0.0
        fee_paid = 0.0
        ticks_crossed = 0

        while amount_remaining > 0 and liquidity > 0:
            target_tick = self._get_next_initialized_tick(tick, zero_for_one, liquidity_net)
            if target_tick is None:
                target_sqrt = MIN_SQRT_PRICE_X96 / Q96 if zero_for_one else MAX_SQRT_PRICE_X96 / Q96
            else:
                target_sqrt = tick_to_sqrt_price_x96(target_tick) / Q96

            step = self._compute_swap_step(
                sqrt_price=sqrt_price,
                target_sqrt=target_sqrt,
                liquidity=liquidity,
                amount_in=amount_remaining,
                fee_fraction=fee_fraction,
                zero_for_one=zero_for_one,
            )

            amount_remaining -= step["gross_in"]
            amount_out += step["amount_out"]
            fee_paid += step["fee_paid"]
            sqrt_price = step["next_sqrt"]

            if step["reached_target"] and target_tick is not None:
                ticks_crossed += 1
                liquidity = self._cross_tick(
                    tick_boundary=target_tick,
                    liquidity=liquidity,
                    liquidity_net=liquidity_net,
                    zero_for_one=zero_for_one,
                )
                tick = target_tick - 1 if zero_for_one else target_tick
            else:
                tick = sqrt_price_x96_to_tick(int(sqrt_price * Q96))

        self.current_tick = tick
        self.sqrt_price_x96 = int(sqrt_price * Q96)
        return SwapResult(
            amount_in=amount_in,
            amount_out=amount_out,
            fee_paid=fee_paid,
            final_sqrt_price_x96=self.sqrt_price_x96,
            final_tick=self.current_tick,
            ticks_crossed=ticks_crossed,
        )

    # ---------------------------- internals -------------------------------
    def _liquidity_at_tick(self, tick: int) -> float:
        return sum(pos.liquidity for pos in self.positions if pos.contains(tick))

    def _build_liquidity_net(self) -> Dict[int, float]:
        net: Dict[int, float] = {}
        for pos in self.positions:
            net[pos.lower_tick] = net.get(pos.lower_tick, 0.0) + pos.liquidity
            net[pos.upper_tick] = net.get(pos.upper_tick, 0.0) - pos.liquidity
        return net

    def _get_next_initialized_tick(
        self, tick: int, zero_for_one: bool, liquidity_net: Dict[int, float]
    ) -> Optional[int]:
        if not liquidity_net:
            return None
        ticks = sorted(liquidity_net.keys())
        if zero_for_one:
            below = [t for t in ticks if t <= tick]
            if not below:
                return None
            return below[-1] if below[-1] < tick else (below[-2] if len(below) > 1 else None)
        above = [t for t in ticks if t > tick]
        if not above:
            return None
        return above[0]

    def _cross_tick(
        self, tick_boundary: int, liquidity: float, liquidity_net: Dict[int, float], zero_for_one: bool
    ) -> float:
        delta = liquidity_net.get(tick_boundary, 0.0)
        if zero_for_one:
            return liquidity - delta
        return liquidity + delta

    def _compute_swap_step(
        self,
        sqrt_price: float,
        target_sqrt: float,
        liquidity: float,
        amount_in: float,
        fee_fraction: float,
        zero_for_one: bool,
    ) -> Dict[str, float | bool]:
        net_available = amount_in * (1 - fee_fraction)

        if zero_for_one:
            amount0_needed = get_amount0_delta(sqrt_price * Q96, target_sqrt * Q96, liquidity)
            if net_available + 1e-18 >= amount0_needed:
                amount_out = get_amount1_delta(sqrt_price * Q96, target_sqrt * Q96, liquidity)
                gross_in = amount0_needed / (1 - fee_fraction)
                next_sqrt = target_sqrt
                reached_target = True
            else:
                gross_in = amount_in
                next_sqrt = 1.0 / (1.0 / sqrt_price + net_available / liquidity)
                amount_out = liquidity * (sqrt_price - next_sqrt)
                reached_target = False
        else:
            amount1_needed = get_amount1_delta(sqrt_price * Q96, target_sqrt * Q96, liquidity)
            if net_available + 1e-18 >= amount1_needed:
                amount_out = get_amount0_delta(sqrt_price * Q96, target_sqrt * Q96, liquidity)
                gross_in = amount1_needed / (1 - fee_fraction)
                next_sqrt = target_sqrt
                reached_target = True
            else:
                gross_in = amount_in
                next_sqrt = sqrt_price + net_available / liquidity
                amount_out = liquidity * (1.0 / sqrt_price - 1.0 / next_sqrt)
                reached_target = False

        net_in_used = gross_in * (1 - fee_fraction)
        fee_paid = gross_in - net_in_used
        return {
            "gross_in": gross_in,
            "fee_paid": fee_paid,
            "amount_out": amount_out,
            "next_sqrt": next_sqrt,
            "reached_target": reached_target,
        }


__all__ = ["ConcentratedLiquidityPool", "RangePosition", "SwapResult"]
