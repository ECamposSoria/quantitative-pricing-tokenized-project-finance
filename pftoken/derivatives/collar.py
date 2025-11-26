"""Interest rate collar (long cap + short floor)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from scipy.optimize import brentq

from pftoken.derivatives.interest_rate_cap import CapletPeriod, InterestRateCap
from pftoken.derivatives.interest_rate_floor import InterestRateFloor
from pftoken.pricing.constants import PricingContext
from pftoken.pricing.zero_curve import ZeroCurve


@dataclass(frozen=True)
class CollarPricingResult:
    """Pricing breakdown for a cap-floor collar."""

    cap_premium: float
    floor_premium: float
    net_premium: float
    cap_strike: float
    floor_strike: float
    effective_rate_band: tuple[float, float]
    carry_cost_bps: float
    is_zero_cost: bool

    def to_dict(self) -> dict[str, float | tuple[float, float]]:
        return {
            "cap_premium": self.cap_premium,
            "floor_premium": self.floor_premium,
            "net_premium": self.net_premium,
            "cap_strike": self.cap_strike,
            "floor_strike": self.floor_strike,
            "effective_rate_band": self.effective_rate_band,
            "carry_cost_bps": self.carry_cost_bps,
            "is_zero_cost": self.is_zero_cost,
        }


class InterestRateCollar:
    """Combination of long cap + short floor (net premium = cap - floor)."""

    def __init__(
        self,
        *,
        notional: float,
        cap_strike: float,
        floor_strike: float,
        reset_schedule: Sequence[CapletPeriod],
        pricing_context: PricingContext | None = None,
    ):
        if notional <= 0:
            raise ValueError("Collar notional must be positive.")
        if cap_strike <= floor_strike:
            raise ValueError("Cap strike must exceed floor strike.")
        if not reset_schedule:
            raise ValueError("Collar requires at least one period.")
        self.notional = notional
        self.cap_strike = cap_strike
        self.floor_strike = floor_strike
        self.reset_schedule = list(reset_schedule)
        self.pricing_context = pricing_context or PricingContext()

    def price(
        self,
        zero_curve: ZeroCurve,
        *,
        volatility: float | None = None,
        zero_cost_tolerance: float = 1e-6,
    ) -> CollarPricingResult:
        """Price the collar (long cap, short floor)."""

        vol = float(volatility if volatility is not None else self.pricing_context.cap_flat_volatility)
        cap = InterestRateCap(
            notional=self.notional,
            strike=self.cap_strike,
            reset_schedule=self.reset_schedule,
            pricing_context=self.pricing_context,
        )
        floor = InterestRateFloor(
            notional=self.notional,
            strike=self.floor_strike,
            reset_schedule=self.reset_schedule,
            pricing_context=self.pricing_context,
        )

        cap_result = cap.price(zero_curve, volatility=vol)
        floor_result = floor.price(zero_curve, volatility=vol)
        net_premium = cap_result.total_value - floor_result.total_value
        carry_cost_bps = self._carry_cost_bps(net_premium)

        return CollarPricingResult(
            cap_premium=cap_result.total_value,
            floor_premium=floor_result.total_value,
            net_premium=net_premium,
            cap_strike=self.cap_strike,
            floor_strike=self.floor_strike,
            effective_rate_band=(self.floor_strike, self.cap_strike),
            carry_cost_bps=carry_cost_bps,
            is_zero_cost=abs(net_premium) <= zero_cost_tolerance,
        )

    def payoff_at_rate(self, rate: float) -> float:
        """Effective floating rate after applying the collar band."""

        if rate > self.cap_strike:
            return self.cap_strike
        if rate < self.floor_strike:
            return self.floor_strike
        return rate

    def _carry_cost_bps(self, net_premium: float) -> float:
        avg_tenor = sum(p.year_fraction() for p in self.reset_schedule) / len(self.reset_schedule)
        if avg_tenor <= 0 or self.notional <= 0:
            return 0.0
        return net_premium / self.notional / avg_tenor * 10_000.0


def find_zero_cost_floor_strike(
    notional: float,
    cap_strike: float,
    reset_schedule: Sequence[CapletPeriod],
    zero_curve: ZeroCurve,
    volatility: float = 0.20,
    tolerance: float = 1_000.0,
) -> float | None:
    """Solve for floor strike that makes net premium ~ 0 (long cap / short floor)."""

    cap = InterestRateCap(notional=notional, strike=cap_strike, reset_schedule=reset_schedule)
    cap_premium = cap.price(zero_curve, volatility=volatility).total_value

    def objective(strike: float) -> float:
        if strike >= cap_strike:
            return cap_premium  # invalid region
        floor = InterestRateFloor(notional=notional, strike=strike, reset_schedule=reset_schedule)
        floor_premium = floor.price(zero_curve, volatility=volatility).total_value
        return floor_premium - cap_premium

    low, high = 1e-4, cap_strike - 1e-4
    obj_low, obj_high = objective(low), objective(high)
    # If already close at the upper bound, treat as solution.
    if abs(obj_high) <= tolerance:
        return high
    try:
        if obj_low * obj_high > 0:
            return high  # best effort approximate strike
        return float(brentq(objective, low, high, xtol=tolerance / notional))
    except ValueError:
        return high


__all__ = ["CollarPricingResult", "InterestRateCollar", "find_zero_cost_floor_strike"]
