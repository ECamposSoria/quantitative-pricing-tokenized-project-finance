import numpy as np

from pftoken.models import load_placeholder_calibration
from pftoken.simulation import CorrelatedSampler


def test_correlated_sampler_preserves_rank_correlation():
    calibration = load_placeholder_calibration()
    sampler = CorrelatedSampler(calibration, seed=123)
    draws = sampler.sample(5000)
    keys = list(draws.keys())
    matrix = np.corrcoef([draws[k] for k in keys])
    # Expect correlation direction to match calibration (signs)
    assert np.sign(matrix[0, 1]) == np.sign(calibration.correlation.matrix[0][1])
    assert np.sign(matrix[0, 2]) == np.sign(calibration.correlation.matrix[0][2])
