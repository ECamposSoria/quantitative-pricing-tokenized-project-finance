"""Governance and reporting helpers (off-chain design only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional

from .governance_interfaces import GovernancePolicy, IGovernanceAction, IOracle


@dataclass
class StaticOracle:
    """Simple oracle returning a fixed payload (used for testing/documentation)."""

    name: str
    payload: Mapping[str, float]

    def fetch(self) -> Mapping[str, float]:
        return dict(self.payload)


@dataclass
class ThresholdPolicy:
    """Triggers when a metric falls below a locked threshold."""

    name: str
    metric: str
    threshold: float
    action_ids: List[str]

    def should_trigger(self, metrics: Mapping[str, float]) -> bool:
        value = metrics.get(self.metric)
        return value is not None and value < self.threshold

    def actions(self) -> List[str]:
        return list(self.action_ids)


@dataclass
class LoggingAction:
    """Records the execution context instead of performing on-chain work."""

    name: str
    log: List[Dict[str, float]] = field(default_factory=list)

    def execute(self, *, period: int, metrics: Mapping[str, float]) -> None:
        payload = dict(metrics)
        payload["period"] = period
        self.log.append(payload)


class GovernanceController:
    """
    Coordinates oracle reads and policies, executing registered actions.

    This is intentionally off-chain; the caller is responsible for wiring the
    outputs into smart contracts or reporting layers.
    """

    def __init__(
        self,
        oracles: Iterable[IOracle],
        policies: Iterable[GovernancePolicy],
        actions: Mapping[str, IGovernanceAction],
    ):
        self.oracles = list(oracles)
        self.policies = list(policies)
        self.actions = dict(actions)

    def collect_metrics(self) -> Dict[str, float]:
        metrics: Dict[str, float] = {}
        for oracle in self.oracles:
            metrics.update(oracle.fetch())
        return metrics

    def run_cycle(self, period: int, extra_metrics: Optional[Mapping[str, float]] = None) -> Dict[str, bool]:
        metrics = self.collect_metrics()
        if extra_metrics:
            metrics.update(extra_metrics)
        executed: Dict[str, bool] = {}
        for policy in self.policies:
            if not policy.should_trigger(metrics):
                continue
            for action_id in policy.actions():
                action = self.actions.get(action_id)
                if action is None:
                    continue
                action.execute(period=period, metrics=metrics)
                executed[action_id] = True
        return executed


__all__ = [
    "GovernanceController",
    "LoggingAction",
    "StaticOracle",
    "ThresholdPolicy",
]
