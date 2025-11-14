"""Tinlake snapshot management tests."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from pftoken.pricing.spreads import tinlake
from scripts import manage_tinlake_snapshot as tinlake_cli


@pytest.fixture
def snapshot_path(tmp_path, monkeypatch):
    path = tmp_path / "tinlake_snapshot.json"
    monkeypatch.setattr(tinlake, "TINLAKE_SNAPSHOT_PATH", path)
    monkeypatch.setattr(tinlake_cli, "TINLAKE_SNAPSHOT_PATH", path)
    tinlake.fetch_tinlake_metrics.cache_clear()
    yield path
    tinlake.fetch_tinlake_metrics.cache_clear()


def _write_snapshot(path: Path, **overrides):
    payload = {
        "tvl_usd": 500_000_000.0,
        "avg_daily_volume_usd": 2_500_000.0,
        "avg_pool_ticket_usd": 12_000_000.0,
        "datapoints": 30,
        "timestamp": int(time.time()),
    }
    payload.update(overrides)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


def test_fetch_uses_snapshot_when_api_unavailable(snapshot_path, monkeypatch):
    _write_snapshot(snapshot_path, tvl_usd=123.0)

    def _fail(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(tinlake.requests, "get", _fail)
    tinlake.fetch_tinlake_metrics.cache_clear()
    metrics = tinlake.fetch_tinlake_metrics()
    assert metrics is not None
    assert metrics.tvl_usd == 123.0


def test_manage_snapshot_offline_reads_cache(snapshot_path):
    _write_snapshot(snapshot_path, tvl_usd=321.0)
    payload = tinlake_cli.manage_snapshot(force_refresh=False, offline=True)
    assert payload["offline_mode"] is True
    assert payload["tvl_usd"] == 321.0


def test_manage_snapshot_force_refresh(snapshot_path, monkeypatch):
    response_payload = {
        "currentChainTvls": {
            "Ethereum": 600_000_000.0,
            "borrowed": 300_000_000.0,
        },
        "chainTvls": {
            "Ethereum": {
                "tvl": [
                    {"date": 1, "totalLiquidityUSD": 500_000_000.0},
                    {"date": 2, "totalLiquidityUSD": 505_000_000.0},
                ]
            }
        },
    }

    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return response_payload

    monkeypatch.setattr(tinlake.requests, "get", lambda *_, **__: _Resp())
    tinlake.fetch_tinlake_metrics.cache_clear()
    payload = tinlake_cli.manage_snapshot(force_refresh=True, offline=False)
    assert payload["action"] == "force-refresh"
    assert payload["tvl_usd"] == response_payload["currentChainTvls"]["Ethereum"]
    assert Path(payload["snapshot_path"]).exists()
