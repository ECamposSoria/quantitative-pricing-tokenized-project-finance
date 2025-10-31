"""Mathematical helpers specific to AMM tick math."""

from __future__ import annotations

import math


def decimal_sqrt(value: float) -> float:
    if value < 0:
        raise ValueError("value must be non-negative.")
    return math.sqrt(value)


def tick_to_price(tick: int) -> float:
    return 1.0001 ** tick


def price_to_tick(price: float) -> int:
    if price <= 0:
        raise ValueError("price must be positive.")
    return int(math.log(price, 1.0001))


def basis_points(value: float) -> float:
    return value / 10_000
