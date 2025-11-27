# Impermanent Loss (V2 and V3)

## Overview
Impermanent loss (IL) measures the value drag a liquidity provider (LP) experiences versus simply holding the underlying tokens. It is path-independent for constant product AMMs (v2) and path- and range-dependent for concentrated liquidity (v3). This note documents the approximations used in this codebase for WP-14 analytics.

## V2 Closed Form
- Invariant: `x * y = k`
- Price: `P = y / x` (token1 per token0)
- Price move: `r = P_new / P_old`
- Impermanent loss (fraction):  
  ```
  IL_v2(r) = 2 * sqrt(r) / (1 + r) - 1
  ```

## V3 Range-Aware Approximation
Given a position with tick bounds `(t_lower, t_upper)`:
- Map ticks to prices: `P = 1.0001^tick`
- Convert to square roots for math: `sqrtP = sqrt(P)`
- Unit liquidity `L = 1` for relative IL (scales out)

Token holdings at price `sqrtP`:
- If `sqrtP <= sqrtP_lower`: all token0  
  `amount0 = L * (1/sqrtP_lower - 1/sqrtP_upper)`
- If `sqrtP >= sqrtP_upper`: all token1  
  `amount1 = L * (sqrtP_upper - sqrtP_lower)`
- If inside range:  
  `amount0 = L * (1/sqrtP - 1/sqrtP_upper)`  
  `amount1 = L * (sqrtP - sqrtP_lower)`

IL computation:
1. Compute amounts at start price `P_start` → `(x0, y0)`
2. Compute amounts at end price `P_end` → `(x1, y1)`
3. Hold value at end: `V_hold = x0 * P_end + y0`
4. LP value at end: `V_lp = x1 * P_end + y1`
5. Range IL (fraction): `IL_v3 = V_lp / V_hold - 1`

Notes:
- This ignores fees and assumes constant liquidity `L` across the range.
- When price exits the range, the position becomes fully one-sided; IL versus hold reflects lost exposure to the other asset and can be large in magnitude.

## IL Surfaces
To build heatmaps, evaluate `IL_v3` over:
- Price ratios `r = P_new / P_old` (baseline `P_old = 1`)
- Multiple tick ranges `(t_lower, t_upper)`
Result is a grid `len(ratios) x len(ranges)` for visualization.

## Fee Breakeven
Given an absolute IL amount `|IL|` (same units as fees):
- Daily fees `f_d` (per day)
- Holding period `T` days
- Breakeven days: `days = |IL| / f_d` (if `f_d > 0`)
- If `days > T` or `f_d <= 0`, breakeven is considered unattainable (`∞`).
