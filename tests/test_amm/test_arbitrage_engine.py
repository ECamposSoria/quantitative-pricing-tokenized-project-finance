import numpy as np
import pytest

from pftoken.amm.core.pool_v2 import ConstantProductPool, PoolConfig, PoolState
from pftoken.amm.pricing.arbitrage_engine import AlmgrenChrissEngine


def make_pool():
    return ConstantProductPool(PoolConfig("A", "B"), PoolState(1_000.0, 1_000.0))


def test_optimal_trajectory_sums_to_size():
    engine = AlmgrenChrissEngine(eta=0.1, gamma=0.1, sigma=0.2, lambda_risk=0.05)
    traj = engine.optimal_trajectory(total_size=100.0, time_horizon=1.0, n_steps=5)
    assert traj.sum() == pytest.approx(100.0)
    assert np.all(traj > 0)


def test_simulate_convergence_returns_metrics():
    engine = AlmgrenChrissEngine(eta=0.1, gamma=0.1, sigma=0.2, lambda_risk=0.05)
    pool = make_pool()
    refs = np.array([1.05, 1.02, 1.01])
    res = engine.simulate_convergence(pool, refs, capital_limit=50.0)
    assert res.execution_cost > 0
    assert res.trajectory.shape == refs.shape
    assert res.realized_spread_reduction == refs[0] - refs[-1]


def test_convergence_half_life():
    engine = AlmgrenChrissEngine(eta=0.1, gamma=0.1, sigma=0.2, lambda_risk=0.05)
    spreads = [0.10, 0.07, 0.05, 0.04]
    hl = engine.convergence_half_life(spreads)
    assert hl >= 0
