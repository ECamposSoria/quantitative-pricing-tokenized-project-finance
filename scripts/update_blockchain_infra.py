#!/usr/bin/env python3
"""Refresh blockchain infrastructure cost assumptions using public APIs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple

import requests

from pftoken.pricing.spreads.infrastructure import (
    DEFAULT_NETWORK_PROFILES,
    NetworkCostProfile,
)

COINGECKO_ENDPOINT = "https://api.coingecko.com/api/v3/simple/price"
TOKEN_PRICE_SOURCE = "CoinGecko Simple Price API"

GLOBAL_ETHERSCAN_ENV = "ETHERSCAN_API_KEY"
ETHERSCAN_V2_ENDPOINT = "https://api.etherscan.io/v2/api"

NETWORK_API_CONFIG = {
    "Ethereum": {
        "chain_id": 1,
        "url": ETHERSCAN_V2_ENDPOINT,
        "env": "ETHERSCAN_API_KEY",
        "source": "Etherscan Gas Tracker (V2)",
    },
    "Arbitrum": {
        "chain_id": 42161,
        "url": ETHERSCAN_V2_ENDPOINT,
        "env": "ARBISCAN_API_KEY",
        "source": "Arbiscan Gas Tracker (V2)",
    },
    "Optimism": {
        "chain_id": 10,
        "url": ETHERSCAN_V2_ENDPOINT,
        "env": "OPTIMISM_ETHERSCAN_API_KEY",
        "source": "Optimism Gas Tracker (V2)",
    },
    "Base": {
        "chain_id": 8453,
        "url": ETHERSCAN_V2_ENDPOINT,
        "env": "BASESCAN_API_KEY",
        "source": "Basescan Gas Tracker (V2)",
    },
    "Polygon": {
        "chain_id": 137,
        "url": ETHERSCAN_V2_ENDPOINT,
        "env": "POLYGONSCAN_API_KEY",
        "source": "Polygonscan Gas Tracker (V2)",
    },
}

LEGACY_ENDPOINTS = {
    "Arbitrum": {
        "url": "https://api.arbiscan.io/api",
        "source": "Arbiscan Gas Tracker (legacy)",
    },
    "Optimism": {
        "url": "https://api-optimistic.etherscan.io/api",
        "source": "Optimism Gas Tracker (legacy)",
    },
    "Base": {
        "url": "https://api.basescan.org/api",
        "source": "Basescan Gas Tracker (legacy)",
    },
    "Polygon": {
        "url": "https://api.polygonscan.com/api",
        "source": "Polygonscan Gas Tracker (legacy)",
    },
}

GAS_STATION_ENDPOINTS = {
    "Polygon": {
        "url": "https://gasstation.polygon.technology/v2",
        "source": "Polygon Gas Station",
        "field": ("standard", "maxFee"),
    },
}

RPC_ENDPOINTS = {
    "Arbitrum": "https://arb1.arbitrum.io/rpc",
    "Optimism": "https://mainnet.optimism.io",
    "Base": "https://mainnet.base.org",
}

GAS_TOKEN_IDS = {
    "Ethereum": "ethereum",
    "Arbitrum": "ethereum",
    "Optimism": "ethereum",
    "Base": "ethereum",
    "Polygon": "matic-network",
}

ORACLE_SOURCE = "Chainlink docs – Gas & Oracle fee overview"
MONITORING_SOURCE = "Ops assumption documented in docs/tokenized_spread_decomposition.md"


def fetch_token_prices(token_ids: Dict[str, str]) -> Dict[str, float]:
    unique_ids = sorted(set(token_ids.values()))
    if not unique_ids:
        return {}
    resp = requests.get(
        COINGECKO_ENDPOINT,
        params={"ids": ",".join(unique_ids), "vs_currencies": "usd"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    prices: Dict[str, float] = {}
    for token_id in unique_ids:
        price = data.get(token_id, {}).get("usd")
        if price is not None:
            prices[token_id] = float(price)
    return prices


def fetch_gas_price(network: str, default_price: float) -> Tuple[float, str]:
    cfg = NETWORK_API_CONFIG.get(network)
    if not cfg:
        return default_price, "manual default"
    api_key = os.getenv(cfg["env"]) or os.getenv(GLOBAL_ETHERSCAN_ENV)
    if not api_key:
        return default_price, f"{cfg['source']} (API key missing)"
    params_v2 = {
        "module": "gastracker",
        "action": "gasoracle",
        "chainid": cfg.get("chain_id"),
        "apikey": api_key,
    }
    safe_gas, source_info = _query_gas_endpoint(cfg["url"], params_v2, cfg["source"])
    if safe_gas is not None:
        return safe_gas, source_info
    legacy = LEGACY_ENDPOINTS.get(network)
    if legacy:
        params_legacy = {"module": "gastracker", "action": "gasoracle", "apikey": api_key}
        safe_gas, legacy_info = _query_gas_endpoint(legacy["url"], params_legacy, legacy["source"])
        if safe_gas is not None:
            return safe_gas, legacy_info
        source_info = legacy_info
    station = GAS_STATION_ENDPOINTS.get(network)
    if station:
        station_gas, station_source = _query_gas_station(station)
        if station_gas is not None:
            return station_gas, station_source
        source_info = station_source
    rpc_url = RPC_ENDPOINTS.get(network)
    if rpc_url:
        rpc_gas, rpc_source = _query_rpc_gas_price(rpc_url)
        if rpc_gas is not None:
            return rpc_gas, rpc_source
        source_info = rpc_source
    return default_price, source_info


def _query_gas_endpoint(url: str, params: Dict[str, object], source: str) -> Tuple[float | None, str]:
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        return None, f"{source} (error: {exc})"
    result = payload.get("result")
    if isinstance(result, dict):
        value = result.get("SafeGasPrice") or result.get("safeGasPrice")
        if value is not None:
            try:
                return float(value), source
            except ValueError:
                return None, f"{source} (invalid SafeGasPrice: {value})"
    message = None
    if isinstance(result, str) and result:
        message = result
    elif isinstance(payload.get("message"), str):
        message = payload["message"]
    if message:
        return None, f"{source} ({message})"
    return None, source


def _query_gas_station(station: Dict[str, object]) -> Tuple[float | None, str]:
    url = station["url"]
    source = station["source"]
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        return None, f"{source} (error: {exc})"
    field = station.get("field")
    value = payload
    try:
        for key in field:
            value = value[key]
    except Exception:
        value = None
    if value is None:
        return None, f"{source} (missing field)"
    try:
        return float(value), source
    except ValueError:
        return None, f"{source} (invalid value: {value})"


def _query_rpc_gas_price(rpc_url: str) -> Tuple[float | None, str]:
    source = f"RPC eth_gasPrice ({rpc_url})"
    payload = {"jsonrpc": "2.0", "method": "eth_gasPrice", "params": [], "id": 1}
    try:
        resp = requests.post(rpc_url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        value = data.get("result")
        if not isinstance(value, str):
            return None, f"{source} (invalid result)"
        wei = int(value, 16)
        return wei / 1_000_000_000, source
    except Exception as exc:
        return None, f"{source} (error: {exc})"


def risk_premium(profile: NetworkCostProfile) -> float:
    weighted_score = (
        0.4 * profile.security_score
        + 0.3 * profile.liquidity_score
        + 0.2 * profile.regulation_score
        + 0.1 * profile.ux_score
    )
    return max(0.0, (5.0 - weighted_score)) * 4.0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="data/derived/tokenized_infra_costs.csv",
        help="Ruta del CSV de salida (default: %(default)s)",
    )
    parser.add_argument(
        "--reference-principal",
        type=float,
        default=100_000_000.0,
        help="Principal de referencia en USD para anualizar costos.",
    )
    args = parser.parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    token_prices = fetch_token_prices(GAS_TOKEN_IDS)

    rows = []
    for name, profile in DEFAULT_NETWORK_PROFILES.items():
        gas_price_gwei, gas_source = fetch_gas_price(name, profile.gas_price_gwei)
        token_id = GAS_TOKEN_IDS.get(name, "ethereum")
        gas_token_price = token_prices.get(token_id, profile.gas_token_price_usd)
        gas_token_source = TOKEN_PRICE_SOURCE if token_id in token_prices else "default assumption"
        gas_cost_usd = (
            profile.annual_tx_count
            * profile.gas_per_tx
            * gas_price_gwei
            * 1e-9
            * gas_token_price
        )
        gas_cost_bps = gas_cost_usd / max(args.reference_principal, 1.0) * 10_000
        risk_bps = risk_premium(profile)
        total_bps = gas_cost_bps + profile.oracle_bps + profile.monitoring_bps + risk_bps
        rows.append(
            {
                "network": name,
                "reference_principal": args.reference_principal,
                "annual_tx_count": profile.annual_tx_count,
                "gas_per_tx": profile.gas_per_tx,
                "gas_price_gwei": gas_price_gwei,
                "gas_price_source": gas_source,
                "gas_token_price_usd": gas_token_price,
                "gas_token_price_source": gas_token_source,
                "oracle_bps": profile.oracle_bps,
                "oracle_source": ORACLE_SOURCE,
                "monitoring_bps": profile.monitoring_bps,
                "monitoring_source": MONITORING_SOURCE,
                "risk_premium_bps": risk_bps,
                "gas_cost_bps": gas_cost_bps,
                "total_bps": total_bps,
                "security_score": profile.security_score,
                "liquidity_score": profile.liquidity_score,
                "regulation_score": profile.regulation_score,
                "ux_score": profile.ux_score,
                "notes": "Auto-generated via public APIs",
            }
        )

    timestamp = datetime.now(timezone.utc).isoformat()
    assumption_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    for row in rows:
        row["timestamp_utc"] = timestamp
        row["assumption_hash"] = assumption_hash

    with output_path.open("w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} network rows to {output_path}")
    print("Remember to export ETHERSCAN/ARBISCAN/OPTIMISM_ETHERSCAN/BASESCAN/POLYGONSCAN API keys as needed.")


if __name__ == "__main__":
    main()
