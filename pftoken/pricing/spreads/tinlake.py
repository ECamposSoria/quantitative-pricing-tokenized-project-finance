"""Utilities for sourcing Tinlake (Centrifuge) liquidity metrics."""

from __future__ import annotations

import json
import statistics
import time
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

from datetime import datetime, timezone

import requests

TINLAKE_PROTOCOL_ENDPOINT = "https://api.llama.fi/protocol/centrifuge"
TINLAKE_TIMEOUT_SECONDS = 10
VOLUME_LOOKBACK_DAYS = 30
BASE_TVL_USD = 250_000_000.0
BASE_VOLUME_USD = 25_000_000.0
BASE_TICKET_USD = 100_000_000.0
TINLAKE_SNAPSHOT_PATH = Path("data/derived/liquidity/tinlake_metrics.json")
TINLAKE_METADATA_PATH = Path("data/derived/liquidity/tinlake_metadata.json")


@dataclass(frozen=True)
class TinlakeMetrics:
    tvl_usd: float
    avg_daily_volume_usd: float
    avg_pool_ticket_usd: float
    datapoints: int
    timestamp: int


def _fallback_metrics() -> TinlakeMetrics:
    """Return conservative fallback data when live + cached sources fail."""

    return TinlakeMetrics(
        tvl_usd=500_000_000.0,
        avg_daily_volume_usd=750_000.0,
        avg_pool_ticket_usd=15_000_000.0,
        datapoints=0,
        timestamp=int(time.time()),
    )


def _sum_tokenized_tvl(current_chain_tvls: Dict[str, float]) -> tuple[float, int]:
    total = 0.0
    active = 0
    for chain, value in current_chain_tvls.items():
        if chain.lower().startswith("borrowed"):
            continue
        if value and value > 0:
            total += float(value)
            if value > 1_000_000:
                active += 1
    return total, active


def _avg_daily_volume(series: List[Dict[str, float]]) -> tuple[float, int]:
    if not series:
        return 0.0, 0
    ordered = sorted(series, key=lambda item: item.get("date", 0))[-(VOLUME_LOOKBACK_DAYS + 1) :]
    diffs = []
    for prev, nxt in zip(ordered, ordered[1:]):
        a = prev.get("totalLiquidityUSD")
        b = nxt.get("totalLiquidityUSD")
        if a is None or b is None:
            continue
        diffs.append(abs(float(b) - float(a)))
    if not diffs:
        return 0.0, len(ordered)
    return statistics.mean(diffs), len(ordered)


@lru_cache(maxsize=1)
def fetch_tinlake_metrics() -> TinlakeMetrics | None:
    data = None
    try:
        resp = requests.get(TINLAKE_PROTOCOL_ENDPOINT, timeout=TINLAKE_TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        data = None

    if data is None:
        cached = _read_snapshot()
        if cached:
            return cached
        fallback = _fallback_metrics()
        _write_snapshot(fallback, source="fallback")
        return fallback

    current = data.get("currentChainTvls") or {}
    tvl_usd, active_pools = _sum_tokenized_tvl(
        {k: float(v) for k, v in current.items()}
    )
    borrowed = float(
        current.get("Ethereum-borrowed")
        or current.get("borrowed")
        or 0.0
    )
    chain_tvls = data.get("chainTvls", {})
    ethereum_series = chain_tvls.get("Ethereum", {}).get("tvl", [])
    avg_volume, datapoints = _avg_daily_volume(ethereum_series)
    if not active_pools:
        active_pools = max(1, len([k for k, v in current.items() if v]))
    avg_ticket = borrowed / active_pools if active_pools else borrowed
    metrics = TinlakeMetrics(
        tvl_usd=tvl_usd,
        avg_daily_volume_usd=avg_volume,
        avg_pool_ticket_usd=avg_ticket,
        datapoints=datapoints,
        timestamp=int(time.time()),
    )
    _write_snapshot(metrics, source="api")
    return metrics


def calibrate_liquidity_from_tinlake(
    metrics: TinlakeMetrics,
) -> tuple[float, float, float]:
    """Return (depth_multiplier, volume_multiplier, ticket_multiplier)."""

    depth_multiplier = max(metrics.tvl_usd / BASE_TVL_USD, 0.1)
    volume_multiplier = max(metrics.avg_daily_volume_usd / BASE_VOLUME_USD, 0.1)
    ticket_multiplier = max(min(metrics.avg_pool_ticket_usd / BASE_TICKET_USD, 10.0), 0.01)
    return depth_multiplier, volume_multiplier, ticket_multiplier


def _write_snapshot(metrics: TinlakeMetrics, *, source: str) -> None:
    path = TINLAKE_SNAPSHOT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = asdict(metrics)
    path.write_text(json.dumps(serialized, indent=2))
    _write_metadata(metrics, source)


def _read_snapshot() -> TinlakeMetrics | None:
    path = TINLAKE_SNAPSHOT_PATH
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return TinlakeMetrics(**data)
    except Exception:
        return None


def _write_metadata(metrics: TinlakeMetrics, source: str) -> None:
    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "snapshot_path": str(TINLAKE_SNAPSHOT_PATH),
        "metadata_path": str(TINLAKE_METADATA_PATH),
        "source": source,
        "api_endpoint": TINLAKE_PROTOCOL_ENDPOINT,
        "tvl_usd": metrics.tvl_usd,
        "avg_daily_volume_usd": metrics.avg_daily_volume_usd,
        "avg_pool_ticket_usd": metrics.avg_pool_ticket_usd,
        "datapoints": metrics.datapoints,
        "metrics_timestamp": metrics.timestamp,
    }
    TINLAKE_METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    TINLAKE_METADATA_PATH.write_text(json.dumps(payload, indent=2))


__all__ = [
    "TinlakeMetrics",
    "fetch_tinlake_metrics",
    "calibrate_liquidity_from_tinlake",
    "BASE_TVL_USD",
    "BASE_VOLUME_USD",
    "BASE_TICKET_USD",
]
