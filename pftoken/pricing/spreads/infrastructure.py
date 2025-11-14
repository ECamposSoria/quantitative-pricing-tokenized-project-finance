"""Blockchain infrastructure cost tracker and CSV exporter."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from .base import SpreadComponentResult, TokenizedSpreadConfig, TrancheSpreadInputs

DEFAULT_ETH_PRICE_USD = 3000.0
BPS_PER_UNIT = 10_000.0


@dataclass(frozen=True)
class NetworkCostProfile:
    """Static inputs describing expected annual infra costs for a network."""

    name: str
    annual_tx_count: int
    gas_per_tx: int
    gas_price_gwei: float
    oracle_bps: float
    monitoring_bps: float
    security_score: float
    liquidity_score: float
    regulation_score: float
    ux_score: float
    gas_token_price_usd: float = DEFAULT_ETH_PRICE_USD
    metadata: Dict[str, str] = field(default_factory=dict)


DEFAULT_NETWORK_PROFILES: Dict[str, NetworkCostProfile] = {
    "Ethereum": NetworkCostProfile(
        name="Ethereum",
        annual_tx_count=200,
        gas_per_tx=110_000,
        gas_price_gwei=25.0,
        oracle_bps=3.0,
        monitoring_bps=2.0,
        security_score=5.0,
        liquidity_score=4.5,
        regulation_score=3.5,
        ux_score=2.5,
        metadata={
            "gas_price_source": "Placeholder – use scripts/update_blockchain_infra.py (Etherscan Gas Tracker).",
            "oracle_source": "Chainlink public docs (pricing overview).",
            "monitoring_source": "Operations assumption (docs/tokenized_spread_decomposition.md).",
        },
    ),
    "Arbitrum": NetworkCostProfile(
        name="Arbitrum",
        annual_tx_count=200,
        gas_per_tx=35_000,
        gas_price_gwei=1.5,
        oracle_bps=4.0,
        monitoring_bps=2.5,
        security_score=3.5,
        liquidity_score=3.0,
        regulation_score=3.0,
        ux_score=3.5,
        metadata={
            "gas_price_source": "Placeholder – Arbiscan Gas Tracker.",
            "oracle_source": "Chainlink public docs (pricing overview).",
            "monitoring_source": "Operations assumption (docs/tokenized_spread_decomposition.md).",
        },
    ),
    "Polygon": NetworkCostProfile(
        name="Polygon",
        annual_tx_count=200,
        gas_per_tx=45_000,
        gas_price_gwei=0.9,
        oracle_bps=4.0,
        monitoring_bps=2.5,
        security_score=3.0,
        liquidity_score=3.5,
        regulation_score=3.0,
        ux_score=3.8,
        gas_token_price_usd=0.8,
        metadata={
            "gas_price_source": "Placeholder – Polygonscan Gas Station.",
            "oracle_source": "Chainlink public docs (pricing overview).",
            "monitoring_source": "Operations assumption (docs/tokenized_spread_decomposition.md).",
        },
    ),
    "Optimism": NetworkCostProfile(
        name="Optimism",
        annual_tx_count=200,
        gas_per_tx=40_000,
        gas_price_gwei=1.2,
        oracle_bps=4.5,
        monitoring_bps=2.5,
        security_score=3.3,
        liquidity_score=3.0,
        regulation_score=3.0,
        ux_score=3.2,
        metadata={
            "gas_price_source": "Placeholder – Optimistic Etherscan Gas Tracker.",
            "oracle_source": "Chainlink public docs (pricing overview).",
            "monitoring_source": "Operations assumption (docs/tokenized_spread_decomposition.md).",
        },
    ),
    "Base": NetworkCostProfile(
        name="Base",
        annual_tx_count=200,
        gas_per_tx=28_000,
        gas_price_gwei=1.0,
        oracle_bps=4.0,
        monitoring_bps=2.2,
        security_score=3.2,
        liquidity_score=2.8,
        regulation_score=2.8,
        ux_score=3.5,
        metadata={
            "gas_price_source": "Placeholder – Basescan Gas Tracker.",
            "oracle_source": "Chainlink public docs (pricing overview).",
            "monitoring_source": "Operations assumption (docs/tokenized_spread_decomposition.md).",
        },
    ),
}


class BlockchainInfrastructureTracker:
    """Computes blockchain infra spreads and persists assumption tables."""

    def __init__(self, config: TokenizedSpreadConfig):
        self.config = config
        self._profiles: Dict[str, NetworkCostProfile] | None = None

    def compute(self, inputs: TrancheSpreadInputs) -> SpreadComponentResult:
        profile = self._get_profile(self.config.blockchain_network)
        total_bps, metadata = self._calculate_bps(profile, inputs.principal)
        overrides = self.config.infra_overrides or {}
        if profile.name in overrides:
            total_bps = overrides[profile.name]
            metadata["override_bps"] = total_bps
        return SpreadComponentResult("infrastructure", 0.0, total_bps, metadata)

    def export_cost_table(self, reference_principal: float = 100_000_000.0) -> Path:
        rows = []
        for profile in self._profiles_or_defaults().values():
            total_bps, metadata = self._calculate_bps(profile, reference_principal)
            row = {
                "network": profile.name,
                "reference_principal": reference_principal,
                "annual_tx_count": profile.annual_tx_count,
                "gas_per_tx": profile.gas_per_tx,
                "gas_price_gwei": profile.gas_price_gwei,
                "gas_token_price_usd": profile.gas_token_price_usd,
                "gas_price_source": profile.metadata.get("gas_price_source", ""),
                "oracle_bps": profile.oracle_bps,
                "oracle_source": profile.metadata.get("oracle_source", ""),
                "monitoring_bps": profile.monitoring_bps,
                "monitoring_source": profile.metadata.get("monitoring_source", ""),
                "risk_premium_bps": metadata["risk_premium_bps"],
                "gas_cost_bps": metadata["gas_cost_bps"],
                "total_bps": total_bps,
                "security_score": profile.security_score,
                "liquidity_score": profile.liquidity_score,
                "regulation_score": profile.regulation_score,
                "ux_score": profile.ux_score,
                "notes": profile.metadata.get("notes", ""),
            }
            rows.append(row)
        path = Path(self.config.infrastructure_csv_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        assumption_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()[:12]
        for row in rows:
            row["timestamp_utc"] = timestamp
            row["assumption_hash"] = assumption_hash
        with path.open("w", newline="") as fp:
            writer = csv.DictWriter(fp, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        return path

    def _get_profile(self, name: str) -> NetworkCostProfile:
        profiles = self._profiles_or_defaults()
        key = name.strip()
        if key not in profiles:
            raise KeyError(f"Unsupported network '{name}'. Available: {', '.join(profiles)}")
        return profiles[key]

    def _profiles_or_defaults(self) -> Dict[str, NetworkCostProfile]:
        if self._profiles is None:
            self._profiles = dict(DEFAULT_NETWORK_PROFILES)
            csv_profiles = load_network_profiles_from_csv(Path(self.config.infrastructure_csv_path))
            self._profiles.update(csv_profiles)
        return self._profiles

    def _calculate_bps(self, profile: NetworkCostProfile, principal: float) -> tuple[float, Dict[str, float]]:
        gas_cost_usd = (
            profile.annual_tx_count * profile.gas_per_tx * profile.gas_price_gwei * 1e-9 * profile.gas_token_price_usd
        )
        gas_cost_bps = gas_cost_usd / max(principal, 1.0) * BPS_PER_UNIT
        risk_premium_bps = self._risk_premium(profile)
        total_bps = gas_cost_bps + profile.oracle_bps + profile.monitoring_bps + risk_premium_bps
        metadata = {
            "gas_cost_usd": gas_cost_usd,
            "gas_cost_bps": gas_cost_bps,
            "oracle_bps": profile.oracle_bps,
            "monitoring_bps": profile.monitoring_bps,
            "risk_premium_bps": risk_premium_bps,
            "principal": principal,
            **profile.metadata,
        }
        return total_bps, metadata

    def _risk_premium(self, profile: NetworkCostProfile) -> float:
        weighted_score = (
            0.4 * profile.security_score
            + 0.3 * profile.liquidity_score
            + 0.2 * profile.regulation_score
            + 0.1 * profile.ux_score
        )
        return max(0.0, (5.0 - weighted_score)) * 4.0


def load_network_profiles_from_csv(csv_path: Path) -> Dict[str, NetworkCostProfile]:
    """Load network profiles from a reproducible CSV."""

    if not csv_path.exists():
        return {}
    profiles: Dict[str, NetworkCostProfile] = {}
    with csv_path.open() as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            name = row.get("network")
            if not name:
                continue
            try:
                profiles[name] = NetworkCostProfile(
                    name=name,
                    annual_tx_count=int(float(row.get("annual_tx_count", 0))),
                    gas_per_tx=int(float(row.get("gas_per_tx", 0))),
                    gas_price_gwei=float(row.get("gas_price_gwei", 0.0)),
                    oracle_bps=float(row.get("oracle_bps", 0.0)),
                    monitoring_bps=float(row.get("monitoring_bps", 0.0)),
                    security_score=float(row.get("security_score", 0.0)),
                    liquidity_score=float(row.get("liquidity_score", 0.0)),
                    regulation_score=float(row.get("regulation_score", 0.0)),
                    ux_score=float(row.get("ux_score", 0.0)),
                    gas_token_price_usd=float(
                        row.get("gas_token_price_usd")
                        or row.get("gas_token_usd")
                        or DEFAULT_ETH_PRICE_USD
                    ),
                    metadata={
                        "gas_price_source": row.get("gas_price_source", ""),
                        "oracle_source": row.get("oracle_source", ""),
                        "monitoring_source": row.get("monitoring_source", ""),
                        "notes": row.get("notes", ""),
                        "assumption_hash": row.get("assumption_hash", ""),
                    },
                )
            except (ValueError, TypeError):
                continue
    return profiles


__all__ = [
    "BlockchainInfrastructureTracker",
    "NetworkCostProfile",
    "DEFAULT_NETWORK_PROFILES",
    "load_network_profiles_from_csv",
]
