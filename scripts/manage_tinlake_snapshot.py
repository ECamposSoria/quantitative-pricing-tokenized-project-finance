"""Operational helper to manage cached Tinlake metrics snapshots."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pftoken.pricing.spreads.tinlake import (
    TINLAKE_SNAPSHOT_PATH,
    TinlakeMetrics,
    fetch_tinlake_metrics,
)

STALE_THRESHOLD_DAYS = 7
REFRESH_HINT = "PYTHONPATH=. python scripts/manage_tinlake_snapshot.py --force-refresh"


def _read_snapshot(path: Path) -> TinlakeMetrics | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
        return TinlakeMetrics(**payload)
    except Exception:
        return None


def _snapshot_age(metrics: TinlakeMetrics | None) -> float | None:
    if metrics is None:
        return None
    return max(time.time() - metrics.timestamp, 0.0)


def _snapshot_status(age_seconds: float | None) -> str:
    if age_seconds is None:
        return "unknown"
    if age_seconds > STALE_THRESHOLD_DAYS * 86400:
        return "stale"
    return "fresh"


def manage_snapshot(force_refresh: bool, offline: bool) -> dict[str, Any]:
    """Load or refresh Tinlake metrics and return an audit payload."""

    action = "status"
    metrics: TinlakeMetrics | None = None
    if offline:
        metrics = _read_snapshot(TINLAKE_SNAPSHOT_PATH)
        action = "offline-status"
    else:
        if force_refresh:
            fetch_tinlake_metrics.cache_clear()  # type: ignore[attr-defined]
            action = "force-refresh"
        metrics = fetch_tinlake_metrics()
        if metrics is None:
            metrics = _read_snapshot(TINLAKE_SNAPSHOT_PATH)

    payload: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "snapshot_path": str(TINLAKE_SNAPSHOT_PATH),
        "snapshot_exists": TINLAKE_SNAPSHOT_PATH.exists(),
        "action": action,
        "offline_mode": offline,
    }
    if metrics:
        age_seconds = _snapshot_age(metrics)
        status = _snapshot_status(age_seconds)
        payload.update(
            {
                "tvl_usd": metrics.tvl_usd,
                "avg_daily_volume_usd": metrics.avg_daily_volume_usd,
                "avg_pool_ticket_usd": metrics.avg_pool_ticket_usd,
                "datapoints": metrics.datapoints,
                "source_timestamp": metrics.timestamp,
                "snapshot_age_seconds": age_seconds,
                "snapshot_status": status,
            }
        )
        if status == "stale":
            warning = f"Tinlake snapshot older than {STALE_THRESHOLD_DAYS} days. Run: {REFRESH_HINT}"
            payload["warning"] = warning
            print(f"WARNING: {warning}", file=sys.stderr)
    else:
        payload.update(
            {
                "tvl_usd": None,
                "avg_daily_volume_usd": None,
                "avg_pool_ticket_usd": None,
                "datapoints": 0,
                "source_timestamp": None,
                "snapshot_age_seconds": None,
                "snapshot_status": "missing",
            }
        )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage cached Tinlake metrics snapshots.")
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Bypass cache and refresh metrics from DeFiLlama.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip network calls and read the last cached snapshot only.",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show snapshot status (default).",
    )
    args = parser.parse_args()
    payload = manage_snapshot(force_refresh=args.force_refresh, offline=args.offline)
    print(json.dumps(payload))
    status_parts = [
        f"Snapshot: {payload['snapshot_path']}",
        f"exists={payload['snapshot_exists']}",
        f"action={payload['action']}",
        f"status={payload.get('snapshot_status', 'unknown')}",
    ]
    if payload.get("snapshot_age_seconds") is not None:
        status_parts.append(f"age={payload['snapshot_age_seconds']:.0f}s")
    print(" | ".join(status_parts), file=sys.stderr)


if __name__ == "__main__":
    main()
