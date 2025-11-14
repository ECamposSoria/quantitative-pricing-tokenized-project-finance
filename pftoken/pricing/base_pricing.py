"""Tranche-level pricing engine built on top of the deterministic waterfall."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import matplotlib.pyplot as plt
from scipy import optimize

from pftoken.pricing.constants import DEFAULT_PRICING_CONTEXT, PricingContext
from pftoken.pricing.zero_curve import ZeroCurve
from pftoken.waterfall.debt_structure import DebtStructure, Tranche
from pftoken.waterfall.waterfall_engine import WaterfallResult

try:  # Optional to avoid import cycles during type checking
    from pftoken.pricing.collateral_adjust import CollateralAnalyzer
except Exception:  # pragma: no cover
    CollateralAnalyzer = None  # type: ignore


@dataclass(frozen=True)
class TrancheCashFlow:
    """Single-period debt service for a tranche."""

    year: int
    interest: float
    principal: float

    @property
    def total(self) -> float:
        return self.interest + self.principal

    def to_dict(self) -> Dict[str, float]:
        """Serialize the cash flow for JSON/CSV exports."""

        return {
            "year": self.year,
            "interest": self.interest,
            "principal": self.principal,
            "total": self.total,
        }


@dataclass(frozen=True)
class TranchePricingMetrics:
    """Summary analytics for a tranche."""

    present_value: float
    clean_price: float
    price_per_par: float
    ytm: float
    macaulay_duration: float
    modified_duration: float
    convexity: float
    cashflows: Sequence[TrancheCashFlow]
    lgd: float | None = None
    ytm_label: str = "risk-free YTM"
    risk_free_curve_rate: float = 0.0
    spread_over_curve: float = 0.0
    explanatory_note: str = (
        "YTM solved against the risk-free curve; credit/liquidity spreads "
        "live in the TokenizedSpreadModel."
    )

    def to_dict(self, *, include_cashflows: bool = True) -> Dict[str, Any]:
        """Return a JSON-friendly representation of these metrics."""

        payload: Dict[str, Any] = {
            "present_value": self.present_value,
            "clean_price": self.clean_price,
            "price_per_par": self.price_per_par,
            "ytm": self.ytm,
            "ytm_label": self.ytm_label,
            "risk_free_curve_rate": self.risk_free_curve_rate,
            "spread_over_curve": self.spread_over_curve,
            "macaulay_duration": self.macaulay_duration,
            "modified_duration": self.modified_duration,
            "convexity": self.convexity,
            "lgd": self.lgd,
            "explanatory_note": self.explanatory_note,
        }
        if include_cashflows:
            payload["cashflows"] = [cf.to_dict() for cf in self.cashflows]
        return payload


class PricingEngine:
    """Discounts tranche cash flows using a zero curve and reports analytics."""

    def __init__(
        self,
        zero_curve: ZeroCurve,
        *,
        pricing_context: PricingContext = DEFAULT_PRICING_CONTEXT,
        collateral_analyzer: "CollateralAnalyzer | None" = None,
    ):
        self.zero_curve = zero_curve
        self.pricing_context = pricing_context
        self.collateral_analyzer = collateral_analyzer

    # --------------------------------------------------------------- Public API
    def price_from_waterfall(
        self,
        waterfall_results: Mapping[int, WaterfallResult],
        debt_structure: DebtStructure,
        *,
        as_dict: bool = False,
    ) -> Dict[str, TranchePricingMetrics] | Dict[str, Dict[str, Any]]:
        """Run pricing for every tranche present in the debt structure.

        Args:
            waterfall_results: Mapping de año → `WaterfallResult`.
            debt_structure: Estructura con los tramos a valorar.
            as_dict: Si `True`, el resultado es JSON-friendly (`metrics.to_dict()`).
        """

        ordered = dict(sorted(waterfall_results.items()))
        output: Dict[str, TranchePricingMetrics | Dict[str, Any]] = {}
        for tranche in debt_structure.tranches:
            cashflows = self._extract_cashflows(tranche.name, ordered.values())
            metrics = self._price_tranche(tranche, cashflows)
            output[tranche.name] = metrics.to_dict() if as_dict else metrics
        return output  # type: ignore[return-value]

    def plot_tranche_cashflows(
        self,
        tranche_name: str,
        metrics: TranchePricingMetrics,
    ):
        """Return a stacked bar chart summarizing interest vs principal."""

        years = [cf.year for cf in metrics.cashflows]
        interest = [cf.interest for cf in metrics.cashflows]
        principal = [cf.principal for cf in metrics.cashflows]
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(years, interest, label="Interest", color="#508991")
        ax.bar(
            years,
            principal,
            bottom=interest,
            label="Principal",
            color="#c1666b",
        )
        ax.set_title(f"{tranche_name.title()} Cash Flows ({self.zero_curve.currency})")
        ax.set_xlabel("Year")
        ax.set_ylabel("Cash Flow")
        ax.legend()
        ax.grid(alpha=0.2)
        fig.tight_layout()
        return fig

    def plot_discount_curve(self):
        """Return a simple line plot of the underlying zero curve."""

        fig, ax = plt.subplots(figsize=(6, 4))
        points = self.zero_curve.points
        ax.plot(
            [p.maturity_years for p in points],
            [p.zero_rate * 100 for p in points],
            marker="o",
        )
        ax.set_title(f"{self.zero_curve.currency} Zero Curve")
        ax.set_xlabel("Maturity (years)")
        ax.set_ylabel("Zero Rate (%)")
        ax.grid(alpha=0.2)
        fig.tight_layout()
        return fig

    # -------------------------------------------------------------- Internals
    def _extract_cashflows(
        self,
        tranche_name: str,
        waterfall_results: Iterable[WaterfallResult],
    ) -> List[TrancheCashFlow]:
        cashflows: List[TrancheCashFlow] = []
        for period in waterfall_results:
            interest = float(period.interest_payments.get(tranche_name, 0.0))
            principal = float(period.principal_payments.get(tranche_name, 0.0))
            if interest == 0 and principal == 0:
                continue
            cashflows.append(TrancheCashFlow(year=period.year, interest=interest, principal=principal))
        if not cashflows:
            raise ValueError(f"No cash flows found for tranche {tranche_name}")
        return cashflows

    def _price_tranche(
        self,
        tranche: Tranche,
        cashflows: Sequence[TrancheCashFlow],
    ) -> TranchePricingMetrics:
        present_value = sum(
            cf.total * self.zero_curve.discount_factor(cf.year) for cf in cashflows
        )
        price_per_par = present_value / tranche.principal if tranche.principal else 0.0
        ytm = self._calculate_ytm(present_value, cashflows)
        duration, mod_duration, convexity = self._duration_convexity(cashflows, ytm)
        lgd = None
        if self.collateral_analyzer is not None:
            lgd = self.collateral_analyzer.lgd(tranche.name)
        curve_rate = self.zero_curve.spot_rate(tranche.tenor_years)
        spread_over_curve = curve_rate - ytm
        explanatory_note = (
            "YTM solved against the risk-free curve from the current snapshot. "
            "All credit/liquidity spreads are handled in the TokenizedSpreadModel."
        )
        return TranchePricingMetrics(
            present_value=present_value,
            clean_price=present_value,
            price_per_par=price_per_par,
            ytm=ytm,
            macaulay_duration=duration,
            modified_duration=mod_duration,
            convexity=convexity,
            cashflows=cashflows,
            lgd=lgd,
            ytm_label="risk-free YTM",
            risk_free_curve_rate=curve_rate,
            spread_over_curve=spread_over_curve,
            explanatory_note=explanatory_note,
        )

    @staticmethod
    def _calculate_ytm(price: float, cashflows: Sequence[TrancheCashFlow]) -> float:
        """
        Solve for Yield-to-Maturity using the tranche's clean price.

        IMPORTANT: YTM is solved against the risk-free discount curve implied
        by the zero rates passed to `PricingEngine`. Credit and liquidity spreads
        stay in TokenizedSpreadModel → WACDCalculator and are not part of this
        root-finding routine. Brent's method finds `r` such that the discounted
        cash flows match the observed clean price.
        """
        if price <= 0:
            return 0.0

        def npv(rate: float) -> float:
            return sum(cf.total / (1.0 + rate) ** cf.year for cf in cashflows) - price

        try:
            return float(optimize.brentq(npv, 1e-6, 1.0))
        except ValueError:
            try:
                return float(optimize.brentq(npv, -0.5, 2.0))
            except ValueError:
                return 0.0

    @staticmethod
    def _duration_convexity(
        cashflows: Sequence[TrancheCashFlow],
        ytm: float,
    ) -> tuple[float, float, float]:
        if not cashflows:
            return 0.0, 0.0, 0.0
        if ytm <= -0.99:
            return 0.0, 0.0, 0.0
        discounted = [
            (cf.year, cf.total / (1.0 + ytm) ** cf.year) for cf in cashflows
        ]
        pv_total = sum(value for _, value in discounted)
        if pv_total == 0:
            return 0.0, 0.0, 0.0
        duration = sum(year * value for year, value in discounted) / pv_total
        modified_duration = duration / (1.0 + ytm)
        convexity = sum(value * year * (year + 1) for year, value in discounted)
        convexity /= pv_total * (1.0 + ytm) ** 2
        return duration, modified_duration, convexity


__all__ = ["PricingEngine", "TrancheCashFlow", "TranchePricingMetrics"]
