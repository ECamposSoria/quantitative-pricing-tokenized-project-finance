# WP-14 AMM Architecture (Simplified)

## Goals
- Model Uniswap v2/v3 style AMMs for pricing, IL/LP analytics, and stress testing.
- Bridge deterministic DCF valuations with market-driven AMM marks.
- Export stress metrics for WP-09 dashboards.

## Module Map
- Core: `pftoken/amm/core`
  - `pool_v2`: constant-product with fee-on-input.
  - `pool_v3`: concentrated liquidity with Q64.96 tick math, tick crossings, fee-on-input.
  - `swap_engine`: routes intents to V2/V3 pools.
  - `sqrt_price_math`: tick <-> sqrtPriceX96 helpers and deltas.
- Pricing: `pftoken/amm/pricing`
  - `market_price`: spot, execution price with slippage, depth curves, signals.
  - `slippage`: slippage percent/curves.
  - `arbitrage_engine`: Almgren–Chriss style trajectories and convergence metrics.
  - `dcf_integration`: blend DCF with AMM price + arb penalty.
- Analysis: `pftoken/amm/analysis`
  - `impermanent_loss`: v2 closed form, v3 range approximation, IL surfaces, fee breakeven.
  - `lp_pnl`: PnL decomposition (fees, IL, appreciation) with v2/v3 awareness.
- Stress: `pftoken/stress`
  - `amm_stress_scenarios`: Panic Sell, LP withdrawal, Flash Crash templates.
  - `liquidity_stress`: scenario math + IL/slippage paths.
  - `amm_metrics_export`: WP-09 export (depth, slippage, IL by scenario, recovery steps).
- Visualization: `pftoken/viz/amm_viz`, `dashboards.py` hooks.
- CLI: `scripts/run_amm_stress.py`.

## Data Flow
1) Pricing: pool price -> execution_price/depth -> arbitrage signals -> DCF blend via `blend_with_arbitrage`.
2) Analytics: price ratios -> IL (v2/v3) -> PnL decomposition.
3) Stress: scenarios -> `get_stress_metrics` -> WP-09 consumer; viz hooks consume depth/paths/IL.

## Key Types
- `SwapResult` (v3), `SwapQuote` (v2): amount_in/out, fee, final price/tick.
- `ScenarioOutcome`: price/liquidity paths, slippage curve, IL, recovery steps.
- `AMMStressMetrics`: depth curves, slippage, IL by scenario, recovery steps.

## Determinism & Safety
- Deterministic seeds not required (analytic), but scenario steps are fixed.
- Fee-on-input model aligns with Uniswap v3 spec.
- Q64.96 math kept in Python ints; boundaries clamped by MIN/MAX ticks.

## Usage Quickstart
- Simulate swap: `pool_v3.ConcentratedLiquidityPool.simulate_swap(amount, "token0")`
- Execution price: `market_price.execution_price(pool, amount, side)`
- IL surface: `impermanent_loss.il_surface(ratios, ranges)`
- Stress export: `get_stress_metrics(pool, build_scenarios().values())`
- CLI: `python scripts/run_amm_stress.py --reserve0 1000 --reserve1 1000 --scenarios PS LP`

## Testing
- Unit: `tests/test_amm/*` (swap math, pricing/slippage, IL/LP, arb engine).
- Integration: `tests/test_integration/test_amm_stress.py`.

## Future Extensions
- Add hypothesis/property tests for tick invariants.
- Path-dependent IL for dynamic fee accrual.
- Monte Carlo integration for stochastic prices/liquidity.
- Multi-pool routing and gas/MEV-aware pricing.
