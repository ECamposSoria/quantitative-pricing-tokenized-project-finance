## Calibration Notes (T-047 Placeholder)

The project ships with a deterministic calibration stored at
`data/derived/leo_iot/stochastic_params.yaml`. This file is generated from the
locked Excel workbook and must **never** overwrite the canonical CSV inputs in
`data/input/leo_iot/`.

### Contents

```yaml
version: 0.1.0
as_of: 2025-11-11
description: Placeholder deterministic calibration for WP-02/WP-03 testing (full T-047 pending T-022/T-023).
params:
  senior:
    asset_volatility: 0.22
    spread_bps: 150
    recovery_rate: 0.55
    pd_floor: 0.015
  mezzanine:
    asset_volatility: 0.28
    spread_bps: 325
    recovery_rate: 0.40
    pd_floor: 0.035
  subordinated:
    asset_volatility: 0.35
    spread_bps: 575
    recovery_rate: 0.25
    pd_floor: 0.065
random_variables:
  revenue_growth:
    distribution: lognormal
    mu: 0.065
    sigma: 0.18
  churn_rate:
    distribution: beta
    alpha: 2.1
    beta: 8.4
  rate_shock:
    distribution: normal
    mean: 0.0
    sigma: 0.015
  launch_failure:
    distribution: bernoulli
    probability: 0.07
  opex_inflation:
    distribution: lognormal
    mu: 0.03
    sigma: 0.07
correlation:
  variables: [revenue_growth, churn_rate, rate_shock, launch_failure, opex_inflation]
  matrix:
    - [1.0, -0.35, 0.25, 0.10, 0.30]
    - [-0.35, 1.0, -0.15, -0.05, -0.25]
    - [0.25, -0.15, 1.0, 0.05, 0.20]
    - [0.10, -0.05, 0.05, 1.0, 0.05]
    - [0.30, -0.25, 0.20, 0.05, 1.0]
```

These values unlock WP-02/03 tests (Merton PD/LGD/EL) while the full stochastic
tasks remain pending. The loader lives in
`pftoken.models.calibration.load_placeholder_calibration` and feeds
`pftoken.simulation.StochasticVariables` plus the correlated sampler.

### Workflow

1. Generate updated placeholders via the Excel validation workbook (manual step).
2. Export to `data/derived/leo_iot/stochastic_params.yaml`.
3. Commit the YAML alongside documentation updates in this file.

### Constraints

- `data/input/leo_iot/` remains immutable—no scripts may touch these CSVs.
- Placeholder params are deterministic; Monte Carlo surfaces (T-021+) can now
  consume them via `StochasticVariables`/`CorrelatedSampler`, but real-world
  calibration still depends on T-022/T-023 deliverables.
- Tests enforce that every modeled PD/LGD/EL stays within 0.01% of the placeholder.
