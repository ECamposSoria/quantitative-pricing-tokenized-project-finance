"""Interest rate floor pricer (Black-76 put) for WP-11 follow-up (collars)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from scipy.optimize import brentq
from scipy.stats import norm

from pftoken.derivatives.interest_rate_cap import CapletPeriod, CapletResult
from pftoken.pricing.constants import PricingContext
from pftoken.pricing.zero_curve import ZeroCurve


@dataclass(frozen=True)
class FloorPricingResult:
    """Aggregated floor valuation output."""

    total_value: float
    floorlet_values: Sequence[CapletResult]
    break_even_spread_bps: float
    breakeven_floating_rate: float
    carry_cost_pct: float

    def to_dict(self) -> dict[str, float | Sequence[dict[str, float]]]:
        return {
            "total_value": self.total_value,
            "break_even_spread_bps": self.break_even_spread_bps,
            "breakeven_floating_rate": self.breakeven_floating_rate,
            "carry_cost_pct": self.carry_cost_pct,
            "floorlets": [f.to_dict() for f in self.floorlet_values],
        }


class InterestRateFloor:
    """Portfolio of floorlets priced with Black-76 (put on forward rates)."""

    def __init__(
        self,
        *,
        notional: float,
        strike: float,
        reset_schedule: Sequence[CapletPeriod],
        pricing_context: PricingContext | None = None,
    ):
        if notional <= 0:
            raise ValueError("Floor notional must be positive.")
        if strike <= 0:
            raise ValueError("Floor strike must be positive.")
        if not reset_schedule:
            raise ValueError("Floor requires at least one floorlet period.")
        self.notional = notional
        self.strike = strike
        self.reset_schedule = list(reset_schedule)
        self.pricing_context = pricing_context or PricingContext()
        self._validate_schedule()

    def price(
        self,
        zero_curve: ZeroCurve,
        *,
        volatility: float | None = None,
    ) -> FloorPricingResult:
        """Price the floor using a flat volatility surface."""

        sigma = float(volatility if volatility is not None else self.pricing_context.cap_flat_volatility)
        floorlets: list[CapletResult] = []
        for period in self.reset_schedule:
            forward = zero_curve.forward_rate(period.start, period.end)
            df_pay = zero_curve.discount_factor(period.end)
            tau = period.year_fraction()
            value, d1, d2 = self._floorlet_price_black(
                forward=forward,
                strike=self.strike,
                discount_factor=df_pay,
                volatility=sigma,
                time_to_reset=max(period.start, 1e-6),
                accrual=tau,
            )
            floorlets.append(
                CapletResult(
                    period=period,
                    forward_rate=forward,
                    discount_factor=df_pay,
                    d1=d1,
                    d2=d2,
                    value=value * self.notional,
                )
            )

        total = sum(item.value for item in floorlets)
        breakeven_spread = self._break_even_spread_bps(floorlets)
        breakeven_rate = self._breakeven_floating_rate(total)
        carry_pct = self._carry_cost_pct(total)
        return FloorPricingResult(
            total_value=total,
            floorlet_values=floorlets,
            break_even_spread_bps=breakeven_spread,
            breakeven_floating_rate=breakeven_rate,
            carry_cost_pct=carry_pct,
        )

    def implied_volatility(
        self,
        *,
        target_price: float,
        zero_curve: ZeroCurve,
        bracket: tuple[float, float] = (1e-4, 3.0),
        tol: float = 1e-6,
        max_iter: int = 100,
    ) -> float:
        """Solve for flat volatility that matches a target floor price."""

        if target_price <= 0:
            raise ValueError("Target price must be positive.")

        lower, upper = bracket
        objective = lambda vol: self.price(zero_curve, volatility=vol).total_value - target_price
        try:
            return float(brentq(objective, lower, upper, xtol=tol, maxiter=max_iter))
        except ValueError as exc:  # pragma: no cover - defensive
            raise ValueError("Target price not bracketed by volatility bounds.") from exc

    def _breakeven_floating_rate(self, premium: float) -> float:
        annuity = sum(
            self.notional * period.year_fraction() * 1.0 for period in self.reset_schedule
        )  # discounting handled in price; here use average tenor approximation
        if annuity <= 0:
            return self.strike
        return self.strike - premium / annuity

    def _carry_cost_pct(self, premium: float) -> float:
        avg_tenor = sum(p.year_fraction() for p in self.reset_schedule) / len(self.reset_schedule)
        if avg_tenor <= 0:
            return 0.0
        return (premium / self.notional) / avg_tenor * 100.0

    # --------------------------------------------------------------- Internals
    def _validate_schedule(self) -> None:
        previous_end = -math.inf
        for period in self.reset_schedule:
            if period.start < previous_end:
                raise ValueError("Floorlet periods must be non-overlapping and ordered.")
            previous_end = period.end

    @staticmethod
    def _floorlet_price_black(
        *,
        forward: float,
        strike: float,
        discount_factor: float,
        volatility: float,
        time_to_reset: float,
        accrual: float,
    ) -> tuple[float, float, float]:
        """Black-76 floorlet pricer returning value per unit notional."""

        if volatility <= 0 or forward <= 0 or strike <= 0 or time_to_reset <= 0:
            return 0.0, 0.0, 0.0
        sigma_sqrt = volatility * math.sqrt(time_to_reset)
        ratio = max(forward, 1e-12) / max(strike, 1e-12)
        d1 = (math.log(ratio) + 0.5 * sigma_sqrt * sigma_sqrt) / sigma_sqrt
        d2 = d1 - sigma_sqrt
        option_value = discount_factor * accrual * (strike * norm.cdf(-d2) - forward * norm.cdf(-d1))
        return option_value, d1, d2

    def _break_even_spread_bps(self, floorlets: Sequence[CapletResult]) -> float:
        premium = sum(c.value for c in floorlets)
        pv01 = sum(self.notional * c.period.year_fraction() * c.discount_factor for c in floorlets)
        if pv01 <= 0:
            return 0.0
        return premium / pv01 * 10_000.0


__all__ = ["FloorPricingResult", "InterestRateFloor"]
