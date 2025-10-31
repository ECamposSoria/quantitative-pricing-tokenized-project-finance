"""
Constant product AMM pool (Uniswap v2 style) with simple swap math.

This module purposefully keeps the API narrow so it can act as scaffolding
for future quantitative extensions (stress propagation, scenario analysis,
etc.).  The formulas implemented here follow the official invariant
definition `x * y = k` and apply a fee on the input leg, mirroring the v2
whitepaper.  All numbers are handled as Python floats to stay lightweight;
replace them with fixed-point types when integrating on-chain data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Tuple


TokenSide = Literal["token0", "token1"]


@dataclass(frozen=True)
class PoolConfig:
    """Immutable metadata describing the pool."""

    token0: str
    token1: str
    fee_bps: int = 30  # 0.30% default

    def fee_fraction(self) -> float:
        return self.fee_bps / 10_000


@dataclass
class PoolState:
    """Mutable reserves for the constant product invariant."""

    reserve0: float
    reserve1: float

    def invariant(self) -> float:
        return self.reserve0 * self.reserve1


@dataclass(frozen=True)
class SwapQuote:
    """Result of simulating a swap on the pool."""

    amount_in: float
    amount_out: float
    price_before: float
    price_after: float
    fee_paid: float


class ConstantProductPool:
    """Lightweight constant product pool model."""

    def __init__(self, config: PoolConfig, state: PoolState):
        if state.reserve0 <= 0 or state.reserve1 <= 0:
            raise ValueError("Pool reserves must be positive.")
        if config.fee_bps < 0:
            raise ValueError("Fee basis points must be non-negative.")

        self.config = config
        self.state = state

    def price(self) -> float:
        """Return price of token0 denominated in token1."""
        return self.state.reserve1 / self.state.reserve0

    def simulate_swap(self, amount_in: float, side_in: TokenSide) -> SwapQuote:
        """
        Pure simulation of a swap.

        Parameters
        ----------
        amount_in:
            Quantity of the input asset.
        side_in:
            `token0` if token0 is provided, otherwise `token1`.
        """
        if amount_in <= 0:
            raise ValueError("Swap amount must be positive.")
        if side_in not in ("token0", "token1"):
            raise ValueError("side_in must be 'token0' or 'token1'.")

        fee_fraction = self.config.fee_fraction()
        fee_paid = amount_in * fee_fraction
        net_amount = amount_in - fee_paid

        if side_in == "token0":
            return self._simulate_swap_token0(
                gross_in=amount_in,
                net_in=net_amount,
                fee_paid=fee_paid,
            )

        return self._simulate_swap_token1(
            gross_in=amount_in,
            net_in=net_amount,
            fee_paid=fee_paid,
        )

    def execute_swap(self, amount_in: float, side_in: TokenSide) -> SwapQuote:
        """Simulate and mutate state to reflect the swap."""
        quote = self.simulate_swap(amount_in, side_in)
        if side_in == "token0":
            self.state.reserve0 += quote.amount_in - quote.fee_paid
            self.state.reserve1 -= quote.amount_out
        else:
            self.state.reserve1 += quote.amount_in - quote.fee_paid
            self.state.reserve0 -= quote.amount_out
        return quote

    def add_liquidity(self, delta0: float, delta1: float) -> None:
        """Add liquidity while preserving pool proportions."""
        if delta0 <= 0 or delta1 <= 0:
            raise ValueError("Liquidity increments must be positive.")
        ratio_before = self.state.reserve0 / self.state.reserve1
        ratio_after = (self.state.reserve0 + delta0) / (self.state.reserve1 + delta1)
        if abs(ratio_before - ratio_after) > 1e-6:
            raise ValueError("Liquidity must be added proportionally to reserves.")

        self.state.reserve0 += delta0
        self.state.reserve1 += delta1

    def remove_liquidity(self, share: float) -> Tuple[float, float]:
        """Remove liquidity pro-rata."""
        if not 0 < share <= 1:
            raise ValueError("Share must be in the interval (0, 1].")
        delta0 = self.state.reserve0 * share
        delta1 = self.state.reserve1 * share
        self.state.reserve0 -= delta0
        self.state.reserve1 -= delta1
        return delta0, delta1

    def _simulate_swap_token0(
        self,
        gross_in: float,
        net_in: float,
        fee_paid: float,
    ) -> SwapQuote:
        price_before = self.price()
        new_reserve0 = self.state.reserve0 + net_in
        k = self.state.invariant()
        new_reserve1 = k / new_reserve0
        amount_out = self.state.reserve1 - new_reserve1
        price_after = new_reserve1 / new_reserve0
        return SwapQuote(
            amount_in=gross_in,
            amount_out=amount_out,
            price_before=price_before,
            price_after=price_after,
            fee_paid=fee_paid,
        )

    def _simulate_swap_token1(
        self,
        gross_in: float,
        net_in: float,
        fee_paid: float,
    ) -> SwapQuote:
        price_before = self.price()
        new_reserve1 = self.state.reserve1 + net_in
        k = self.state.invariant()
        new_reserve0 = k / new_reserve1
        amount_out = self.state.reserve0 - new_reserve0
        price_after = new_reserve1 / new_reserve0
        return SwapQuote(
            amount_in=gross_in,
            amount_out=amount_out,
            price_before=price_before,
            price_after=price_after,
            fee_paid=fee_paid,
        )
