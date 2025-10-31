"""
Swap execution helpers that sit on top of the pool abstractions.

The engine simply validates intent payloads and defers to the underlying
pool implementation.  Downstream integrations can extend this module
with routing, slippage checks, or MEV-aware logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .pool_v2 import ConstantProductPool, SwapQuote

Side = Literal["token0", "token1"]


@dataclass(frozen=True)
class SwapIntent:
    amount_in: float
    side_in: Side
    min_amount_out: float = 0.0


def execute_swap(pool: ConstantProductPool, intent: SwapIntent) -> SwapQuote:
    """Route a swap intent to the provided pool."""
    quote = pool.execute_swap(intent.amount_in, intent.side_in)
    if quote.amount_out < intent.min_amount_out:
        raise ValueError(
            f"Swap output {quote.amount_out:.6f} below minimum {intent.min_amount_out:.6f}"
        )
    return quote
