"""Tests for the curve loader utilities."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from pftoken.pricing import load_zero_curve_from_csv


def test_load_zero_curve_from_csv(tmp_path: Path):
    data = pd.DataFrame({"maturity_years": [1, 2, 5], "rate": [0.04, 0.045, 0.05]})
    csv_path = tmp_path / "curve.csv"
    data.to_csv(csv_path, index=False)

    curve = load_zero_curve_from_csv(csv_path)
    assert len(curve.points) == 3
    assert pytest.approx(curve.spot_rate(2.0), rel=1e-6) == 0.045


def test_load_zero_curve_from_csv_with_swaps(tmp_path: Path):
    data = pd.DataFrame(
            {
                "maturity_years": [1, 2, 5],
                "rate": [0.04, 0.045, 0.05],
                "instrument_type": ["deposit", "deposit", "swap"],
                "payment_frequency": [1, 1, 1],
            }
        )
    csv_path = tmp_path / "curve_swaps.csv"
    data.to_csv(csv_path, index=False)
    curve = load_zero_curve_from_csv(csv_path)
    assert pytest.approx(curve.spot_rate(5.0), rel=1e-6) == 0.05
