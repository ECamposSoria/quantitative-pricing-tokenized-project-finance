"""Dataclasses and shared contracts for stochastic pricing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence, TYPE_CHECKING

from pftoken.pricing.base_pricing import TrancheCashFlow
from pftoken.pricing.zero_curve import ZeroCurve
from pftoken.waterfall.debt_structure import DebtStructure

if TYPE_CHECKING:  # avoid runtime import cycles
    from pftoken.simulation import PipelineOutputs


@dataclass(frozen=True)
class RateScenarioDefinition:
    """Named rate scenario used for curve shocks."""

    name: str
    parallel_bps: float = 0.0
    bucket_shocks: Mapping[tuple[float, float], float] | None = None


@dataclass(frozen=True)
class PriceDistribution:
    """Summary stats for a price distribution."""

    mean: float
    std: float
    p5: float
    p50: float
    p95: float
    p99: float
    prob_below_par: float
    deterministic_price: float | None = None
    jensen_adjustment: float | None = None

    def to_dict(self) -> dict[str, float | None]:
        return {
            "mean": self.mean,
            "std": self.std,
            "p5": self.p5,
            "p50": self.p50,
            "p95": self.p95,
            "p99": self.p99,
            "prob_below_par": self.prob_below_par,
            "deterministic_price": self.deterministic_price,
            "jensen_adjustment": self.jensen_adjustment,
        }


@dataclass(frozen=True)
class StochasticPricingInputs:
    """
    Contract for stochastic pricing.

    Attributes:
        mc_outputs: Result of MonteCarloPipeline (WP-07).
        base_curve: Zero curve snapshot used as starting point.
        debt_structure: DebtStructure with tranche metadata (tenor, principal).
        tranche_cashflows: Optional deterministic cashflows per tranche (fallback
            when MC cashflow paths are not provided). Cashflows are expected as
            lists of TrancheCashFlow objects.
        scenarios: Optional list of scenario names to evaluate; when omitted,
            only the base scenario is priced.
        batch_size: Optional subsampling window for large MC runs.
    """

    mc_outputs: "PipelineOutputs"
    base_curve: ZeroCurve
    debt_structure: DebtStructure
    tranche_cashflows: Mapping[str, Sequence[TrancheCashFlow]] | None = None
    scenarios: Sequence[str] | None = None
    batch_size: int | None = None


@dataclass
class StochasticPricingResult:
    """Aggregated pricing output per tranche."""

    tranche_prices: dict[str, PriceDistribution] = field(default_factory=dict)
    scenario_metadata: dict[str, object] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "tranche_prices": {k: v.to_dict() for k, v in self.tranche_prices.items()},
            "scenario_metadata": self.scenario_metadata,
            "notes": self.notes,
        }


__all__ = [
    "RateScenarioDefinition",
    "PriceDistribution",
    "StochasticPricingInputs",
    "StochasticPricingResult",
]
