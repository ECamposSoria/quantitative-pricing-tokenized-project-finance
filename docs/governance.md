## Governance Framework (WP-03 / T-020)

This repository models governance as an **off-chain controller** that aggregates
deterministic telemetry from Python oracles and evaluates simple policies before
triggering actions. The intent is to document how waterfall automation could be
connected to token-holder decisions without deploying smart contracts inside
this codebase.

### Components

| Component | Responsibility |
| --- | --- |
| `pftoken.waterfall.governance_interfaces.IOracle` | Structural protocol for data sources such as DSCR feeds, reserve balances, or AMM prices. |
| `StaticOracle` | Reference implementation returning deterministic payloads (used in tests). |
| `ThresholdPolicy` | Triggers when a metric breaches a threshold (e.g., DSCR < 1.15). |
| `LoggingAction` | Placeholder action that records execution context instead of touching on-chain state. |
| `GovernanceController` | Coordinates oracle reads, evaluates policies, and executes the registered actions. |

### Lifecycle

1. Collect metrics from all registered oracles (`controller.collect_metrics()`).
2. Evaluate each policy against the metric map.
3. Execute the linked actions when a policy returns `True`.
4. Persist the events (on-chain integration would occur here).

### Example

```python
from pftoken.waterfall import (
    GovernanceController,
    LoggingAction,
    StaticOracle,
    ThresholdPolicy,
)

oracle = StaticOracle(name="dscr_oracle", payload={"dscr": 1.05})
action = LoggingAction(name="block_dividends")
policy = ThresholdPolicy(
    name="Low DSCR",
    metric="dscr",
    threshold=1.20,
    action_ids=[action.name],
)

controller = GovernanceController(
    oracles=[oracle],
    policies=[policy],
    actions={action.name: action},
)

controller.run_cycle(period=6)
```

### Notes

- All metrics/actions are purely off-chain. Connecting them to smart contracts
  would require additional signing, multi-sig management, and oracle security.
- Policies can be extended to support quorum checks or multi-threshold
  workflows (e.g., advisory warnings vs. hard enforcement).
- The current implementation focuses on WP-02/03 requirements: block dividends,
  enable cash sweeps, and log decisions for dashboards/QA.
