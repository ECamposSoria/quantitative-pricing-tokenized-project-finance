# DCF ↔ AMM Integration Guide (WP-14)

## Pricing Loop
1. Run `FinancialPipeline` to obtain cashflows/DCF marks.
2. Observe pool price (v2/v3) and simulate execution via `market_price.execution_price`.
3. Blend DCF and AMM marks with `dcf_integration.blend_with_arbitrage`, passing the arb convergence result if available.
4. Emit arbitrage signals with `market_price.arbitrage_signal` or Almgren–Chriss metrics for reporting.

## IL / LP Analytics
1. Compute IL for price moves: `impermanent_loss.il_v2` or `il_v3_range`.
2. Build IL surfaces across ranges for dashboards: `impermanent_loss.il_surface`.
3. Decompose LP PnL with `lp_pnl.pnl_decomposition` (optionally passing tick bounds for v3 ranges).

## Stress + WP-09 Export
1. Select scenarios from `amm_stress_scenarios.build_scenarios()`.
2. Call `amm_metrics_export.get_stress_metrics(pool, scenarios)` to obtain:
   - `depth_curve`, `slippage_curve`, `stressed_depths`, `il_by_scenario`, `recovery_steps`.
3. Feed metrics to dashboards or WP-09 consumer. CLI: `python scripts/run_amm_stress.py --scenarios PS LP FC`.

## Visualization Hooks
Pass `include_amm=True` and `amm_context` into `dashboards.build_financial_dashboard` with keys:
- `pool_prices`, `dcf_prices`
- `il_surface`, `ratios`, `ranges`
- `stress_results` (dict name -> liquidity path)
- `depth_curve`

## Notes
- Fee model: fee-on-input for both v2 and v3.
- Swaps mutate pool state; for read-only paths prefer `simulate_swap` (v3) or pure pricing helpers.
