# Implementation Plan: Monte Carlo Hedging Comparison (Cap vs Collar)

## OBJECTIVE

Integrate interest rate hedges (Cap vs Collar) into Monte Carlo simulation to:
1. Run 3 hedging scenarios: **Unhedged**, **Cap**, **Collar**
2. Compare breach probabilities and DSCR distributions across scenarios
3. Document results to help decide which hedge to use
4. Add results to output JSON (with potential file rename)

---

## ARCHITECTURE

### Current Flow
```
CFADS paths (stochastic) → Dual Structure Comparator → Breach probabilities
                                    ↓
                      (Hedges priced separately, not applied)
```

### New Flow
```
                        ┌─────────────────────────────────────┐
CFADS paths + Rate paths │  Hedging Scenario Engine           │
          ↓              │                                     │
    ┌─────────────────┐  │  1. Unhedged: CFADS unchanged       │
    │ For each path:  │→ │  2. Cap: CFADS += max(0, r-K)×N     │
    │   - CFADS[t]    │  │  3. Collar: CFADS += cap - floor    │
    │   - rate[t]     │  │                                     │
    └─────────────────┘  └─────────────────────────────────────┘
                                    ↓
                         Dual Structure Comparator
                                    ↓
                         Breach probabilities (per scenario)
```

### Key Insight
Hedge payouts **increase CFADS** when rates spike, improving DSCR:
- **Cap payout** = max(0, floating_rate - strike) × notional × accrual
- **Floor payout** = max(0, strike - floating_rate) × notional × accrual
- **Collar net** = cap_payout - floor_payout (we sell floor, so subtract)

---

## PRIVILEGE REQUIREMENTS

None - all Python code changes, no sudo required.

---

## FILES TO CREATE / MODIFY

### New Files
1. `pftoken/hedging/hedge_simulator.py` - Hedge payout calculation engine
2. `scripts/demo_hedging_comparison.py` - New script for hedged MC comparison

### Modified Files
1. `scripts/demo_risk_metrics.py` - Add hedging comparison to existing flow
2. `pftoken/simulation/path_callbacks.py` - Add rate path generation (if needed)
3. Output JSON renamed: `wp05_risk_metrics.json` → `leo_iot_results.json` ✓

---

## TECHNICAL DECISIONS

### 1. Rate Simulation Approach
**Decision**: Use shocked rate scenarios, not full stochastic rate paths

**Rationale**:
- Current MC already generates CFADS volatility (revenue/cost shocks)
- Interest rate volatility is secondary for project finance
- Use parallel rate shocks (+50bps, +100bps) applied uniformly
- Simpler, faster, matches current stress scenario approach

**Alternative Considered**: Full Hull-White rate simulation
- More complex, overkill for thesis scope
- Would require correlation calibration with revenue factors

### 2. Hedge Payout Integration Point
**Decision**: Adjust CFADS before passing to Dual Structure Comparator

**Rationale**:
- Clean separation of concerns
- Hedge payouts are cash inflows, directly add to CFADS
- Reuses existing breach probability machinery

### 3. Output Structure
**Decision**: Add `hedging_comparison` section to output JSON

```json
{
  "hedging_comparison": {
    "scenarios": {
      "unhedged": { ... breach stats ... },
      "cap_hedged": { ... breach stats ... },
      "collar_hedged": { ... breach stats ... }
    },
    "rate_assumption": {
      "base_rate": 0.0379,
      "shocked_rate": 0.0479,
      "shock_bps": 100
    },
    "recommendation": "cap" | "collar" | "none",
    "thesis_finding": "..."
  }
}
```

### 4. File Naming
**Decision**: Rename output to `leo_iot_results.json`

**Rationale**:
- Current name "wp05_risk_metrics.json" refers to single work package
- File now contains results from WP-05 through WP-13
- Project-specific naming (LEO IoT satellite constellation)

---

## IMPLEMENTATION STEPS

