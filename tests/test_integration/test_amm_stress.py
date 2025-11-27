import numpy as np

from pftoken.amm.core.pool_v2 import ConstantProductPool, PoolConfig, PoolState
from pftoken.stress.amm_metrics_export import get_stress_metrics
from pftoken.stress.amm_stress_scenarios import build_scenarios


def test_stress_metrics_shapes():
    pool = ConstantProductPool(PoolConfig("A", "B"), PoolState(1_000.0, 1_000.0))
    scenarios = build_scenarios()
    metrics = get_stress_metrics(pool, scenarios.values())
    assert metrics.depth_curve.shape[1] == 2
    assert len(metrics.stressed_depths) == len(scenarios)
    assert set(metrics.il_by_scenario.keys()) == set(scenarios.keys())
    assert metrics.slippage_curve.shape[1] == 2
    # liquidity paths should be non-empty arrays
    for path in metrics.stressed_depths.values():
        assert isinstance(path, np.ndarray)
        assert path.size > 0
