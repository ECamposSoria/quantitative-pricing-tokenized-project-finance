"""Delta decomposition utilities for tokenized spread components."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Dict


@dataclass
class PerTrancheDeltaBreakdown:
    """Delta (traditional - tokenized) per component for a tranche."""

    tranche: str
    principal_usd: float
    delta_credit_bps: float
    delta_liquidity_bps: float
    delta_origination_bps: float
    delta_servicing_bps: float
    delta_infrastructure_bps: float

    @property
    def total_delta_bps(self) -> float:
        return (
            self.delta_credit_bps
            + self.delta_liquidity_bps
            + self.delta_origination_bps
            + self.delta_servicing_bps
            + self.delta_infrastructure_bps
        )


@dataclass
class ConsolidatedDeltaDecomposition:
    """Weighted aggregation of per-tranche deltas."""

    per_tranche: Dict[str, PerTrancheDeltaBreakdown]
    weighted_delta_credit_bps: float
    weighted_delta_liquidity_bps: float
    weighted_delta_origination_bps: float
    weighted_delta_servicing_bps: float
    weighted_delta_infrastructure_bps: float

    @property
    def total_weighted_delta_bps(self) -> float:
        return (
            self.weighted_delta_credit_bps
            + self.weighted_delta_liquidity_bps
            + self.weighted_delta_origination_bps
            + self.weighted_delta_servicing_bps
            + self.weighted_delta_infrastructure_bps
        )

    def to_dict(self) -> Dict:
        return {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "per_tranche": {
                name: {
                    **asdict(delta),
                    "total_delta_bps": delta.total_delta_bps,
                }
                for name, delta in self.per_tranche.items()
            },
            "weighted_totals": {
                "delta_credit_bps": self.weighted_delta_credit_bps,
                "delta_liquidity_bps": self.weighted_delta_liquidity_bps,
                "delta_origination_bps": self.weighted_delta_origination_bps,
                "delta_servicing_bps": self.weighted_delta_servicing_bps,
                "delta_infrastructure_bps": self.weighted_delta_infrastructure_bps,
                "total_weighted_delta_bps": self.total_weighted_delta_bps,
            },
        }

