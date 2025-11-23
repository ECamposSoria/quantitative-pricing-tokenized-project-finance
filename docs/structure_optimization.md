# Tokenized Structure Optimization (WP-05/WP-04 Link)

## Goal
Quantify how a tokenized rebalancing of the tranche weights can improve the risk/return/WACD profile relative to the traditional 60/25/15 structure, without altering the traditional baseline.

## Methodology
- Frontier generation: WP-05 efficient frontier with 500 Dirichlet samples, seed=42.
- Metrics: 3D Pareto across (risk ↓, return ↑, WACD ↓). WACD computed after-tax using `WACDCalculator.compute_with_weights`.
- Tolerance: ±1% when evaluating “held equal” dimensions (risk, return, WACD).
- Inputs: PD/LGD (senior 1%/40%, mezz 3%/55%, sub 10%/100%), correlation matrix [[1,0.3,0.2],[0.3,1,0.4],[0.2,0.4,1]], simulations=10,000, seed=42. Tranche returns: senior 6.0%, mezz 8.5%, sub 12.0%.

## Selection
- Current (traditional) structure: 60/25/15; WACD ≈ 5.53%, return ≈ 7.52%, risk ≈ 2.60M.
- Candidate (tokenized optimized): **55/34/12** chosen because:
  - Operational feasibility: subordinated at ~12% (~$7.0M) is more realistic than ultra-small (~8%) subordinated tickets.
  - Lower WACD than other feasible candidates (≈5.57% vs ≈5.59% for 50/41/8).
  - Risk reduction of ~6% vs current while holding return and WACD within the 1% tolerance.
  - Balanced, mezz-heavy allocation aligns with the risk-adjusted return sweet spot seen in the frontier.
- Traditional structure remains unchanged (60/25/15); the optimized structure is proposed only for the tokenized scenario.

## Outputs (report integration)
- `scripts/generate_wp04_report.py` adds a “Tokenizado (óptimo)” row using 55/34/12 and reports its WACD and delta vs traditional.
- No CSV inputs are changed; tranches.csv and debt_schedule.csv stay at 60/25/15 for the traditional baseline and tests.

## Caveats
- Frontier sampling is stochastic; results are contingent on the sample grid (500 draws, seed=42).
- No regulatory/rating constraints applied in the optimized case; traditional constraints still bind the baseline.
- For tighter confidence, increase samples or run deterministic grid sweeps; current run is indicative, not exhaustive.
