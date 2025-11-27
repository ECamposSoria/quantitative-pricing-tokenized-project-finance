# AMM Overview

WP-14 adds an AMM analytics layer atop the DCF toolkit. The package covers:

- Core pools: constant product (v2) and concentrated liquidity (v3) with tick math and fee-on-input swaps.
- Pricing: execution prices with slippage, depth curves, arbitrage signals, Almgren–Chriss convergence engine.
- Analytics: impermanent loss (v2 + v3 range-aware), LP PnL decomposition, IL surfaces and fee breakeven.
- Stress: Panic Sell, LP withdrawal, and Flash Crash scenarios with WP-09 export metrics.
- Visualization: price vs DCF, IL heatmaps, stress paths, depth curves.

Integration points and architecture details live in `docs/amm/architecture.md` and `docs/amm/integration_guide.md`. Use the CLI `scripts/run_amm_stress.py` for quick scenario runs.
