"""Validation helpers for AMM configuration payloads."""

from __future__ import annotations

from typing import Mapping


def validate_pool_config(config: Mapping[str, object]) -> None:
    required = {"token0", "token1", "fee_bps", "initial_reserve0", "initial_reserve1"}
    missing = required - config.keys()
    if missing:
        raise ValueError(f"Missing keys in pool config: {sorted(missing)}")
    if config["initial_reserve0"] <= 0 or config["initial_reserve1"] <= 0:  # type: ignore[operator]
        raise ValueError("Pool reserves must be positive.")
    if config["fee_bps"] < 0:  # type: ignore[operator]
        raise ValueError("fee_bps must be non-negative.")


def validate_range(lower_tick: int, upper_tick: int) -> None:
    if lower_tick >= upper_tick:
        raise ValueError("lower_tick must be strictly less than upper_tick.")