### Phase 1: Core Hedge Simulator (New Module)
- [ ] Create `pftoken/hedging/hedge_simulator.py`
  - `HedgeScenario` enum: UNHEDGED, CAP, COLLAR
  - `calculate_cap_payout(rate, strike, notional)`
  - `calculate_collar_payout(rate, cap_strike, floor_strike, notional)`
  - `apply_hedge_to_cfads(cfads_path, rate_path, hedge_type, config)`

### Phase 2: Integration with MC Pipeline
- [ ] Modify `path_callbacks.py` or add rate generation
  - Generate rate paths (simple: base_rate + shock_factor × volatility)
  - Or: deterministic rate shock scenarios
- [ ] Create wrapper function for hedged dual structure comparison

### Phase 3: New Comparison Script
- [ ] Create `scripts/demo_hedging_comparison.py`
  - Load existing CFADS paths from MC
  - Run 3 scenarios (unhedged, cap, collar)
  - Generate comparison statistics
  - Output to JSON

### Phase 4: Integration into Main Script
- [ ] Modify `scripts/demo_risk_metrics.py`
  - Add `--compare-hedges` flag
  - Run hedge comparison if flag enabled
  - Add `hedging_comparison` section to payload

### Phase 5: Output & Documentation
- [ ] Rename output file to `thesis_results.json`
- [ ] Update any scripts that read the output
- [ ] Document results interpretation
- [ ] Add to WP-11 comprehensive analysis

---

## HEDGE PAYOUT FORMULAS

### Cap Payout (Per Period)
```python
def cap_payout(rate: float, strike: float, notional: float, accrual: float = 1.0) -> float:
    """Cash inflow when rate exceeds strike."""
    return max(0, rate - strike) * notional * accrual
```

**Example**: Rate = 5%, Strike = 4%, Notional = $50M, Accrual = 1 year
- Payout = max(0, 0.05 - 0.04) × 50,000,000 × 1 = **$500,000**
- This $500K offsets the extra $500K interest expense

### Collar Net Payout (Per Period)
```python
def collar_payout(rate: float, cap_strike: float, floor_strike: float, notional: float) -> float:
    """Net payout: receive cap, pay floor."""
    cap = max(0, rate - cap_strike) * notional
    floor = max(0, floor_strike - rate) * notional  # We pay this
    return cap - floor  # Can be negative!
```

**Example 1**: Rate = 5%, Cap = 4%, Floor = 3%, Notional = $50M
- Cap payout = (0.05 - 0.04) × $50M = +$500K
- Floor payout = 0 (rate > floor)
- Net = **+$500K**

**Example 2**: Rate = 2.5%, Cap = 4%, Floor = 3%, Notional = $50M
- Cap payout = 0 (rate < cap)
- Floor payout = (0.03 - 0.025) × $50M = -$250K (we pay)
- Net = **-$250K** (reduces CFADS)

---

## COMPARISON METRICS

For each scenario (Unhedged, Cap, Collar), calculate:

| Metric | Description |
|--------|-------------|
| `breach_probability` | P(DSCR < covenant) |
| `breach_count` | Number of breaching paths |
| `min_dscr_p25` | 25th percentile of minimum DSCR |
| `min_dscr_p50` | Median minimum DSCR |
| `avg_balloon` | Average final balloon (tokenized) |
| `net_cost` | Upfront premium (cap: $595K, collar: $326K) |
| `effective_protection` | Breach reduction vs unhedged |

### Decision Framework

```
IF breach_reduction(cap) - breach_reduction(collar) > cost_difference / value_at_risk:
    RECOMMEND cap  # More protection worth the cost
ELSE:
    RECOMMEND collar  # Cheaper, sufficient protection
```

---

## RATE SHOCK SCENARIOS

Since we're not doing full rate simulation, use deterministic scenarios:

| Scenario | Rate Shock | Interpretation |
|----------|------------|----------------|
| Base | 0 bps | Current forward curve |
| Mild stress | +50 bps | Moderate rate increase |
| Severe stress | +100 bps | Significant rate increase |
| Extreme | +150 bps | Tail scenario |

For Monte Carlo, apply each shock to a subset of paths to create a blended distribution.

---

