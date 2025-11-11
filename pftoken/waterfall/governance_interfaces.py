"""Protocol definitions for governance-related components."""

from __future__ import annotations

from typing import Mapping, Protocol, runtime_checkable


@runtime_checkable
class IOracle(Protocol):
    """Oracle interface for off-chain metrics."""

    name: str

    def fetch(self) -> Mapping[str, float]:
        ...


@runtime_checkable
class IGovernanceAction(Protocol):
    """Action executed when a governance policy triggers."""

    name: str

    def execute(self, *, period: int, metrics: Mapping[str, float]) -> None:
        ...


@runtime_checkable
class GovernancePolicy(Protocol):
    """Definition of a policy that decides when to trigger governance actions."""

    name: str

    def should_trigger(self, metrics: Mapping[str, float]) -> bool:
        ...

    def actions(self) -> list[str]:
        ...


__all__ = ["IOracle", "IGovernanceAction", "GovernancePolicy"]
