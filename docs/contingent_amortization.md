# DSCR-Contingent Amortization: A Tokenization-Native Structure (WP-12)

## Executive Summary

This document describes a novel debt structure enabled by tokenization:
**DSCR-contingent amortization**, where principal payments automatically
adjust based on realized cash flows to maintain a minimum DSCR floor.

## Problem Statement

Traditional project finance debt uses fixed amortization schedules.
When cash flows underperform, DSCR breaches trigger:
- Technical default
- Dividend lockup
- Potential acceleration

For the LEO IoT constellation, Monte Carlo analysis shows:
- **~40-50% probability** of DSCR breach under traditional structure
- Breach concentrated in Year 5 (transition from grace to amortization)
- Project may be **not bankable** under traditional terms

## Solution: Contingent Amortization

### Mechanism

```
Smart Contract Logic (each period):
1. Pay all interest first (mandatory)
2. Calculate: max_principal = (CFADS / DSCR_floor) - interest
3. Principal_paid = min(scheduled, max_principal, available_CFADS)
4. Deferred = scheduled - principal_paid
5. Deferred accrues at subordinated rate (12%)
6. Balloon at maturity includes all deferred + accrued interest
```

### Key Properties

| Property | Default | Rationale |
|----------|---------|-----------|
| DSCR Floor | 1.25x | Maintains covenant headroom |
| DSCR Target | 1.50x | Target for full principal payment |
| Max Deferral | 30% | Limits balloon risk |
| Deferral Rate | 12% | Subordinated tranche rate |
| Catch-up Threshold | 2.0x | Accelerate when DSCR high |

## Implementation

### Core Classes

```python
from pftoken.waterfall.contingent_amortization import (
    ContingentAmortizationConfig,
    ContingentAmortizationEngine,
    TraditionalAmortizationEngine,
    DualStructureComparator,
)
```

### Usage Example

```python
# Configure contingent amortization
config = ContingentAmortizationConfig(
    dscr_floor=1.25,
    dscr_target=1.50,
    dscr_accelerate=2.00,
    deferral_rate=0.12,
    max_deferral_pct=0.30,
)

# Create comparator
comparator = DualStructureComparator(
    principal=50_000_000,
    interest_rate=0.055,
    tenor=15,
    grace_years=4,
    contingent_config=config,
)

# Run Monte Carlo comparison
results = comparator.run_monte_carlo_comparison(
    cfads_scenarios,  # Shape: (n_sims, n_years) in USD
    covenant=1.20,
)

# Access results
print(f"Traditional breach probability: {results['traditional']['breach_probability']:.1%}")
print(f"Tokenized breach probability: {results['tokenized']['breach_probability']:.1%}")
print(f"Key finding: {results['thesis_summary']['key_finding']}")
```

## Expected Results

Monte Carlo comparison (10,000 simulations) typically shows:

| Metric | Traditional | Tokenized | Improvement |
|--------|-------------|-----------|-------------|
| Breach Probability | ~46% | ~5% | ~89% reduction |
| Min DSCR (P25) | ~0.96x | ~1.25x | +0.29x |
| Bankable | No | Yes | Enabled |
| Avg Additional Balloon | $0 | ~$8M | Trade-off |

## Why Tokenization Enables This

1. **Smart Contract Enforcement**: Deterministic waterfall logic
2. **Transparent State**: On-chain CFADS reporting
3. **Atomic Execution**: Interest -> Principal -> Deferral in one transaction
4. **Investor Alignment**: Token holders see real-time adjustments

## Trade-offs

| Benefit | Cost |
|---------|------|
| Eliminates soft breaches | Higher maturity balloon |
| Self-stabilizing structure | Refinancing risk at balloon |
| Bankability enabled | More complex investor communication |
| Transparent mechanism | Smart contract dependency |

## Demo Scripts

### Standalone Demo

```bash
python scripts/demo_dual_structure.py --sims 10000
```

Options:
- `--sims`: Number of Monte Carlo simulations (default: 10000)
- `--stress`: Stress factor for CFADS (1.0 = base, <1.0 = stressed)
- `--dscr-floor`: DSCR floor for contingent amortization (default: 1.25)
- `--output`: Output JSON path

### Integration with Risk Metrics

The dual structure analysis is automatically included in `demo_risk_metrics.py`:

```bash
python scripts/demo_risk_metrics.py --sims 5000
```

Results appear in `outputs/leo_iot_results.json` under the `dual_structure_comparison` key.

## Academic Contribution

This is the first application of DSCR-contingent amortization to:
1. Tokenized project finance
2. Satellite constellation financing
3. Smart contract-enforced debt service

## References

- Gatti (2018), *Project Finance in Theory and Practice*
- Yescombe (2013), *Principles of Project Finance*
- Basel Committee (2009), *Enhancements to the Basel II Framework*

## Files

| File | Description |
|------|-------------|
| `pftoken/waterfall/contingent_amortization.py` | Core engine implementation |
| `tests/test_waterfall/test_contingent_amortization.py` | Unit tests |
| `scripts/demo_dual_structure.py` | Standalone demo script |
| `docs/contingent_amortization.md` | This documentation |
