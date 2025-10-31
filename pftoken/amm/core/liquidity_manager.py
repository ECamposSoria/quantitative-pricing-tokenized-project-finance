"""
Helpers to manage LP positions for constant-product pools.

The implementation keeps accounting deliberately simple (single pool,
pro-rata shares) so downstream modules can evolve the logic without
rewriting orchestration code.  When integrating with Uniswap-style NFTs,
extend the bookkeeping to support time-varying ranges and fee accrual.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .pool_v2 import ConstantProductPool


@dataclass
class LiquidityPosition:
    owner: str
    shares: float


class LiquidityManager:
    """Minimal LP accounting for a constant-product pool."""

    def __init__(self, pool: ConstantProductPool):
        self.pool = pool
        self._positions: Dict[str, LiquidityPosition] = {}
        self._total_shares = 0.0

    def total_shares(self) -> float:
        return self._total_shares

    def position(self, owner: str) -> LiquidityPosition | None:
        return self._positions.get(owner)

    def deposit(self, owner: str, amount0: float, amount1: float) -> LiquidityPosition:
        """Add liquidity to the pool and mint LP shares."""
        if amount0 <= 0 or amount1 <= 0:
            raise ValueError("Liquidity contributions must be positive.")

        if self._total_shares == 0:
            shares_minted = (amount0 * amount1) ** 0.5
        else:
            shares_minted = min(
                amount0 / self.pool.state.reserve0 * self._total_shares,
                amount1 / self.pool.state.reserve1 * self._total_shares,
            )

        self.pool.add_liquidity(amount0, amount1)
        position = self._positions.get(owner)
        if position:
            position.shares += shares_minted
        else:
            position = LiquidityPosition(owner=owner, shares=shares_minted)
            self._positions[owner] = position

        self._total_shares += shares_minted
        return position

    def withdraw(self, owner: str, share_fraction: float) -> tuple[float, float]:
        """Burn LP shares and withdraw underlying reserves."""
        if owner not in self._positions:
            raise KeyError(f"{owner} has no liquidity position.")
        if not 0 < share_fraction <= 1:
            raise ValueError("share_fraction must be within (0, 1].")

        position = self._positions[owner]
        shares_to_burn = position.shares * share_fraction
        pool_fraction = shares_to_burn / self._total_shares
        amount0, amount1 = self.pool.remove_liquidity(pool_fraction)

        position.shares -= shares_to_burn
        self._total_shares -= shares_to_burn
        if position.shares <= 0:
            del self._positions[owner]
        return amount0, amount1
