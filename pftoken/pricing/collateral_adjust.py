"""Collateral-driven recovery analysis supporting LGD adjustments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping

from pftoken.pricing.constants import DEFAULT_PRICING_CONTEXT, PricingContext
from pftoken.pricing.zero_curve import ZeroCurve
from pftoken.waterfall.debt_structure import DebtStructure, Tranche


@dataclass(frozen=True)
class CollateralResult:
    """Stores the recovery analytics for a single tranche."""

    tranche_name: str
    recovery_rate: float
    discounted_collateral: float
    lgd: float


class CollateralAnalyzer:
    """Allocates collateral value through the priority waterfall."""

    def __init__(
        self,
        debt_structure: DebtStructure,
        zero_curve: ZeroCurve,
        *,
        collateral_value: float | None = None,
        pricing_context: PricingContext = DEFAULT_PRICING_CONTEXT,
        custom_haircuts: Mapping[str, float] | None = None,
    ):
        self.debt_structure = debt_structure
        self.zero_curve = zero_curve
        self.pricing_context = pricing_context
        self.collateral_value = collateral_value
        self.custom_haircuts = {k.lower(): v for k, v in (custom_haircuts or {}).items()}
        self._cache: Dict[str, CollateralResult] | None = None

    def analyze(self) -> Dict[str, CollateralResult]:
        """Run the waterfall allocation if not already cached."""

        if self._cache is not None:
            return self._cache

        discounted_pool = self._discounted_collateral_pool()
        results: Dict[str, CollateralResult] = {}
        remaining = discounted_pool
        for tranche in self.debt_structure.tranches:
            applied = min(remaining, tranche.principal)
            recovery_rate = applied / tranche.principal if tranche.principal else 0.0
            results[tranche.name] = CollateralResult(
                tranche_name=tranche.name,
                recovery_rate=recovery_rate,
                discounted_collateral=applied,
                lgd=max(0.0, 1.0 - recovery_rate),
            )
            remaining -= applied
        self._cache = results
        return results

    def lgd(self, tranche_name: str) -> float:
        """Convenience getter returning the LGD for a tranche."""

        results = self.analyze()
        if tranche_name not in results:
            raise KeyError(f"Unknown tranche: {tranche_name}")
        return results[tranche_name].lgd

    # ----------------------------------------------------------------- helpers
    def _discounted_collateral_pool(self) -> float:
        discount_factor = self.zero_curve.discount_factor(
            self.pricing_context.time_to_liquidation_years
        )
        available = 0.0
        total_principal = self.debt_structure.total_principal
        if total_principal <= 0:
            raise ValueError("Debt structure must have positive principal.")
        pool_total = self.collateral_value if self.collateral_value is not None else total_principal
        for tranche in self.debt_structure.tranches:
            haircut = self.custom_haircuts.get(tranche.name.lower(), self.pricing_context.collateral_haircut)
            weight = tranche.principal / total_principal
            collateral_slice = pool_total * weight
            available += collateral_slice * (1.0 - haircut)
        return available * discount_factor


__all__ = ["CollateralAnalyzer", "CollateralResult"]
