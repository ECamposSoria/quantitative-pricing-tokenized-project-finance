import numpy as np

from pftoken.models.calibration import load_placeholder_calibration
from pftoken.simulation.monte_carlo import MonteCarloConfig, MonteCarloEngine


def test_monte_carlo_engine_runs_and_derives():
    calibration = load_placeholder_calibration()

    def path_callback(batch):
        # Simple derived metric: asset value proxy = revenue_growth * 100
        asset = batch["revenue_growth"] * 100
        return {"asset_values": asset}

    engine = MonteCarloEngine(calibration, path_callback=path_callback)
    config = MonteCarloConfig(simulations=256, seed=7, antithetic=True)
    result = engine.run_simulation(config)

    assert "revenue_growth" in result.draws
    assert result.draws["revenue_growth"].shape == (256,)
    assert "asset_values" in result.derived
    assert result.derived["asset_values"].shape == (256,)
    summary = result.summary()
    assert "revenue_growth" in summary
    assert "mean" in summary["revenue_growth"]
