import numpy as np

from pftoken.simulation.path_dependent import PathDependentConfig, evaluate_first_passage


def test_first_passage_disabled_returns_zero():
    cfg = PathDependentConfig(enable_path_default=False, barrier_ratio=1.0)
    asset_paths = np.ones((3, 2))
    debt = np.array([1.0, 1.0])
    flags = evaluate_first_passage(asset_paths, debt, cfg)
    assert flags.shape == (3,)
    assert not flags.any()


def test_first_passage_triggers_when_barrier_crossed():
    cfg = PathDependentConfig(enable_path_default=True, barrier_ratio=1.0)
    asset_paths = np.array([[1.2, 0.8], [1.5, 1.6]])
    debt = np.array([1.0, 1.0])
    flags = evaluate_first_passage(asset_paths, debt, cfg)
    assert flags.tolist() == [True, False]
