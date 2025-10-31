# Constant Product vs. Concentrated Liquidity

| Aspect | Uniswap v2 (Constant Product) | Uniswap v3 (Concentrated Liquidity) |
| --- | --- | --- |
| Liquidity distribution | Uniform across all prices | User-defined ranges (ticks) |
| State variables | Reserves (x, y) | Reserves + tick bitmap + liquidity |
| Fee tiers | Single (per pool) | Multiple (per pool/position) |
| Capital efficiency | Baseline | Higher when price stays within range |

The scaffolded implementation mirrors these properties at a high level
without yet modeling full on-chain intricacies (tick bitmaps, fee growth
global accumulators, etc.). Use the AMM analysis utilities to stress-test
LP strategies under both paradigms.
