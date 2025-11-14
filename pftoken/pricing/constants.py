"""Shared constants for the WP-04 pricing stack."""

from __future__ import annotations

from dataclasses import dataclass

from pftoken.pricing.spreads.base import TokenizedSpreadConfig

# Numerical tolerances --------------------------------------------------------
# Maximum relative error allowed when matching Excel/benchmark outputs.
PRICING_REL_TOLERANCE = 1e-4  # 0.01 %

# WACD / capital structure defaults -------------------------------------------
DEFAULT_CORPORATE_TAX_RATE = 0.25
DEFAULT_WITHHOLDING_TAX_RATE = 0.05
TOKENIZED_SPREAD_DELTA_BPS = -75  # tokenized implementation reduces spread
TOKENIZED_ORIGINATION_FEE_BPS = -25

# Collateral / recovery assumptions ------------------------------------------
DEFAULT_COLLATERAL_HAIRCUT = 0.25
DEFAULT_TIME_TO_LIQUIDATION_YEARS = 1.5

# FX and curve defaults -------------------------------------------------------
DEFAULT_BASE_CURRENCY = "USD"
DEFAULT_FX_FORWARD_BUFFER_BPS = 15


@dataclass(frozen=True)
class PricingContext:
    """Container for shared knobs exposed to the pricing modules."""

    corporate_tax_rate: float = DEFAULT_CORPORATE_TAX_RATE
    withholding_tax_rate: float = DEFAULT_WITHHOLDING_TAX_RATE
    tokenized_spread_delta_bps: float = TOKENIZED_SPREAD_DELTA_BPS
    tokenized_origination_fee_bps: float = TOKENIZED_ORIGINATION_FEE_BPS
    collateral_haircut: float = DEFAULT_COLLATERAL_HAIRCUT
    time_to_liquidation_years: float = DEFAULT_TIME_TO_LIQUIDATION_YEARS
    fx_forward_buffer_bps: float = DEFAULT_FX_FORWARD_BUFFER_BPS
    pricing_rel_tolerance: float = PRICING_REL_TOLERANCE
    use_computed_deltas: bool = True


DEFAULT_PRICING_CONTEXT = PricingContext()
DEFAULT_TOKENIZED_SPREAD_CONFIG = TokenizedSpreadConfig()


__all__ = [
    "DEFAULT_COLLATERAL_HAIRCUT",
    "DEFAULT_CORPORATE_TAX_RATE",
    "DEFAULT_PRICING_CONTEXT",
    "DEFAULT_TOKENIZED_SPREAD_CONFIG",
    "DEFAULT_TIME_TO_LIQUIDATION_YEARS",
    "DEFAULT_WITHHOLDING_TAX_RATE",
    "PricingContext",
    "PRICING_REL_TOLERANCE",
    "TOKENIZED_ORIGINATION_FEE_BPS",
    "TOKENIZED_SPREAD_DELTA_BPS",
]
