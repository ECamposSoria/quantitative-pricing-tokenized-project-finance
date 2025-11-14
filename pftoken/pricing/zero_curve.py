"""Zero curve construction helpers with bootstrap and shock support."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

import numpy as np
from scipy import optimize


def _round_key(value: float) -> float:
    return round(float(value), 8)


@dataclass(frozen=True)
class CurveInstrument:
    """Par instrument used for bootstrapping.

    Attributes:
        maturity_years: Time to maturity expressed in years.
        rate: Annualized coupon/interest rate in decimal form.
        instrument_type: `deposit` for zero-coupon style deposits or `swap`
            for fixed-for-floating par swaps.
        payment_frequency: Coupons per year for swaps (ignored for deposits).
    """

    maturity_years: float
    rate: float
    instrument_type: str = "deposit"
    payment_frequency: int = 1

    def __post_init__(self) -> None:
        if self.maturity_years <= 0:
            raise ValueError("Instrument maturity must be positive.")
        if self.rate < 0:
            raise ValueError("Instrument rates must be non-negative.")
        if self.instrument_type not in {"deposit", "swap"}:
            raise ValueError("instrument_type must be 'deposit' or 'swap'.")
        if self.payment_frequency <= 0:
            raise ValueError("payment_frequency must be positive.")


@dataclass(frozen=True)
class CurvePoint:
    """Single zero-rate observation."""

    maturity_years: float
    zero_rate: float


class ZeroCurve:
    """Piecewise-linear zero curve with helper analytics."""

    def __init__(
        self,
        points: Sequence[CurvePoint],
        *,
        currency: str = "USD",
        interpolation: str = "linear",
    ):
        if not points:
            raise ValueError("ZeroCurve requires at least one point.")
        self.currency = currency.upper()
        self.interpolation = interpolation
        self._points = sorted(points, key=lambda p: p.maturity_years)
        self._times = np.array([p.maturity_years for p in self._points], dtype=float)
        self._zero_rates = np.array([p.zero_rate for p in self._points], dtype=float)
        if np.any(self._times <= 0):
            raise ValueError("Curve maturities must be strictly positive.")
        self._discounts = self._compute_discounts(self._zero_rates, self._times)

    # ------------------------------------------------------------------ Factory
    @classmethod
    def bootstrap(
        cls,
        instruments: Sequence[CurveInstrument],
        *,
        currency: str = "USD",
    ) -> "ZeroCurve":
        """Construct a curve from par instruments via sequential bootstrap."""

        if not instruments:
            raise ValueError("Cannot bootstrap curve without instruments.")
        ordered = sorted(instruments, key=lambda inst: inst.maturity_years)
        known_dfs: Dict[float, float] = {}
        points: List[CurvePoint] = []
        for instrument in ordered:
            maturity = instrument.maturity_years
            if instrument.instrument_type == "deposit":
                df = _discount_from_deposit(instrument.rate, maturity)
            else:
                df = _bootstrap_swap_discount(instrument, known_dfs)
            zero_rate = df ** (-1.0 / maturity) - 1.0
            key = _round_key(maturity)
            known_dfs[key] = df
            points.append(CurvePoint(maturity_years=maturity, zero_rate=float(zero_rate)))
        return cls(points, currency=currency)

    # ----------------------------------------------------------------- Analytics
    @staticmethod
    def _compute_discounts(zero_rates: np.ndarray, maturities: np.ndarray) -> np.ndarray:
        return np.power(1.0 + zero_rates, -maturities)

    def discount_factor(self, maturity_years: float) -> float:
        """Return the discount factor for the requested maturity."""

        if maturity_years < 0:
            raise ValueError("Maturity must be non-negative.")
        if maturity_years == 0:
            return 1.0
        rate = self.spot_rate(maturity_years)
        return (1.0 + rate) ** (-maturity_years)

    def spot_rate(self, maturity_years: float) -> float:
        """Interpolate the zero rate for the provided tenor."""

        if maturity_years <= self._times[0]:
            slope = self._zero_rates[0] / self._times[0]
            return slope * maturity_years
        if maturity_years >= self._times[-1]:
            return self._zero_rates[-1]
        return float(np.interp(maturity_years, self._times, self._zero_rates))

    def forward_rate(self, start: float, end: float) -> float:
        """Compute the implied forward rate between two maturities."""

        if end <= start:
            raise ValueError("forward end must be greater than start.")
        df_start = self.discount_factor(start)
        df_end = self.discount_factor(end)
        tenor = end - start
        return (df_start / df_end) ** (1.0 / tenor) - 1.0

    # ------------------------------------------------------------------- Shocks
    def apply_shock(
        self,
        *,
        parallel_bps: float = 0.0,
        bucket_shocks: Mapping[Tuple[float, float], float] | None = None,
    ) -> "ZeroCurve":
        """Return a shocked copy of the curve.

        Args:
            parallel_bps: Shift applied to all tenors (basis points).
            bucket_shocks: Optional mapping {(start, end]: bps} for custom shocks.
        """

        new_points: List[CurvePoint] = []
        for point in self._points:
            adjustment = parallel_bps
            if bucket_shocks:
                for (start, end), shock_bps in bucket_shocks.items():
                    if start < point.maturity_years <= end:
                        adjustment += shock_bps
            shocked_rate = point.zero_rate + adjustment / 10_000.0
            new_points.append(
                CurvePoint(maturity_years=point.maturity_years, zero_rate=shocked_rate)
            )
        return ZeroCurve(new_points, currency=self.currency, interpolation=self.interpolation)

    # ----------------------------------------------------------------- Helpers
    def to_dict(self) -> Dict[str, object]:
        """Serialize the curve to a JSON-friendly structure."""

        return {
            "currency": self.currency,
            "interpolation": self.interpolation,
            "points": [
                {"maturity_years": point.maturity_years, "zero_rate": point.zero_rate}
                for point in self._points
            ],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "ZeroCurve":
        """Rebuild a curve from :meth:`to_dict` output."""

        points = [
            CurvePoint(maturity_years=float(item["maturity_years"]), zero_rate=float(item["zero_rate"]))
            for item in payload["points"]  # type: ignore[index]
        ]
        return cls(points, currency=str(payload.get("currency", "USD")))

    def __len__(self) -> int:
        return len(self._points)

    def __repr__(self) -> str:
        return f"ZeroCurve(currency={self.currency}, points={len(self._points)})"

    @property
    def points(self) -> Sequence[CurvePoint]:
        return tuple(self._points)


# ----------------------------------------------------------------------- helpers
def _discount_from_deposit(rate: float, maturity_years: float) -> float:
    return (1.0 + rate) ** (-maturity_years)


def _bootstrap_swap_discount(
    instrument: CurveInstrument,
    known_discounts: Mapping[float, float],
) -> float:
    periods = int(round(instrument.maturity_years * instrument.payment_frequency))
    if not np.isclose(periods / instrument.payment_frequency, instrument.maturity_years):
        raise ValueError("Swap maturity must align with payment frequency.")
    payment_times = [
        round(period / instrument.payment_frequency, 8)
        for period in range(1, periods + 1)
    ]
    coupon = instrument.rate / instrument.payment_frequency
    for time in payment_times[:-1]:
        key = _round_key(time)
        if key not in known_discounts:
            raise ValueError(
                f"Missing discount factor for coupon time {time}y when bootstrapping swap."
            )

    def npv(df_last: float) -> float:
        pv_coupons = sum(
            coupon * known_discounts[_round_key(time)] for time in payment_times[:-1]
        )
        pv_last = (coupon + 1.0) * df_last
        return pv_coupons + pv_last - 1.0

    return optimize.brentq(npv, 1e-6, 1.0)


__all__ = ["CurveInstrument", "CurvePoint", "ZeroCurve"]
