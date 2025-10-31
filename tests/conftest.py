"""Shared pytest fixtures for the project finance tokenization suite."""

import pytest

@pytest.fixture
def placeholder_config():
    """Return a minimal configuration placeholder."""
    return {}


@pytest.fixture
def amm_pool_v2():
    """Return a simple constant product pool for AMM tests."""
    from pftoken.amm.core.pool_v2 import ConstantProductPool, PoolConfig, PoolState

    config = PoolConfig(token0="TOKEN0", token1="TOKEN1", fee_bps=30)
    state = PoolState(reserve0=1_000_000.0, reserve1=500_000.0)
    return ConstantProductPool(config=config, state=state)
