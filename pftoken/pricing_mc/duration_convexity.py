"""Duration and convexity analytics (WP-08 T-027)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Mapping, Sequence, Tuple

import numpy as np

from pftoken.pricing.base_pricing import PricingEngine, TrancheCashFlow
from pftoken.pricing.zero_curve import ZeroCurve
from pftoken.waterfall.debt_structure import Tranche


@dataclass(frozen=True)
class DurationConvexityResult:
    """Aggregated duration/convexity metrics for a tranche."""

    price: float
    macaulay_duration: float
    modified_duration: float
    convexity: float
    effective_duration: float
    effective_convexity: float
    key_rate_durations: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, float]:
        payload = {
            "price": self.price,
            "macaulay_duration": self.macaulay_duration,
            "modified_duration": self.modified_duration,
            "convexity": self.convexity,
            "effective_duration": self.effective_duration,
            "effective_convexity": self.effective_convexity,
        }
        payload.update({f"krd_{k}": v for k, v in self.key_rate_durations.items()})
        return payload


class DurationConvexityAnalyzer:
    """Extends deterministic duration/convexity with effective and key-rate metrics."""

    def __init__(self, zero_curve: ZeroCurve, *, epsilon_bps: float = 1.0):
        self.zero_curve = zero_curve
        self.epsilon_bps = float(epsilon_bps)

    def analyze(
        self,
        tranche: Tranche,
        cashflows: Sequence[TrancheCashFlow],
        *,
        spread_bps: float = 0.0,
        bucket_definitions: Sequence[Tuple[float, float]] | None = None,
    ) -> DurationConvexityResult:
        """Compute deterministic + effective + key-rate metrics."""

        price = self._price_cashflows(cashflows, self.zero_curve, spread_bps=spread_bps)
        ytm = PricingEngine._calculate_ytm(price, cashflows)
        macaulay, modified, convexity = PricingEngine._duration_convexity(cashflows, ytm)

        eff_duration, eff_convexity = self._effective_measures(
            cashflows=cashflows,
            spread_bps=spread_bps,
            price=price,
        )
        key_rates = self._key_rate_durations(
            cashflows=cashflows,
            spread_bps=spread_bps,
            price=price,
            bucket_definitions=bucket_definitions,
        )

        return DurationConvexityResult(
            price=price,
            macaulay_duration=macaulay,
            modified_duration=modified,
            convexity=convexity,
            effective_duration=eff_duration,
            effective_convexity=eff_convexity,
            key_rate_durations=key_rates,
        )

    # --------------------------------------------------------------- Internals
    def _price_cashflows(
        self,
        cashflows: Sequence[TrancheCashFlow],
        curve: ZeroCurve,
        *,
        spread_bps: float,
    ) -> float:
        rates = np.array([curve.spot_rate(float(cf.year)) for cf in cashflows], dtype=float)
        eff_rate = rates + spread_bps / 10_000.0
        discounts = np.power(1.0 + eff_rate, -np.array([cf.year for cf in cashflows], dtype=float))
        totals = np.array([cf.total for cf in cashflows], dtype=float)
        return float(np.sum(totals * discounts))

    def _effective_measures(
        self,
        *,
        cashflows: Sequence[TrancheCashFlow],
        spread_bps: float,
        price: float,
    ) -> tuple[float, float]:
        if price <= 0:
            return 0.0, 0.0
        eps = self.epsilon_bps
        curve_up = self.zero_curve.apply_shock(parallel_bps=eps)
        curve_down = self.zero_curve.apply_shock(parallel_bps=-eps)

        p_up = self._price_cashflows(cashflows, curve_up, spread_bps=spread_bps)
        p_down = self._price_cashflows(cashflows, curve_down, spread_bps=spread_bps)

        dv = eps / 10_000.0
        eff_duration = (p_down - p_up) / (2 * price * dv) if dv != 0 else 0.0
        eff_convexity = (p_down + p_up - 2 * price) / (price * dv**2) if dv != 0 else 0.0
        return float(eff_duration), float(eff_convexity)

    def _key_rate_durations(
        self,
        *,
        cashflows: Sequence[TrancheCashFlow],
        spread_bps: float,
        price: float,
        bucket_definitions: Sequence[Tuple[float, float]] | None,
    ) -> Dict[str, float]:
        if not bucket_definitions:
            return {}
        eps = self.epsilon_bps
        key_rates: Dict[str, float] = {}
        for start, end in bucket_definitions:
            bucket = {(start, end): eps}
            curve_up = self.zero_curve.apply_shock(bucket_shocks=bucket)
            curve_down = self.zero_curve.apply_shock(bucket_shocks={(start, end): -eps})
            p_up = self._price_cashflows(cashflows, curve_up, spread_bps=spread_bps)
            p_down = self._price_cashflows(cashflows, curve_down, spread_bps=spread_bps)
            dv = eps / 10_000.0
            krd = (p_down - p_up) / (2 * price * dv) if dv != 0 else 0.0
            key_rates[f"{start}-{end}y"] = float(krd)
        return key_rates


__all__ = ["DurationConvexityAnalyzer", "DurationConvexityResult"]
