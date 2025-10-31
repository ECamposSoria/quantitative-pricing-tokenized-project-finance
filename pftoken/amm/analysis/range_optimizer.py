"""
Range optimization scaffolding leveraging SciPy for quick experimentation.

The routine provides a deterministic, differentiable objective so that
future iterations can plug in richer payoff modeling without refactoring
the optimizer interface.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize


@dataclass(frozen=True)
class RangeOptimizationResult:
    lower_tick: int
    upper_tick: int
    success: bool
    message: str


def optimize_ticks(target_price: float, width_hint: int = 1_000) -> RangeOptimizationResult:
    """
    Compute a symmetric tick range around the target price.

    The objective encourages symmetry and proximity to the target while
    penalizing overly narrow ranges that could lead to rapid fee decay.
    """
    if target_price <= 0:
        raise ValueError("target_price must be positive.")
    if width_hint <= 0:
        raise ValueError("width_hint must be positive.")

    target_tick = math.log(target_price, 1.0001)

    def objective(x: np.ndarray) -> float:
        lower, upper = x
        if lower >= upper:
            return 1e9 + (lower - upper + 1) ** 2
        mid_tick = 0.5 * (lower + upper)
        mid_price = 1.0001 ** mid_tick
        width = upper - lower
        penalty_mid = (math.log(target_price) - math.log(mid_price)) ** 2
        penalty_width = (width - width_hint) ** 2 / max(width_hint, 1)
        return penalty_mid + 1e-6 * penalty_width

    bounds = [(-887_272, 887_272), (-887_272, 887_272)]  # Uniswap v3 bounds
    initial = np.array(
        [target_tick - width_hint / 2, target_tick + width_hint / 2],
        dtype=float,
    )

    result = minimize(
        objective,
        initial,
        method="L-BFGS-B",
        bounds=bounds,
        options={"maxiter": 100},
    )

    lower_tick, upper_tick = result.x
    return RangeOptimizationResult(
        lower_tick=int(math.floor(lower_tick)),
        upper_tick=int(math.ceil(upper_tick)),
        success=result.success,
        message=result.message,
    )
