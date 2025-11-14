"""Liquidity spread component using simple Amihud-style impact."""

from __future__ import annotations

from dataclasses import dataclass

from .base import SpreadComponentResult, TokenizedSpreadConfig, TrancheSpreadInputs
from .tinlake import (
    calibrate_liquidity_from_tinlake,
    fetch_tinlake_metrics,
    TinlakeMetrics,
)


@dataclass
class LiquiditySpreadComponent:
    """Estimates liquidity premiums and applies configurable alpha reduction."""

    config: TokenizedSpreadConfig

    def __post_init__(self):
        self.depth_multiplier = self.config.token_market_depth_multiplier
        self.volume_multiplier = self.config.token_market_volume_multiplier
        self.ticket_multiplier = self.config.token_ticket_size_multiplier
        self.calibration_metadata: dict[str, float] | None = None
        if self.config.auto_calibrate_liquidity and self.config.liquidity_calibration_source.lower() == "tinlake":
            metrics = fetch_tinlake_metrics()
            if metrics:
                (
                    self.depth_multiplier,
                    self.volume_multiplier,
                    self.ticket_multiplier,
                ) = calibrate_liquidity_from_tinlake(metrics)
                self.calibration_metadata = {
                    "source": "DeFiLlama Tinlake protocol",
                    "tvl_usd": metrics.tvl_usd,
                    "avg_daily_volume_usd": metrics.avg_daily_volume_usd,
                    "avg_pool_ticket_usd": metrics.avg_pool_ticket_usd,
                    "datapoints": metrics.datapoints,
                    "timestamp": metrics.timestamp,
                    "turnover_ratio": (metrics.avg_daily_volume_usd * 365.0) / max(metrics.tvl_usd, 1.0),
                }

    def compute(self, inputs: TrancheSpreadInputs) -> SpreadComponentResult:
        traditional_bps = self._base_liquidity_bps(inputs)
        alpha = min(max(self.config.liquidity_alpha, 0.0), 1.0)
        microstructure_factor = self._token_microstructure_factor()
        tokenized_bps = traditional_bps * microstructure_factor * (1.0 - alpha)
        metadata = {
            "impact_coeff": self.config.liquidity_impact_coeff,
            "alpha": alpha,
            "microstructure_factor": microstructure_factor,
            "token_depth_multiplier": self.depth_multiplier,
            "token_volume_multiplier": self.volume_multiplier,
            "token_ticket_size_multiplier": self.ticket_multiplier,
        }
        if self.calibration_metadata:
            metadata["tinlake_metrics"] = self.calibration_metadata
        return SpreadComponentResult("liquidity", traditional_bps, tokenized_bps, metadata)

    def _base_liquidity_bps(self, inputs: TrancheSpreadInputs) -> float:
        ticket_pct = 1.0
        depth = 1.0
        volume = 1.0
        ticket_notional = inputs.principal * ticket_pct
        depth_volume = max(depth * volume, 1e-6)
        impact = self.config.liquidity_impact_coeff * (ticket_notional / 1_000_000.0) / depth_volume
        return impact * 100.0

    def _token_microstructure_factor(self) -> float:
        numerator = self.ticket_multiplier * self._turnover_factor()
        denominator = max(self.depth_multiplier * self.volume_multiplier, 1e-6)
        factor = numerator / denominator
        return max(factor, self.config.min_liquidity_factor)

    def _turnover_factor(self) -> float:
        if not self.calibration_metadata:
            return 1.0
        turnover = self.calibration_metadata.get("turnover_ratio")
        if not turnover or turnover <= 0:
            return 1.0
        baseline = max(self.config.tradfi_turnover_ratio, 1e-3)
        ratio = max(turnover / baseline, 0.1)
        return 1.0 / max(ratio**0.5, 1.0)


__all__ = ["LiquiditySpreadComponent"]
