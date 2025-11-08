"""Shared pytest fixtures for the project finance tokenization suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from pftoken.models import CFADSCalculator, ProjectParameters


@pytest.fixture
def project_parameters() -> ProjectParameters:
    """Load the canonical LEO IoT parameters (validated)."""
    base = Path(__file__).resolve().parents[1] / "data" / "input" / "leo_iot"
    return ProjectParameters.from_directory(base)


@pytest.fixture
def cfads_calculator(project_parameters: ProjectParameters) -> CFADSCalculator:
    """Convenience fixture returning a CFADS calculator."""
    return CFADSCalculator.from_project_parameters(project_parameters)


@pytest.fixture
def amm_pool_v2():
    """Return a simple constant product pool for AMM tests."""
    from pftoken.amm.core.pool_v2 import ConstantProductPool, PoolConfig, PoolState

    config = PoolConfig(token0="TOKEN0", token1="TOKEN1", fee_bps=30)
    state = PoolState(reserve0=1_000_000.0, reserve1=500_000.0)
    return ConstantProductPool(config=config, state=state)
