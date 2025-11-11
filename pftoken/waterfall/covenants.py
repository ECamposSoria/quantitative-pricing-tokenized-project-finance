"""Debt covenant evaluation utilities (WP-03)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable, List, Optional

from pftoken.config.defaults import DEFAULT_COVENANT_LIMITS, CovenantLimits
from pftoken.models.ratios import LLCRObservation

class CovenantSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CovenantType(str, Enum):
    DSCR = "dscr"
    LLCR = "llcr"
    LTV = "ltv"


@dataclass(frozen=True)
class Covenant:
    name: str
    metric: CovenantType
    threshold: float
    action: str
    severity: CovenantSeverity = CovenantSeverity.LOW


@dataclass
class CovenantBreach:
    covenant: Covenant
    metric_value: float
    period: int


class CovenantEngine:
    """Evaluates covenant metrics and tracks breaches across periods."""

    def __init__(
        self,
        covenants: Iterable[Covenant] | None = None,
        *,
        limits: CovenantLimits | None = None,
    ):
        self.limits = limits or DEFAULT_COVENANT_LIMITS
        self.covenants = list(covenants) if covenants is not None else self._build_default_covenants()
        self.breach_history: List[CovenantBreach] = []

    def find_covenant(self, metric: CovenantType) -> Optional[Covenant]:
        for covenant in self.covenants:
            if covenant.metric == metric:
                return covenant
        return None

    def check_breach(self, metric: CovenantType, value: float, period: int) -> Optional[CovenantBreach]:
        covenant = self.find_covenant(metric)
        if covenant is None:
            return None
        if value < covenant.threshold:
            breach = CovenantBreach(covenant=covenant, metric_value=value, period=period)
            self.breach_history.append(breach)
            return breach
        return None

    def apply_covenant_actions(self, dscr_value: float, period: int) -> Dict[str, bool]:
        """
        Evaluate DSCR tiers and translate them into enforcement actions.

        Returns a dictionary with flags for dividends, sweep, and default events.
        """

        actions = {
            "block_dividends": False,
            "cash_sweep": False,
            "technical_default": False,
        }
        breach = self.check_breach(CovenantType.DSCR, dscr_value, period)
        if breach is None:
            return actions

        if dscr_value < 1.0:
            actions["technical_default"] = True
            actions["cash_sweep"] = True
            actions["block_dividends"] = True
        elif dscr_value < 1.15:
            actions["cash_sweep"] = True
            actions["block_dividends"] = True
        else:
            actions["block_dividends"] = True
        return actions

    def evaluate_llcr(self, llcr_results: Dict[str, LLCRObservation], period: int) -> List[CovenantBreach]:
        breaches: List[CovenantBreach] = []
        for observation in llcr_results.values():
            if observation.value < observation.threshold:
                breach = CovenantBreach(
                    covenant=Covenant(
                        name=f"LLCR {observation.tranche}",
                        metric=CovenantType.LLCR,
                        threshold=observation.threshold,
                        action="restrict_releverage",
                        severity=CovenantSeverity.MEDIUM,
                    ),
                    metric_value=observation.value,
                    period=period,
                )
                breaches.append(breach)
                self.breach_history.append(breach)
        return breaches

    def _build_default_covenants(self) -> List[Covenant]:
        return [
            Covenant(
                name="DSCR Minimum",
                metric=CovenantType.DSCR,
                threshold=self.limits.min_dscr,
                action="block_dividends",
                severity=CovenantSeverity.MEDIUM,
            )
        ]


__all__ = [
    "Covenant",
    "CovenantBreach",
    "CovenantEngine",
    "CovenantSeverity",
    "CovenantType",
]
