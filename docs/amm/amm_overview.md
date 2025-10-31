# AMM Overview

> **Status:** Placeholder – outline of the Automated Market Maker module.

The AMM package extends the deterministic DCF toolkit with constant-product
and concentrated-liquidity pools. It introduces:

- Core pool abstractions for Uniswap v2 and v3 style mechanics.
- Liquidity management helpers and swap execution intents.
- Pricing adapters to reconcile pool marks with DCF valuations.
- Analysis helpers for impermanent loss, LP PnL, and liquidity depth.

Future iterations will connect these components to stress testing and Monte
Carlo scenarios to deliver a unified project-finance + AMM simulation stack.
