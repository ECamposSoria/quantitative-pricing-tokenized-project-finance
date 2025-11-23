"""Project-wide constants for tokenized structures and benchmarks."""

TOKENIZED_OPTIMAL_STRUCTURE = {
    "senior": 0.55,
    "mezzanine": 0.34,
    "subordinated": 0.12,
}

# Benchmarked tokenized WACD (after-tax) in basis points.
TOKENIZED_OPTIMAL_WACD_BPS = 557

__all__ = ["TOKENIZED_OPTIMAL_STRUCTURE", "TOKENIZED_OPTIMAL_WACD_BPS"]
