"""Project-wide constants for tokenized structures and benchmarks."""

TOKENIZED_OPTIMAL_STRUCTURE = {
    "senior": 0.55,
    "mezzanine": 0.34,
    "subordinated": 0.11,
}

# Coupon-based WACD in basis points.
# Tranches have differentiated coupons based on risk:
#   Senior: SOFR (4.5%) + 150 bps = 6.0%
#   Mezzanine: SOFR (4.5%) + 400 bps = 8.5%
#   Subordinated: SOFR (4.5%) + 650 bps = 11.0%
#
# Traditional WACD (60/25/15): 0.60×6% + 0.25×8.5% + 0.15×11% = 7.375% = 737.5 bps
# Optimal WACD (55/34/11): 0.55×6% + 0.34×8.5% + 0.11×11% = 7.40% = 740 bps
#
# The 55/34/11 structure was chosen for RISK-RETURN optimization (Pareto frontier),
# not cost reduction. It has slightly higher WACD (+2.5 bps) but lower tail risk.
# Tokenization benefits (liquidity, operational, transparency) reduce all-in cost separately.
TRADITIONAL_WACD_BPS = 737.5
TOKENIZED_OPTIMAL_WACD_BPS = 740

# Regulatory risk premium for security-token ban tail risk (midpoint 5–10 bps).
REGULATORY_RISK_BPS = 7.5

__all__ = ["TOKENIZED_OPTIMAL_STRUCTURE", "TOKENIZED_OPTIMAL_WACD_BPS", "REGULATORY_RISK_BPS"]