## EXPECTED RESULTS (Hypothesis)

Based on current analysis:

| Scenario | Expected Breach Prob | Rationale |
|----------|---------------------|-----------|
| Unhedged | ~25% (current) | Baseline |
| Cap Hedged | ~20-22% | Reduces rate exposure |
| Collar Hedged | ~21-23% | Similar protection, lower cost |

**Thesis Finding (Expected)**:
- Hedging provides modest additional protection (~10-15% breach reduction)
- Main benefit is from contingent amortization (~89% reduction)
- Collar recommended for cost efficiency if marginal protection is acceptable

---

## POTENTIAL CHALLENGES & MITIGATIONS

### 1. Rate Path Correlation
**Challenge**: Interest rates may correlate with revenue (satellite demand)
**Mitigation**: Document assumption of independence; sensitivity analysis

### 2. Computational Cost
**Challenge**: 3× more simulations (one per hedge scenario)
**Mitigation**: Reuse CFADS paths, only hedge adjustment differs

### 3. Collar Negative Payouts
**Challenge**: Floor can reduce CFADS when rates drop
**Mitigation**: Document in results; show distribution of collar payouts

### 4. Output File Rename
**Challenge**: Other scripts may reference old filename
**Mitigation**: Search codebase for references; update imports

---

## OUTPUT JSON STRUCTURE (New Section)

```json
{
  "hedging_comparison": {
    "rate_scenario": {
      "base_rate_pct": 3.79,
      "shocked_rate_pct": 4.79,
      "shock_bps": 100,
      "description": "100bps parallel shock to forward curve"
    },
    "scenarios": {
      "unhedged": {
        "traditional": {
          "breach_probability": 0.246,
          "min_dscr_p25": 1.21
        },
        "tokenized": {
          "breach_probability": 0.027,
          "min_dscr_p25": 1.25
        }
      },
      "cap_hedged": {
        "upfront_cost": 595433,
        "traditional": {
          "breach_probability": 0.22,
          "min_dscr_p25": 1.24
        },
        "tokenized": {
          "breach_probability": 0.023,
          "min_dscr_p25": 1.26
        }
      },
      "collar_hedged": {
        "upfront_cost": 326139,
        "floor_strike": 0.03462,
        "traditional": {
          "breach_probability": 0.23,
          "min_dscr_p25": 1.23
        },
        "tokenized": {
          "breach_probability": 0.024,
          "min_dscr_p25": 1.255
        }
      }
    },
    "comparison_summary": {
      "cap_vs_unhedged_reduction_pct": 14.8,
      "collar_vs_unhedged_reduction_pct": 11.1,
      "cap_additional_cost": 269294,
      "cap_additional_protection_pct": 3.7
    },
    "recommendation": {
      "choice": "collar",
      "rationale": "Collar provides 11% breach reduction at $269K lower cost than cap. Additional 3.7% protection from cap not justified by 45% higher premium.",
      "thesis_implication": "Interest rate hedging provides incremental protection; primary risk mitigation comes from DSCR-contingent amortization (89% breach reduction)."
    }
  }
}
```

---

## TESTING STRATEGY

1. **Unit tests**: `test_hedge_simulator.py`
   - Cap payout at various rates
   - Collar payout including negative scenarios
   - CFADS adjustment correctness

2. **Integration tests**:
   - Run with 100 sims, verify output structure
   - Check that hedged breach prob <= unhedged

3. **Validation**:
   - Hand-calculate expected payout for single path
   - Verify against simulation output

---

## FILE RENAME DECISION

**Recommendation**: Rename `wp05_risk_metrics.json` → `leo_iot_results.json` ✓ DONE

**Justification**:
- Contains results from WP-05 (risk metrics), WP-11 (hedging), WP-12 (contingent amortization), WP-13 (hedging comparison)
- Project-specific naming for LEO IoT satellite constellation
- Single source of truth for all quantitative results

**Files to Update**:
- `scripts/demo_risk_metrics.py` (output path)
- `docs/wp11_comprehensive_analysis.md` (references)
- Any tests that read the output file
