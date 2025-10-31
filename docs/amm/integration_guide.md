# DCF ↔ AMM Integration Guide

1. Generate deterministic cashflows (CFADS) using the existing project finance models.
2. Convert cashflows into AMM liquidity actions via `pftoken.integration.dcf_to_amm.allocate_liquidity`.
3. Propagate Monte Carlo shocks to market prices with `scenario_propagation.propagate_shocks`.
4. Feed observed spreads back into discount curves using `feedback_loop.update_discount_rate`.
5. Evaluate liquidity resilience through `stress.liquidity_stress`.

This workflow provides a blueprint for linking financing models with on-chain
market dynamics. Replace the placeholder logic with production code as the
project evolves.
