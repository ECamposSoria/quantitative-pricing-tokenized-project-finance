# System Architecture

This document will detail the architecture for the project finance tokenization platform.

## Status

> Placeholder: awaiting detailed design input.

## High-Level Components

- **Deterministic Layer:** CFADS models, waterfall engine, pricing analytics.
- **Stochastic Layer:** Monte Carlo simulation, stress testing, optimisation.
- **AMM Layer:** New `pftoken.amm` package providing pool mechanics, pricing adapters, and liquidity analysis.
- **Integration Layer:** Bridges DCF outputs with AMM state updates and feedback loops.

Future iterations will add sequence diagrams and deployment topology once the implementation stabilises.
