# Derivatives – Interest Rate Cap (WP-11, T-045)

This page documents the interest rate cap module delivered in WP-11. It covers the core pricing API, calibration, break-even analytics, and how to integrate hedging results into reports like `outputs/leo_iot_results.json`.

## Quickstart: Price a Cap

```python
from pftoken.derivatives import InterestRateCap, CapletPeriod
from pftoken.pricing.curve_loader import load_zero_curve_from_csv

curve = load_zero_curve_from_csv("data/derived/market_curves/usd_combined_curve_2025-11-20.csv")
schedule = [CapletPeriod(start=i-1 if i > 0 else 0.0, end=float(i)) for i in range(1, 6)]
cap = InterestRateCap(notional=72_000_000, strike=0.04, reset_schedule=schedule)

result = cap.price(curve)  # flat vol from PricingContext (default 20%)
print(result.total_value)              # premium in currency units
print(result.break_even_spread_bps)    # bps over floating leg
print(result.to_dict())                # JSON-friendly payload
```

## Implied Volatility

Recover a flat Black volatility that matches a target premium:

```python
target_premium = 900_000
implied_vol = cap.implied_volatility(target_price=target_premium, zero_curve=curve)
```

Internally this uses `scipy.optimize.brentq` for robustness.

## Break-even Analytics

- `break_even_spread_bps`: Premium-equivalent spread over the floating leg (PV01-based).
- `breakeven_floating_rate(curve)`: Uniform floating rate where PV(cap payoff) equals the premium.
- `carry_cost_pct(curve)`: Annualized premium as % of notional using average accrual tenor.
- `par_swap_rate(curve)`: Reference swap rate on the same schedule (helps show moneyness).

## Hedge Integration with Rate Scenarios

Use the WP-08 sensitivity engine to compare naked vs hedged exposure:

```python
from pftoken.pricing_mc.sensitivity import InterestRateSensitivity
from pftoken.pricing_mc.contracts import RateScenarioDefinition

# Assume `inputs` is a populated StochasticPricingInputs
sense = InterestRateSensitivity(inputs)
hedged = sense.analyze_with_hedge(
    hedge_instrument=cap,
    scenarios=[
        RateScenarioDefinition(name="Base", parallel_bps=0),
        RateScenarioDefinition(name="+50bps", parallel_bps=50),
        RateScenarioDefinition(name="-50bps", parallel_bps=-50),
    ],
)
print(hedged["hedge_results"])  # delta vs base per scenario
```

`HedgeComparisonResult` reports total price with the hedge applied and the incremental hedge value for each scenario.

## CLI: Regenerate Risk Metrics with Hedging

The demo runner now writes the hedging block automatically:

```bash
docker run --rm -v "$(pwd)":/app -w /app qptf-quant_token_app:latest \
  python3 scripts/demo_risk_metrics.py --sims 10000
```

Flags:
- `--hedge-curve-csv` (default: combined USD curve 2025-11-20)
- `--cap-strike` (default: 0.04)
- `--cap-years` (default: 5 annual caplets)

The output `outputs/leo_iot_results.json` will include `hedging.interest_rate_cap` with live premiums, break-even metrics, breakeven floating rate, carry cost, par swap rate, and Base/±50 bps scenarios.

## Testing

Cap-specific tests live in `tests/test_derivatives/test_interest_rate_cap.py` and cover:
- Black-76 pricing correctness
- Aggregation of caplet PVs
- Implied volatility roundtrip
- Break-even spread, breakeven floating rate, carry cost
- Hedge integration with sensitivity scenarios

## Interest Rate Floor (put on forward rates)

Price floorlets (Black-76 put):

```python
from pftoken.derivatives import InterestRateFloor, CapletPeriod

floor = InterestRateFloor(notional=50_000_000, strike=0.03, reset_schedule=schedule)
result = floor.price(curve, volatility=0.20)
print(result.total_value, result.break_even_spread_bps, result.breakeven_floating_rate)
```

Features:
- Same schedule validation as caps
- Implied vol via `brentq`
- Break-even spread, breakeven floating rate (strike − premium/annuity approx), carry cost %

## Interest Rate Collar (long cap, short floor)

Combine long cap + short floor to reduce net premium:

```python
from pftoken.derivatives import InterestRateCollar, find_zero_cost_floor_strike

collar = InterestRateCollar(notional=50_000_000, cap_strike=0.04, floor_strike=0.03, reset_schedule=schedule)
result = collar.price(curve, volatility=0.20)
print(result.net_premium, result.carry_cost_bps, result.effective_rate_band)

zero_cost_strike = find_zero_cost_floor_strike(50_000_000, 0.04, schedule, curve)
```

Integration: collars work with `InterestRateSensitivity.analyze_with_hedge` (net premium used as upfront cost).

## Limitations

- Flat volatility only (no term structure/smile).
- No counterparty adjustment (CVA/DVA).
- Pricing assumes deterministic forwards from the chosen `ZeroCurve`; market levels will shift results.

Run in the provided container:

```bash
docker run --rm -v "$(pwd)":/app -w /app qptf-quant_token_app:latest \
  python -m pytest tests/test_derivatives/test_interest_rate_cap.py -q
```

## WP-13: Hedging Comparison Analysis (Monte Carlo)

The hedging comparison module (`pftoken/hedging/hedge_simulator.py`) integrates cap and collar payouts into Monte Carlo simulation to compare breach probability across hedging strategies.

### Methodology

1. **Stochastic Rate Shocks**: Use existing MC rate_shock draws from N(0, 0.015) per simulation path
2. **Hedge Payouts**: Calculate cap/collar payouts based on effective rate = base_rate + rate_shock
3. **CFADS Adjustment**: Add hedge payouts to CFADS paths (positive payout = cash inflow)
4. **Breach Comparison**: Run DualStructureComparator on adjusted CFADS for each hedge scenario

### Analysis Results (2025-11-26, 10,000 simulations)

| Scenario | Breach Prob | Breaches | Δ vs Unhedged | Cost | Cost/Breach |
|----------|-------------|----------|---------------|------|-------------|
| **Unhedged** | 2.71% | 271 | — | $0 | — |
| **Cap** | 2.09% | 209 | −23% (62 fewer) | $595K | $9,604 |
| **Collar** | 2.38% | 238 | −12% (33 fewer) | $326K | $9,883 |

### Decision: CAP as Default Hedge

**Rationale:**
- Cap provides 23% breach reduction vs 12% for collar (nearly 2x effectiveness)
- Cost per breach avoided is similar (~$9,600 both)
- With tokenized structure (DSCR-contingent amortization), breach is already low (2.7%)
- Cap offers better tail protection for rate spikes

**Implementation:**
```python
from pftoken.hedging import HedgeConfig

config = HedgeConfig()
print(config.default_hedge)  # "cap"
```

### Output Location

Results are in `outputs/leo_iot_results.json` under `hedging_comparison`:

```json
{
  "hedging_comparison": {
    "scenarios": {
      "none": { "breach_probability": 0.0271, "cost": 0 },
      "cap": { "breach_probability": 0.0209, "cost": 595433 },
      "collar": { "breach_probability": 0.0238, "cost": 326139 }
    },
    "recommendation": "cap",
    "rationale": "Cap provides materially better breach probability reduction"
  }
}
```

## Notes & Future Extensions

- Current implementation uses a flat vol (no surface). Extendable to term structures if needed.
- Key-rate deltas and cap/floor parity checks are natural follow-ons.
- Keep using non-root, pinned images (`qptf-quant_token_app:latest` is pinned at build time).
