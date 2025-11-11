import numpy as np

from pftoken.models import load_placeholder_calibration
from pftoken.simulation import StochasticVariables


def test_lognormal_sampling_stable_mean():
    calibration = load_placeholder_calibration()
    variables = StochasticVariables(calibration, seed=7)
    samples = variables.sample("revenue_growth", size=10_000)
    empirical_mean = samples.mean()
    mu = calibration.random_variables["revenue_growth"].params["mu"]
    sigma = calibration.random_variables["revenue_growth"].params["sigma"]
    theoretical_mean = np.exp(mu + 0.5 * sigma**2)
    assert abs(empirical_mean - theoretical_mean) / theoretical_mean < 0.05


def test_antithetic_sampling_reduces_variance():
    calibration = load_placeholder_calibration()
    variables = StochasticVariables(calibration, seed=21)
    direct = variables.sample("rate_shock", size=2000, antithetic=False)
    variables = StochasticVariables(calibration, seed=21)
    anti = variables.sample("rate_shock", size=2000, antithetic=True)
    assert anti.var() <= direct.var() * 1.1
