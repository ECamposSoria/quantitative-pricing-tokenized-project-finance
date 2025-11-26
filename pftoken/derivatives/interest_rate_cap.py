"""Interest rate cap pricer (Black-76) for WP-11 T-045."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from scipy.optimize import brentq
from scipy.stats import norm

from pftoken.pricing.constants import PricingContext
from pftoken.pricing.zero_curve import ZeroCurve


@dataclass(frozen=True)
class CapletPeriod:
    """Reset/payment window for a single caplet."""

    start: float
    end: float
    accrual: float | None = None

    def __post_init__(self) -> None:
        if self.start < 0 or self.end <= self.start:
            raise ValueError("CapletPeriod must satisfy 0 <= start < end.")
        if self.accrual is not None and self.accrual <= 0:
            raise ValueError("Accrual must be positive when provided.")

    def year_fraction(self) -> float:
        return self.accrual if self.accrual is not None else self.end - self.start


@dataclass(frozen=True)
class CapletResult:
    """Detailed pricing breakdown for a caplet."""

    period: CapletPeriod
    forward_rate: float
    discount_factor: float
    d1: float
    d2: float
    value: float

    def to_dict(self) -> dict[str, float]:
        return {
            "start": self.period.start,
            "end": self.period.end,
            "accrual": self.period.year_fraction(),
            "forward_rate": self.forward_rate,
            "discount_factor": self.discount_factor,
            "d1": self.d1,
            "d2": self.d2,
            "value": self.value,
        }


@dataclass(frozen=True)
class CapPricingResult:
    """Aggregated cap valuation output."""

    total_value: float
    caplet_values: Sequence[CapletResult]
    break_even_spread_bps: float

    def to_dict(self) -> dict[str, object]:
        return {
            "total_value": self.total_value,
            "break_even_spread_bps": self.break_even_spread_bps,
            "caplets": [c.to_dict() for c in self.caplet_values],
        }


class InterestRateCap:
    """Portfolio of caplets priced with Black-76."""

    def __init__(
        self,
        *,
        notional: float,
        strike: float,
        reset_schedule: Sequence[CapletPeriod],
        pricing_context: PricingContext | None = None,
    ):
        if notional <= 0:
            raise ValueError("Cap notional must be positive.")
        if strike <= 0:
            raise ValueError("Cap strike must be positive.")
        if not reset_schedule:
            raise ValueError("Cap requires at least one caplet period.")

        self.notional = notional
        self.strike = strike
        self.reset_schedule = list(reset_schedule)
        self.pricing_context = pricing_context or PricingContext()
        self._validate_schedule()

    # ------------------------------------------------------------------ Public
    def price(
        self,
        zero_curve: ZeroCurve,
        *,
        volatility: float | None = None,
    ) -> CapPricingResult:
        """Price the cap using a flat volatility surface."""

        sigma = float(volatility if volatility is not None else self.pricing_context.cap_flat_volatility)
        caplets: List[CapletResult] = []
        for period in self.reset_schedule:
            forward = zero_curve.forward_rate(period.start, period.end)
            df_pay = zero_curve.discount_factor(period.end)
            tau = period.year_fraction()
            value, d1, d2 = self._caplet_price_black(
                forward=forward,
                strike=self.strike,
                discount_factor=df_pay,
                volatility=sigma,
                time_to_reset=max(period.start, 1e-6),
                accrual=tau,
            )
            caplets.append(
                CapletResult(
                    period=period,
                    forward_rate=forward,
                    discount_factor=df_pay,
                    d1=d1,
                    d2=d2,
                    value=value * self.notional,
                )
            )
        total = sum(item.value for item in caplets)
        break_even = self._break_even_spread_bps(caplets)
        return CapPricingResult(total_value=total, caplet_values=caplets, break_even_spread_bps=break_even)

    def implied_volatility(
        self,
        *,
        target_price: float,
        zero_curve: ZeroCurve,
        bracket: tuple[float, float] = (1e-4, 3.0),
        tol: float = 1e-6,
        max_iter: int = 100,
    ) -> float:
        """Solve for flat volatility that matches a target cap price."""

        if target_price <= 0:
            raise ValueError("Target price must be positive.")

        lower, upper = bracket
        objective = lambda vol: self.price(zero_curve, volatility=vol).total_value - target_price
        try:
            return float(brentq(objective, lower, upper, xtol=tol, maxiter=max_iter))
        except ValueError as exc:  # pragma: no cover - defensive
            raise ValueError("Target price not bracketed by volatility bounds.") from exc

    def par_swap_rate(self, zero_curve: ZeroCurve) -> float:
        """Return the fixed rate of a par swap on the same schedule."""

        annuity = 0.0
        for period in self.reset_schedule:
            annuity += zero_curve.discount_factor(period.end) * period.year_fraction()
        # reset_schedule is validated non-empty in __init__
        last_df = zero_curve.discount_factor(self.reset_schedule[-1].end)
        if annuity == 0:
            raise ValueError("Annuity is zero; check schedule.")
        return (1.0 - last_df) / annuity

    def breakeven_floating_rate(
        self,
        zero_curve: ZeroCurve,
        *,
        volatility: float | None = None,
    ) -> float:
        """Uniform floating rate (per annum) where PV(cap payoff) equals premium."""

        premium = self.price(zero_curve, volatility=volatility).total_value
        annuity = sum(
            self.notional * period.year_fraction() * zero_curve.discount_factor(period.end)
            for period in self.reset_schedule
        )
        if annuity <= 0:
            raise ValueError("Annuity must be positive to compute breakeven rate.")
        return self.strike + premium / annuity

    def carry_cost_pct(
        self,
        zero_curve: ZeroCurve,
        *,
        volatility: float | None = None,
    ) -> float:
        """Annualized premium as % of notional using average accrual tenor."""

        premium = self.price(zero_curve, volatility=volatility).total_value
        avg_tenor = sum(p.year_fraction() for p in self.reset_schedule) / len(self.reset_schedule)
        if avg_tenor <= 0:
            raise ValueError("Average tenor must be positive.")
        return (premium / self.notional) / avg_tenor * 100.0

    def hedge_values(
        self,
        zero_curve: ZeroCurve,
        scenarios: Iterable[tuple[str, ZeroCurve]],
        *,
        upfront_premium: float | None = None,
        volatility: float | None = None,
    ) -> list[dict[str, float | str]]:
        """Compute hedge P&L for shocked curves vs upfront premium."""

        base_premium = (
            upfront_premium if upfront_premium is not None else self.price(zero_curve, volatility=volatility).total_value
        )
        results: list[dict[str, float | str]] = []
        for name, curve in scenarios:
            scenario_price = self.price(curve, volatility=volatility).total_value
            hedge_value = scenario_price - base_premium
            results.append(
                {
                    "scenario": name,
                    "cap_price": scenario_price,
                    "upfront_premium": base_premium,
                    "hedge_value": hedge_value,
                }
            )
        return results

    # --------------------------------------------------------------- Internals
    def _validate_schedule(self) -> None:
        previous_end = -math.inf
        for period in self.reset_schedule:
            if period.start < previous_end:
                raise ValueError("Caplet periods must be non-overlapping and ordered.")
            previous_end = period.end

    @staticmethod
    def _caplet_price_black(
        *,
        forward: float,
        strike: float,
        discount_factor: float,
        volatility: float,
        time_to_reset: float,
        accrual: float,
    ) -> tuple[float, float, float]:
        """Black-76 caplet pricer returning value per unit notional."""

        if volatility <= 0:
            return 0.0, 0.0, 0.0
        if forward <= 0 or strike <= 0:
            return 0.0, 0.0, 0.0
        sigma_sqrt = volatility * math.sqrt(time_to_reset)
        if sigma_sqrt <= 0:
            return 0.0, 0.0, 0.0
        ratio = max(forward, 1e-12) / max(strike, 1e-12)
        d1 = (math.log(ratio) + 0.5 * sigma_sqrt * sigma_sqrt) / sigma_sqrt
        d2 = d1 - sigma_sqrt
        option_value = discount_factor * accrual * (forward * norm.cdf(d1) - strike * norm.cdf(d2))
        return option_value, d1, d2

    def _break_even_spread_bps(self, caplets: Sequence[CapletResult]) -> float:
        """Premium-equivalent spread in basis points over the floating leg."""

        premium = sum(c.value for c in caplets)
        pv01 = sum(self.notional * c.period.year_fraction() * c.discount_factor for c in caplets)
        if pv01 <= 0:
            return 0.0
        return premium / pv01 * 10_000.0


__all__ = [
    "CapPricingResult",
    "CapletPeriod",
    "CapletResult",
    "InterestRateCap",
]
