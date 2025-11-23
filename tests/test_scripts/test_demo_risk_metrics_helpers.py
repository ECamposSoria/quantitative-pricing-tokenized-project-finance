import numpy as np

from scripts import demo_risk_metrics as demo


class DummyOutputs:
    def __init__(self):
        self.monte_carlo = type("mc", (), {"derived": {}})()
        self.pd_lgd_paths = None
        self.loss_paths = None
        self.tranche_names = []
        self.breach_curves = None


def test_extract_asset_distribution():
    outputs = DummyOutputs()
    outputs.monte_carlo.derived["asset_values"] = np.array([100.0, 120.0, 140.0])
    dist = demo.extract_asset_distribution(outputs)
    assert dist["p50"] == 120.0


def test_extract_breach_curves_with_dict_wrapper():
    outputs = DummyOutputs()
    Curves = type("Curves", (), {})
    curves = Curves()
    curves.survival = np.array([1.0, 0.9])
    curves.breach_probability = np.array([0.0, 0.1])
    curves.hazard = np.array([0.0, 0.1])
    outputs.breach_curves = {"curves": curves}
    result = demo.extract_breach_curves(outputs, years=[1, 2])
    assert np.allclose(result["cumulative"], [0.0, 0.1])
