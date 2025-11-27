"""Project-wide constants for tokenized structures and benchmarks."""

TOKENIZED_OPTIMAL_STRUCTURE = {
    "senior": 0.55,
    "mezzanine": 0.34,
    "subordinated": 0.11,  # Fixed: was 0.12 which summed to 101%
}

# Coupon-based WACD in basis points.
# Since all tranches have the same 4.5% coupon rate, structure rebalancing
# does NOT change the WACD. The 55/34/11 structure was chosen for RISK-RETURN
# optimization (Pareto frontier), not cost reduction. Tokenization benefits
# (liquidity, operational, transparency) reduce the all-in cost separately.
TOKENIZED_OPTIMAL_WACD_BPS = 450  # Fixed: was 557, now matches traditional (all coupons 4.5%)

# Regulatory risk premium for security-token ban tail risk (midpoint 5–10 bps).
REGULATORY_RISK_BPS = 7.5

__all__ = ["TOKENIZED_OPTIMAL_STRUCTURE", "TOKENIZED_OPTIMAL_WACD_BPS", "REGULATORY_RISK_BPS"]
