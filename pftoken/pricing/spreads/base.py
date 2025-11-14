"""Shared dataclasses and helpers for spread decomposition components."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Mapping, Optional

from pftoken.models.merton import MertonModel


@dataclass(frozen=True)
class TrancheSpreadInputs:
    """Inputs required by all spread components for a given tranche."""

    name: str
    principal: float
    tenor_years: float
    duration_years: float | None
    pd: float
    lgd: float


@dataclass(frozen=True)
class SpreadComponentResult:
    """Normalized representation of a spread contribution in basis points."""

    component: str
    traditional_bps: float
    tokenized_bps: float
    metadata: Dict[str, float] = field(default_factory=dict)


@dataclass
class PerTrancheSpreadBreakdown:
    """Aggregated spread breakdown for a single tranche."""

    tranche: str
    components: Dict[str, SpreadComponentResult] = field(default_factory=dict)
    traditional_total_bps: float = 0.0
    tokenized_total_bps: float = 0.0

    def add_component(self, result: SpreadComponentResult) -> None:
        self.components[result.component] = result
        self.traditional_total_bps = sum(item.traditional_bps for item in self.components.values())
        self.tokenized_total_bps = sum(item.tokenized_bps for item in self.components.values())


@dataclass
class TokenizedSpreadConfig:
    """Central configuration for the spread decomposition engine.

    Defaults are grounded in open benchmarks: credit spreads siguen los rangos
    PF de Oxford Sustainable Finance (2024) e IEA (2020); origination usa el
    rango 100‑300 bps citado por BAM Capital (2025) y World Bank (2024); servicing
    parte de 25 bps anuales (MSLP 2022, Florida/Leon HFAs). La calibración de
    liquidez puede autoconectarse a Tinlake (DeFiLlama) para mantener TVL/volumen
    reales como proxies del mercado RWA.
    """

    # Credit component
    merton_model: Optional[MertonModel] = None
    market_price_of_risk: float = 0.1
    duration_fallback_use_tenor: bool = True

    # Liquidity component
    liquidity_impact_coeff: float = 0.017361111111111112
    liquidity_alpha: float = 0.5
    token_market_depth_multiplier: float = 10.0
    token_market_volume_multiplier: float = 4.0
    token_ticket_size_multiplier: float = 0.01
    auto_calibrate_liquidity: bool = True
    liquidity_calibration_source: str = "tinlake"
    traditional_liquidity_premium_bps: float = 75.0
    tradfi_turnover_ratio: float = 0.05
    min_liquidity_factor: float = 0.2

    # Origination and servicing
    origination_beta: float = 0.5
    servicing_gamma: float = 1.0
    placement_bps: float = 100.0
    syndication_bps: float = 50.0
    paying_agent_bps: float = 15.0
    compliance_audit_bps: float = 7.5
    origination_fee_amortization_years: float = 10.0
    servicing_residual_bps: float = 5.0

    # Infrastructure component
    blockchain_network: str = "Ethereum"
    infrastructure_csv_path: str = "data/derived/tokenized_infra_costs.csv"
    infra_overrides: Optional[Mapping[str, float]] = None

    # Credit transparency
    credit_transparency_delta_bps: float = -30.0
