"""Origination and servicing fee components."""

from __future__ import annotations

from dataclasses import dataclass

from .base import SpreadComponentResult, TokenizedSpreadConfig, TrancheSpreadInputs


def _clamp(value: float) -> float:
    return min(max(value, 0.0), 1.0)


@dataclass
class OriginationServicingComponent:
    """Benchmarks banking fees and applies beta/gamma reductions."""

    config: TokenizedSpreadConfig

    def compute_origination(self, inputs: TrancheSpreadInputs) -> SpreadComponentResult:
        beta = _clamp(self.config.origination_beta)
        amort_years = max(self.config.origination_fee_amortization_years, 1.0)
        base_bps = (self.config.placement_bps + self.config.syndication_bps) / amort_years
        tokenized_bps = base_bps * (1.0 - beta)
        metadata = {
            "placement_bps": self.config.placement_bps,
            "syndication_bps": self.config.syndication_bps,
            "beta": beta,
            "amortization_years": amort_years,
            "principal": inputs.principal,
        }
        return SpreadComponentResult("origination", base_bps, tokenized_bps, metadata)

    def compute_servicing(self, inputs: TrancheSpreadInputs) -> SpreadComponentResult:
        base_bps = self.config.paying_agent_bps + self.config.compliance_audit_bps
        gamma = _clamp(self.config.servicing_gamma)
        residual = max(self.config.servicing_residual_bps, 0.0)
        tokenized_bps = max(base_bps * (1.0 - gamma), 0.0) + residual
        tokenized_bps = min(tokenized_bps, base_bps)
        metadata = {
            "paying_agent_bps": self.config.paying_agent_bps,
            "compliance_audit_bps": self.config.compliance_audit_bps,
            "gamma": gamma,
            "residual_bps": residual,
            "principal": inputs.principal,
        }
        return SpreadComponentResult("servicing", base_bps, tokenized_bps, metadata)


__all__ = ["OriginationServicingComponent"]
