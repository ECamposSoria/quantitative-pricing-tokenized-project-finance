# API Reference

This reference will catalogue public classes and functions exposed by `pftoken`.

## Status

> Placeholder pending implementation.

## AMM Module Snapshot

- `pftoken.amm.core.pool_v2.ConstantProductPool`: constant-product invariant with simple swap simulation.
- `pftoken.amm.core.pool_v3.ConcentratedLiquidityPool`: tick-based liquidity scaffolding.
- `pftoken.amm.pricing.market_price.spot_price`: read instantaneous pool price.
- `pftoken.amm.analysis.impermanent_loss.impermanent_loss`: compute IL for price movements.
- `pftoken.amm.analysis.range_optimizer.optimize_ticks`: optimise tick ranges via SciPy.

## Core Financial Models

- `pftoken.models.ProjectParameters.from_directory`: carga y valida parámetros financieros/operativos desde los CSV base.
- `pftoken.models.calculate_cfads`: calcula CFADS anual devolviendo un `CFADSStatement` con el detalle del estado de resultados.
- `pftoken.models.CFADSScenarioInputs`: encapsula shocks operativos/financieros aplicados al cálculo base.
