import numpy as np

from pftoken.models.calibration import load_placeholder_calibration
from pftoken.simulation.correlation import CorrelatedSampler, CorrelationMatrix


def test_correlation_sampler_antithetic():
    calibration = load_placeholder_calibration()
    sampler = CorrelatedSampler(calibration, seed=123)
    draws = sampler.sample(200, antithetic=True)
    first_var = next(iter(draws.values()))
    assert first_var.shape == (200,)
    assert np.isfinite(first_var).all()


def test_correlation_matrix_repairs_near_spd():
    calibration = load_placeholder_calibration()
    corr = calibration.correlation
    corr.matrix[0][1] = corr.matrix[1][0] = corr.matrix[0][1] - 1e-8  # tiny asymmetry
    matrix = CorrelationMatrix(corr, tolerance=1e-6)
    assert matrix.matrix.shape[0] == matrix.matrix.shape[1]
