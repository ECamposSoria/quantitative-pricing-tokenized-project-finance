import numpy as np
import pytest

from pftoken.risk.hhi import RiskConcentrationAnalysis


def test_hhi_on_exposures_and_losses():
    names = ["Senior", "Mezz", "Equity"]
    exposures = {"Senior": 60, "Mezz": 25, "Equity": 15}
    analysis = RiskConcentrationAnalysis(names)
    exposure_metrics = analysis.exposures_hhi(exposures)
    expected_hhi = 0.6**2 + 0.25**2 + 0.15**2
    assert exposure_metrics["hhi"] == expected_hhi
    assert exposure_metrics["equivalent_n"] == pytest.approx(1 / expected_hhi)

    losses = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.5, 0.2],
            [2.0, 1.0, 0.4],
        ]
    )
    loss_metrics = analysis.losses_hhi(losses)
    assert loss_metrics["hhi"] > 0
    assert loss_metrics["equivalent_n"] > 0
