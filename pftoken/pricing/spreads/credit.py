"""Credit spread component derived from Merton-model PD/LGD outputs."""

from __future__ import annotations

from dataclasses import dataclass

from .base import SpreadComponentResult, TokenizedSpreadConfig, TrancheSpreadInputs

BPS_PER_UNIT = 10_000.0


@dataclass
class CreditSpreadComponent:
    """Maps PD/LGD/duration inputs to a credit spread in basis points."""

    config: TokenizedSpreadConfig

    def compute(self, inputs: TrancheSpreadInputs) -> SpreadComponentResult:
        duration_years = self._resolve_duration(inputs)
        pd = min(max(inputs.pd, 1e-6), 0.999)
        lgd = min(max(inputs.lgd, 0.0), 1.0)

        base_spread = (pd * lgd / duration_years) / max(1.0 - pd, 1e-6)
        adjusted_spread = base_spread * self.config.market_price_of_risk
        bps = max(adjusted_spread * BPS_PER_UNIT, self.config.credit_spread_floor_bps)
        tokenized_bps = max(bps + self.config.credit_transparency_delta_bps, 0.0)
        metadata = {
            "pd": pd,
            "lgd": lgd,
            "duration_years": duration_years,
            "lambda_market_price_of_risk": self.config.market_price_of_risk,
            "credit_transparency_delta_bps": self.config.credit_transparency_delta_bps,
            "credit_spread_floor_bps": self.config.credit_spread_floor_bps,
        }
        return SpreadComponentResult("credit", bps, tokenized_bps, metadata)

    def _resolve_duration(self, inputs: TrancheSpreadInputs) -> float:
        if inputs.duration_years and inputs.duration_years > 0:
            return inputs.duration_years
        if not self.config.duration_fallback_use_tenor:
            raise ValueError(f"Missing duration for tranche {inputs.name}")
        if inputs.tenor_years <= 0:
            raise ValueError(f"Invalid tenor for tranche {inputs.name}")
        return inputs.tenor_years


__all__ = ["CreditSpreadComponent"]
