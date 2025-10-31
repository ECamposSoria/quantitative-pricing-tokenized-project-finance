# Liquidity Optimisation Blueprint

The `range_optimizer.optimize_ticks` helper wraps SciPy's L-BFGS-B solver to
produce symmetric tick ranges around a target price. The objective function
penalises deviation from the target mid-price and discourages excessively
narrow ranges.

Suggested next steps:

- Replace the placeholder objective with a fee/APY model derived from historical fills.
- Add constraints for capital budgets and risk tolerance.
- Extend the CLI tool `scripts/optimize_pool_ranges.py` with data loading hooks.
