"""Synthetic forward/zero curve fixtures used by the pricing tests."""

from __future__ import annotations

from typing import List

from pftoken.pricing.zero_curve import CurveInstrument, ZeroCurve


def build_flat_curve(currency: str, rate: float, years: int = 20) -> ZeroCurve:
    """Return a flat zero curve with yearly deposit instruments."""

    instruments: List[CurveInstrument] = [
        CurveInstrument(maturity_years=year, rate=rate, instrument_type="deposit")
        for year in range(1, years + 1)
    ]
    return ZeroCurve.bootstrap(instruments, currency=currency)

