"""Explicit quantification of tokenization benefits for Project Finance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class TokenizationBenefits:
    """Quantifies tokenization advantage mechanisms."""

    liquidity_premium_traditional_bps: float = 75.0
    liquidity_premium_tokenized_bps: float = 25.0
    admin_cost_traditional_pct: float = 0.50
    admin_cost_tokenized_pct: float = 0.15
    min_ticket_traditional: float = 1_000_000.0
    min_ticket_tokenized: float = 100.0
    investor_base_multiplier: float = 100.0
    info_asymmetry_traditional_bps: float = 25.0
    info_asymmetry_tokenized_bps: float = 5.0

    @property
    def liquidity_benefit_bps(self) -> float:
        return self.liquidity_premium_traditional_bps - self.liquidity_premium_tokenized_bps

    @property
    def operational_savings_bps(self) -> float:
        return (self.admin_cost_traditional_pct - self.admin_cost_tokenized_pct) * 100

    @property
    def transparency_benefit_bps(self) -> float:
        return self.info_asymmetry_traditional_bps - self.info_asymmetry_tokenized_bps

    @property
    def total_benefit_bps(self) -> float:
        return (
            self.liquidity_benefit_bps
            + self.transparency_benefit_bps
            + self.operational_savings_bps * 0.1  # assumed 10% pass-through to WACD
        )

    def to_dict(self) -> dict:
        return {
            "mechanisms": {
                "liquidity_premium": {
                    "traditional_bps": self.liquidity_premium_traditional_bps,
                    "tokenized_bps": self.liquidity_premium_tokenized_bps,
                    "reduction_bps": self.liquidity_benefit_bps,
                    "driver": "secondary_market_depth",
                },
                "operational_efficiency": {
                    "traditional_admin_cost_pct": self.admin_cost_traditional_pct,
                    "tokenized_admin_cost_pct": self.admin_cost_tokenized_pct,
                    "savings_pct": self.admin_cost_traditional_pct - self.admin_cost_tokenized_pct,
                    "driver": "smart_contract_automation",
                },
                "capital_efficiency": {
                    "traditional_min_ticket": self.min_ticket_traditional,
                    "tokenized_min_ticket": self.min_ticket_tokenized,
                    "investor_base_expansion": self.investor_base_multiplier,
                    "driver": "fractional_ownership",
                },
                "transparency_premium": {
                    "traditional_info_asymmetry_bps": self.info_asymmetry_traditional_bps,
                    "tokenized_info_asymmetry_bps": self.info_asymmetry_tokenized_bps,
                    "reduction_bps": self.transparency_benefit_bps,
                    "driver": "on_chain_reporting",
                },
            },
            "total_benefit_bps": self.total_benefit_bps,
            "breakdown": {
                "liquidity": self.liquidity_benefit_bps,
                "transparency": self.transparency_benefit_bps,
                "operational": self.operational_savings_bps * 0.1,
            },
        }


def compute_liquidity_premium(
    depth: float,
    base_illiquidity_premium_bps: float = 75.0,
    depth_sensitivity: float = 0.8,
) -> float:
    """Deeper secondary market → lower illiquidity premium."""

    depth = max(0.0, min(1.0, depth))
    return base_illiquidity_premium_bps * (1 - depth**depth_sensitivity)


def compute_tokenization_wacd_impact(
    traditional_wacd_bps: float,
    *,
    secondary_market_depth: float = 0.7,
    smart_contract_operational: bool = True,
    on_chain_reporting: bool = True,
    benefits: TokenizationBenefits | None = None,
) -> dict:
    """Compute WACD reduction from tokenization mechanisms."""

    benefits = benefits or TokenizationBenefits()
    liquidity_reduction = compute_liquidity_premium(
        0.0, benefits.liquidity_premium_traditional_bps
    ) - compute_liquidity_premium(secondary_market_depth, benefits.liquidity_premium_traditional_bps)
    operational_reduction = benefits.operational_savings_bps * 0.1 if smart_contract_operational else 0.0
    transparency_reduction = benefits.transparency_benefit_bps if on_chain_reporting else 0.0

    total_reduction = liquidity_reduction + operational_reduction + transparency_reduction
    tokenized_wacd = traditional_wacd_bps - total_reduction

    return {
        "traditional_wacd_bps": traditional_wacd_bps,
        "tokenized_wacd_bps": tokenized_wacd,
        "total_reduction_bps": total_reduction,
        "breakdown": {
            "liquidity_reduction_bps": liquidity_reduction,
            "operational_reduction_bps": operational_reduction,
            "transparency_reduction_bps": transparency_reduction,
        },
        "assumptions": {
            "secondary_market_depth": secondary_market_depth,
            "smart_contract_operational": smart_contract_operational,
            "on_chain_reporting": on_chain_reporting,
        },
    }


__all__ = [
    "TokenizationBenefits",
    "compute_liquidity_premium",
    "compute_tokenization_wacd_impact",
]
