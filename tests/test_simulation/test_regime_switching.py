import numpy as np

from pftoken.simulation.regime_switching import RegimeConfig, RegimeSwitchingProcess


def _regime_payload():
    return {
        "enable_regime_switching": True,
        "enable_regime_lgd": True,
        "enable_regime_spreads": True,
        "n_regimes": 2,
        "transition_matrix": [
            [0.9, 0.1],
            [0.3, 0.7],
        ],
        "regimes": {
            0: {"mu": 0.05, "sigma": 0.2, "recovery_adj": 0.0, "spread_lift_bps": 0.0},
            1: {"mu": 0.02, "sigma": 0.35, "recovery_adj": -0.3, "spread_lift_bps": 50.0},
        },
    }


def test_regime_simulation_shapes_and_params():
    cfg = RegimeConfig.from_dict(_regime_payload())
    process = RegimeSwitchingProcess(cfg, seed=42)
    paths = process.simulate_regimes(n_sims=5, n_periods=4)
    assert paths.shape == (5, 4)
    assert np.all(paths[:, 0] == 0)
    assert set(np.unique(paths)).issubset({0, 1})

    params = process.get_params_by_path(paths)
    assert params["mu"].shape == (5, 4)
    assert np.all(params["mu"][paths == 0] == 0.05)
    assert np.all(params["sigma"][paths == 1] == 0.35)
    assert np.all(params["spread_lift_bps"][paths == 1] == 50.0)


def test_regime_config_defaults_disabled():
    cfg = RegimeConfig.from_dict(None)
    assert cfg.enable_regime_switching is False
    process = RegimeSwitchingProcess(cfg)
    paths = process.simulate_regimes(n_sims=2, n_periods=3)
    assert np.all(paths == 0)
