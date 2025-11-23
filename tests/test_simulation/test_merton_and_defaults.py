import numpy as np

from pftoken.models.calibration import load_placeholder_calibration
from pftoken.simulation.default_flags import DefaultDetector
from pftoken.simulation.merton_integration import compute_pathwise_pd_lgd, loss_paths_from_pd_lgd


def test_merton_pathwise_pd_lgd_and_losses():
    calibration = load_placeholder_calibration()
    asset_values = np.full(128, 150.0)
    debt = {"senior": 80.0, "mezzanine": 40.0, "subordinated": 20.0}
    metrics = compute_pathwise_pd_lgd(
        asset_values,
        debt,
        discount_rate=0.08,
        horizon_years=10,
        calibration=calibration,
    )
    pd_paths = {k: v.pd for k, v in metrics.items()}
    lgd_paths = {k: v.lgd for k, v in metrics.items()}
    names, losses = loss_paths_from_pd_lgd(pd_paths, lgd_paths, seed=3)
    assert set(names) == set(debt.keys())
    assert losses.shape == (128, 3)


def test_default_detector_flags_and_first_breach():
    dscr = np.array([[1.1, 0.9, 1.2], [1.3, 1.25, 1.4]])
    detector = DefaultDetector(dscr_threshold=1.0)
    flags = detector.classify(dscr)
    assert bool(flags.payment[0]) is True  # allow numpy.bool_
    assert bool(flags.payment[1]) is False
    assert flags.first_breach_period.tolist() == [1, -1]
