import numpy as np

from pftoken.models.calibration import load_placeholder_calibration
from pftoken.simulation.stochastic_vars import StochasticVariables


def test_stochastic_variables_samples_shapes():
    calibration = load_placeholder_calibration()
    sampler = StochasticVariables(calibration, seed=42)
    names = list(sampler.names())
    samples = sampler.sample_many(names, size=500, antithetic=True)
    assert set(samples.keys()) == set(names)
    for arr in samples.values():
        assert arr.shape == (500,)
        assert np.isfinite(arr).all()
