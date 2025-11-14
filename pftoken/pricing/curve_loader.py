"""Helpers to build zero curves from stored market curve CSV files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import pandas as pd

from .zero_curve import CurveInstrument, CurvePoint, ZeroCurve


@dataclass(frozen=True)
class MarketCurveSnapshot:
    """Metadata describing a stored market curve."""

    path: Path
    currency: str = "USD"


def load_zero_curve_from_csv(
    csv_path: str | Path,
    *,
    currency: str = "USD",
) -> ZeroCurve:
    """Create a :class:`ZeroCurve` from a CSV with ``maturity_years``/``rate`` columns.

    If ``instrument_type``/``payment_frequency`` columns exist, they are retained when
    converting to :class:`CurveInstrument` for bootstrapping.
    """

    csv_path = Path(csv_path)
    instruments = curve_instruments_from_csv(csv_path)
    try:
        return ZeroCurve.bootstrap(instruments, currency=currency)
    except ValueError:
        points = [
            CurvePoint(maturity_years=inst.maturity_years, zero_rate=inst.rate)
            for inst in instruments
        ]
        return ZeroCurve(points, currency=currency)


def load_zero_curve_from_snapshot(snapshot: MarketCurveSnapshot) -> ZeroCurve:
    return load_zero_curve_from_csv(snapshot.path, currency=snapshot.currency)


def curve_instruments_from_csv(
    csv_path: str | Path,
    *,
    default_instrument_type: str = "deposit",
    default_payment_frequency: int = 1,
) -> Sequence[CurveInstrument]:
    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path, comment="#")
    required = {"maturity_years", "rate"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Missing required columns in curve CSV: {missing}")
    instruments: list[CurveInstrument] = []
    for row in df.itertuples(index=False):
        maturity = float(row.maturity_years)
        rate = float(row.rate)
        instrument_type = getattr(row, "instrument_type", default_instrument_type) or default_instrument_type
        payment_frequency = getattr(row, "payment_frequency", default_payment_frequency) or default_payment_frequency
        instruments.append(
            CurveInstrument(
                maturity_years=maturity,
                rate=rate,
                instrument_type=str(instrument_type).lower(),
                payment_frequency=int(payment_frequency),
            )
        )
    return instruments


__all__ = [
    "MarketCurveSnapshot",
    "curve_instruments_from_csv",
    "load_zero_curve_from_csv",
    "load_zero_curve_from_snapshot",
]
